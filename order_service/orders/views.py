from decimal import Decimal

from django.db import transaction
from django.db.models import Sum
from rest_framework import generics, status
from rest_framework.response import Response

from .models import Order, OrderItem
from .serializers import (OrderSerializer, OrderDetailSerializer,
                          OrderItemSerializer, OrderCreateSerializer,
                          OrderStatusUpdateSerializer, OrderItemCreateSerializer,
                          OrderItemUpdateSerializer)
from .services import (ProductServiceClient, ProductNotFound,
                       ProductServiceUnavailable)

# Thông điệp lỗi khi client gửi trạng thái không hợp lệ (khớp validate_status
# trong serializers.py)
STATUS_INVALID_DETAIL = "Trạng thái phải là một trong: pending, completed, cancelled."


def _validation_detail(errors):
    """Gom các lỗi của serializer thành một dòng thông điệp dễ đọc cho client."""
    parts = []
    for field, messages in errors.items():
        texts = []
        for message in (messages if isinstance(messages, (list, tuple)) else [messages]):
            if isinstance(message, dict):
                # Lỗi lồng nhau (ví dụ từng phần tử trong danh sách items)
                for sub in message.values():
                    texts.append(sub[0] if isinstance(sub, (list, tuple)) and sub else str(sub))
            else:
                texts.append(str(message))
        parts.append(f"{field}: {'; '.join(texts)}")
    return '; '.join(parts)


def _fetch_product_snapshot(product_id, quantity, auth_header):
    """
    Hỏi Service quản lý sản phẩm (Service 2) thông tin sản phẩm + kiểm tra tồn kho.

    Trả về (snapshot, None) nếu hợp lệ, hoặc (None, Response lỗi) khi:
    - Sản phẩm không tồn tại (404 từ Service 2)  -> 400
    - Tồn kho không đủ                           -> 400
    - Service 2 không gọi được / báo 5xx         -> 503

    Snapshot lưu lại tên + giá tại thời điểm đặt hàng để đơn hàng không bị
    ảnh hưởng khi sản phẩm đổi tên/đ giá về sau.
    """
    try:
        product = ProductServiceClient().get_product(product_id, auth_header)
    except ProductNotFound:
        return None, Response({
            "error": "Sản phẩm không tồn tại",
            "detail": f"Sản phẩm #{product_id} không tồn tại trong dịch vụ quản lý sản phẩm.",
        }, status=status.HTTP_400_BAD_REQUEST)
    except ProductServiceUnavailable:
        return None, Response({
            "error": "Service Unavailable",
            "detail": "Service quản lý sản phẩm hiện không khả dụng. Vui lòng thử lại sau.",
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    # So sánh số lượng yêu cầu với tồn kho hiện có (view giữ vai trò này)
    stock = int(product.get('quantity') or 0)
    if quantity > stock:
        return None, Response({
            "error": "Tồn kho không đủ",
            "detail": f"Sản phẩm '{product.get('name', '')}' chỉ còn {stock} sản phẩm trong kho.",
        }, status=status.HTTP_400_BAD_REQUEST)

    snapshot = {
        'product_id': product_id,
        'product_name': product.get('name', ''),
        'unit_price': Decimal(str(product.get('price') or 0)),
    }
    return snapshot, None


def _recalc_order_total(order):
    """Tính lại total_amount của đơn = tổng total_price các dòng hàng còn lại."""
    total = order.items.aggregate(total=Sum('total_price'))['total'] or Decimal('0')
    order.total_amount = total
    order.save(update_fields=['total_amount'])


class OrderListCreateView(generics.ListCreateAPIView):
    """
    GET    /orders     -> Lấy danh sách tất cả đơn hàng (dạng phẳng, không kèm items)
    POST   /orders     -> Tạo đơn hàng mới (kiểm tra tồn kho qua Service sản phẩm)
    """
    queryset = Order.objects.all().order_by('id')
    serializer_class = OrderSerializer  # dùng cho GET list

    def create(self, request, *args, **kwargs):
        """
        Tạo đơn hàng: hỏi tồn kho Service 2 TRƯỚC, sau đó mới ghi CSDL
        (đơn + các dòng hàng trong cùng một transaction).
        """
        input_serializer = OrderCreateSerializer(data=request.data)
        if not input_serializer.is_valid():
            return Response({
                "error": "Dữ liệu không hợp lệ",
                "detail": _validation_detail(input_serializer.errors),
            }, status=status.HTTP_400_BAD_REQUEST)

        data = input_serializer.validated_data
        # Forward header Authorization sang Service 2 để nó xác thực JWT
        auth_header = request.headers.get('Authorization', '')

        # 1. Kiểm tra từng dòng hàng với Service quản lý sản phẩm
        snapshots = []
        for item in data['items']:
            snapshot, error = _fetch_product_snapshot(
                item['product_id'], item['quantity'], auth_header)
            if error:
                return error
            snapshot['quantity'] = item['quantity']
            snapshot['total_price'] = snapshot['unit_price'] * item['quantity']
            snapshots.append(snapshot)

        total_amount = sum((s['total_price'] for s in snapshots), Decimal('0'))

        # 2. Mọi dòng hàng hợp lệ -> ghi CSDL một lần (all-or-nothing)
        with transaction.atomic():
            order = Order.objects.create(
                customer_name=data['customer_name'],
                customer_email=data['customer_email'],
                status='pending',
                total_amount=total_amount,
            )
            for s in snapshots:
                OrderItem.objects.create(
                    order=order,
                    product_id=s['product_id'],
                    product_name=s['product_name'],
                    quantity=s['quantity'],
                    unit_price=s['unit_price'],
                    total_price=s['total_price'],
                )

        return Response({
            "message": "Tạo đơn hàng thành công",
            "order": OrderDetailSerializer(order).data,
        }, status=status.HTTP_201_CREATED)


class OrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /orders/id  -> Chi tiết một đơn hàng (kèm danh sách items)
    PUT    /orders/id  -> Cập nhật trạng thái / thông tin khách
    DELETE /orders/id  -> Xoá đơn hàng (cascade các dòng hàng)
    """
    queryset = Order.objects.all()
    serializer_class = OrderDetailSerializer

    def update(self, request, *args, **kwargs):
        """
        PUT: chủ yếu đổi trạng thái (pending/completed/cancelled),
        kèm tuỳ chọn sửa tên/email khách hàng.
        """
        order = self.get_object()  # tự trả 404 nếu đơn không tồn tại

        input_serializer = OrderStatusUpdateSerializer(data=request.data)
        if not input_serializer.is_valid():
            errors = input_serializer.errors
            if 'status' in errors:
                detail = STATUS_INVALID_DETAIL
            else:
                detail = _validation_detail(errors)
            return Response({
                "error": "Dữ liệu không hợp lệ",
                "detail": detail,
            }, status=status.HTTP_400_BAD_REQUEST)

        data = input_serializer.validated_data
        for field in ('status', 'customer_name', 'customer_email'):
            if field in data:
                setattr(order, field, data[field])
        order.save()

        return Response(OrderDetailSerializer(order).data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        """
        DELETE: xoá đơn hàng — các OrderItem bị xoá theo tự động
        nhờ on_delete=CASCADE trên khoá ngoại.
        """
        return super().destroy(request, *args, **kwargs)


class OrderItemListCreateView(generics.ListCreateAPIView):
    """
    GET    /order_items     -> Danh sách tất cả dòng hàng (kèm order_id)
    POST   /order_items     -> Thêm một dòng hàng vào đơn hiện có
    """
    queryset = OrderItem.objects.all().order_by('id')
    serializer_class = OrderItemSerializer  # dùng cho GET list

    def create(self, request, *args, **kwargs):
        """
        Thêm dòng hàng vào đơn hiện có: đơn phải tồn tại, sản phẩm phải còn đủ
        tồn kho (hỏi Service 2), sau đó tạo dòng hàng + tính lại tổng tiền đơn.
        """
        input_serializer = OrderItemCreateSerializer(data=request.data)
        if not input_serializer.is_valid():
            return Response({
                "error": "Dữ liệu không hợp lệ",
                "detail": _validation_detail(input_serializer.errors),
            }, status=status.HTTP_400_BAD_REQUEST)

        data = input_serializer.validated_data

        # 1. Đơn hàng phải tồn tại mới thêm được dòng hàng
        order = Order.objects.filter(id=data['order_id']).first()
        if not order:
            return Response({
                "error": "Đơn hàng không tồn tại",
                "detail": f"Đơn hàng #{data['order_id']} không tồn tại trong hệ thống.",
            }, status=status.HTTP_400_BAD_REQUEST)

        # 2. Hỏi tồn kho + snapshot tên/giá từ Service 2
        auth_header = request.headers.get('Authorization', '')
        snapshot, error = _fetch_product_snapshot(
            data['product_id'], data['quantity'], auth_header)
        if error:
            return error

        # 3. Tạo dòng hàng và tính lại tổng tiền của đơn
        with transaction.atomic():
            item = OrderItem.objects.create(
                order=order,
                product_id=snapshot['product_id'],
                product_name=snapshot['product_name'],
                quantity=data['quantity'],
                unit_price=snapshot['unit_price'],
                total_price=snapshot['unit_price'] * data['quantity'],
            )
            _recalc_order_total(order)

        return Response({
            "message": "Thêm dòng hàng vào đơn hàng thành công",
            "item": OrderItemSerializer(item).data,
        }, status=status.HTTP_201_CREATED)


class OrderItemDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /order_items/id  -> Chi tiết một dòng hàng
    PUT    /order_items/id  -> Đổi số lượng / đổi sản phẩm của dòng hàng
    DELETE /order_items/id  -> Xoá dòng hàng, tính lại tổng tiền đơn
    """
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer

    def update(self, request, *args, **kwargs):
        """
        PUT: đổi số lượng (bắt buộc). Nếu gửi kèm product_id thì chuyển sang
        sản phẩm khác và snapshot lại tên + giá; luôn kiểm tra tồn kho với
        số lượng mới trước khi ghi CSDL.
        """
        item = self.get_object()  # tự trả 404 nếu dòng hàng không tồn tại

        input_serializer = OrderItemUpdateSerializer(data=request.data)
        if not input_serializer.is_valid():
            return Response({
                "error": "Dữ liệu không hợp lệ",
                "detail": _validation_detail(input_serializer.errors),
            }, status=status.HTTP_400_BAD_REQUEST)

        data = input_serializer.validated_data
        product_id = data.get('product_id', item.product_id)
        quantity = data['quantity']

        # Hỏi Service 2: snapshot mới + kiểm tra tồn kho theo số lượng mới
        auth_header = request.headers.get('Authorization', '')
        snapshot, error = _fetch_product_snapshot(product_id, quantity, auth_header)
        if error:
            return error

        with transaction.atomic():
            item.product_id = snapshot['product_id']
            item.product_name = snapshot['product_name']
            item.unit_price = snapshot['unit_price']
            item.quantity = quantity
            item.total_price = snapshot['unit_price'] * quantity
            item.save()
            _recalc_order_total(item.order)

        return Response(OrderItemSerializer(item).data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        """DELETE: xoá dòng hàng rồi tính lại total_amount của đơn cha."""
        item = self.get_object()
        order = item.order

        with transaction.atomic():
            item.delete()
            _recalc_order_total(order)

        return Response(status=status.HTTP_204_NO_CONTENT)
