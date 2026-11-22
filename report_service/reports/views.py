from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction
from rest_framework import generics, status
from rest_framework.response import Response

from .models import OrderReport, ProductReport
from .serializers import (OrderReportSerializer, OrderReportDetailSerializer,
                          ProductReportSerializer, OrderReportCreateSerializer,
                          ProductReportCreateSerializer)
from .services import (OrderServiceClient, OrderNotFound,
                       OrderServiceUnavailable, ProductServiceClient,
                       ProductNotFound, ProductServiceUnavailable)

# Làm tròn đến 2 chữ số thập phân (chuẩn DecimalField 10,2 của models)
TWO_PLACES = Decimal('0.01')


def _round2(value):
    """Làm tròn một giá trị Decimal về 2 chữ số thập phân."""
    return Decimal(value).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def _validation_detail(errors):
    """Gom các lỗi của serializer thành một dòng thông điệp dễ đọc cho client."""
    parts = []
    for field, messages in errors.items():
        texts = [str(m) for m in (messages if isinstance(messages, (list, tuple)) else [messages])]
        parts.append(f"{field}: {'; '.join(texts)}")
    return '; '.join(parts)


def _get_order_or_error(order_id, auth_header):
    """
    Hỏi Service quản lý đơn hàng (Service 3) dữ liệu đơn hàng <order_id>.

    Trả về (order_dict, None) nếu thành công, hoặc (None, Response lỗi) khi:
    - Đơn hàng không tồn tại (404 từ Service 3)      -> 404
    - Service 3 không gọi được / báo 5xx             -> 503
    """
    try:
        order = OrderServiceClient().get_order(order_id, auth_header)
    except OrderNotFound:
        return None, Response({
            "error": "Không tìm thấy đơn hàng",
            "detail": f"Đơn hàng #{order_id} không tồn tại trong dịch vụ quản lý đơn hàng.",
        }, status=status.HTTP_404_NOT_FOUND)
    except OrderServiceUnavailable:
        return None, Response({
            "error": "Service Unavailable",
            "detail": "Service quản lý đơn hàng hiện không khả dụng. Vui lòng thử lại sau.",
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    return order, None


class OrderReportListCreateView(generics.ListCreateAPIView):
    """
    GET    /reports/orders     -> Danh sách tất cả báo cáo đơn hàng (dạng phẳng)
    POST   /reports/orders     -> Tổng hợp báo cáo cho một đơn hàng (gọi Service 3)
    """
    queryset = OrderReport.objects.all().order_by('id')
    serializer_class = OrderReportSerializer  # dùng cho GET list

    def create(self, request, *args, **kwargs):
        """
        Tạo báo cáo đơn hàng: hỏi Service 3 dữ liệu đơn hàng + các dòng hàng,
        sau đó tính doanh thu / chi phí / lợi nhuận và ghi CSDL
        (báo cáo đơn + báo cáo từng sản phẩm trong cùng một transaction).
        """
        input_serializer = OrderReportCreateSerializer(data=request.data)
        if not input_serializer.is_valid():
            return Response({
                "error": "Dữ liệu không hợp lệ",
                "detail": _validation_detail(input_serializer.errors),
            }, status=status.HTTP_400_BAD_REQUEST)

        data = input_serializer.validated_data
        order_id = data['order_id']
        cost_rate = Decimal(str(data.get('cost_rate', 0.7)))

        # Forward header Authorization sang Service 3 để nó xác thực JWT
        auth_header = request.headers.get('Authorization', '')

        # 1. Lấy dữ liệu đơn hàng từ Service quản lý đơn hàng
        order, error = _get_order_or_error(order_id, auth_header)
        if error:
            return error

        # 2. Tổng hợp số liệu từ đơn hàng:
        #    - total_revenue = tổng tiền đơn (total_amount)
        #    - với MỖI dòng hàng: chi phí = đơn giá x số lượng x cost_rate
        #    - total_cost = tổng chi phí các dòng hàng
        #    - total_profit = doanh thu - chi phí
        total_revenue = Decimal(str(order.get('total_amount') or 0))
        total_cost = Decimal('0')
        item_reports = []
        for item in order.get('items', []):
            unit_price = Decimal(str(item.get('unit_price') or 0))
            quantity = int(item.get('quantity') or 0)
            item_revenue = Decimal(str(item.get('total_price') or 0))
            item_cost = unit_price * quantity * cost_rate

            total_cost += item_cost
            item_reports.append({
                'product_id': item.get('product_id'),
                'total_sold': quantity,
                'revenue': _round2(item_revenue),
                'cost': _round2(item_cost),
                'profit': _round2(item_revenue - item_cost),
            })

        total_revenue = _round2(total_revenue)
        total_cost = _round2(total_cost)
        total_profit = _round2(total_revenue - total_cost)

        # 3. Ghi CSDL một lần (all-or-nothing): báo cáo đơn + từng sản phẩm
        with transaction.atomic():
            report = OrderReport.objects.create(
                order_id=order_id,
                total_revenue=total_revenue,
                total_cost=total_cost,
                total_profit=total_profit,
            )
            for item in item_reports:
                ProductReport.objects.create(
                    order_report=report,
                    product_id=item['product_id'],
                    total_sold=item['total_sold'],
                    revenue=item['revenue'],
                    cost=item['cost'],
                    profit=item['profit'],
                )

        return Response({
            "message": "Tạo báo cáo đơn hàng thành công",
            "report": OrderReportDetailSerializer(report).data,
        }, status=status.HTTP_201_CREATED)


class OrderReportDetailView(generics.RetrieveDestroyAPIView):
    """
    GET    /reports/orders/id  -> Chi tiết một báo cáo đơn hàng (kèm product_reports)
    DELETE /reports/orders/id  -> Xoá báo cáo đơn hàng (cascade các báo cáo sản phẩm)
    """
    queryset = OrderReport.objects.all()
    serializer_class = OrderReportDetailSerializer

    def destroy(self, request, *args, **kwargs):
        """
        DELETE: xoá báo cáo đơn hàng — các ProductReport bị xoá theo tự động
        nhờ on_delete=CASCADE trên khoá ngoại.
        """
        return super().destroy(request, *args, **kwargs)


class ProductReportListCreateView(generics.ListCreateAPIView):
    """
    GET    /reports/products     -> Danh sách tất cả báo cáo sản phẩm (kèm order_report_id)
    POST   /reports/products     -> Tạo báo cáo cho một sản phẩm trong đơn đã có báo cáo
    """
    queryset = ProductReport.objects.all().order_by('id')
    serializer_class = ProductReportSerializer  # dùng cho GET list

    def create(self, request, *args, **kwargs):
        """
        Tạo báo cáo sản phẩm: báo cáo đơn phải tồn tại, sản phẩm phải còn
        tồn tại (hỏi Service 2) và thực sự có trong đơn hàng (hỏi Service 3),
        sau đó tổng hợp số liệu bán được của sản phẩm trong đơn đó.
        """
        input_serializer = ProductReportCreateSerializer(data=request.data)
        if not input_serializer.is_valid():
            return Response({
                "error": "Dữ liệu không hợp lệ",
                "detail": _validation_detail(input_serializer.errors),
            }, status=status.HTTP_400_BAD_REQUEST)

        data = input_serializer.validated_data

        # 1. Báo cáo đơn hàng phải tồn tại trong DB của service này
        report = OrderReport.objects.filter(id=data['order_report_id']).first()
        if not report:
            return Response({
                "error": "Báo cáo đơn hàng không tồn tại",
                "detail": f"Báo cáo đơn hàng #{data['order_report_id']} không tồn tại.",
            }, status=status.HTTP_400_BAD_REQUEST)

        # Forward header Authorization sang Service 2/3 để chúng xác thực JWT
        auth_header = request.headers.get('Authorization', '')

        # 2. Sản phẩm phải còn tồn tại trong Service quản lý sản phẩm
        try:
            ProductServiceClient().get_product(data['product_id'], auth_header)
        except ProductNotFound:
            return Response({
                "error": "Sản phẩm không tồn tại",
                "detail": f"Sản phẩm #{data['product_id']} không tồn tại trong dịch vụ quản lý sản phẩm.",
            }, status=status.HTTP_400_BAD_REQUEST)
        except ProductServiceUnavailable:
            return Response({
                "error": "Service Unavailable",
                "detail": "Service quản lý sản phẩm hiện không khả dụng. Vui lòng thử lại sau.",
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        # 3. Lấy lại đơn hàng gốc từ Service 3 (đơn có thể đã bị xoá)
        order, error = _get_order_or_error(report.order_id, auth_header)
        if error:
            if error.status_code == status.HTTP_404_NOT_FOUND:
                # Đơn hàng gốc không còn -> không thể tổng hợp số liệu
                return Response({
                    "error": "Đơn hàng không còn tồn tại",
                    "detail": f"Đơn hàng #{report.order_id} không còn tồn tại trong dịch vụ quản lý đơn hàng.",
                }, status=status.HTTP_400_BAD_REQUEST)
            return error  # 503 khi Service đơn hàng không khả dụng

        # 4. Lọc các dòng hàng của sản phẩm trong đơn hàng
        matched_items = [item for item in order.get('items', [])
                         if item.get('product_id') == data['product_id']]
        if not matched_items:
            return Response({
                "error": "Sản phẩm không có trong đơn hàng",
                "detail": f"Sản phẩm #{data['product_id']} không xuất hiện trong đơn hàng #{report.order_id}.",
            }, status=status.HTTP_400_BAD_REQUEST)

        # 5. Tổng hợp số liệu bán được của sản phẩm trong đơn:
        #    - total_sold = tổng số lượng các dòng hàng
        #    - revenue    = tổng tiền các dòng hàng
        #    - cost       = đơn giá chi phí (client gửi) x số lượng bán
        #    - profit     = doanh thu - chi phí
        total_sold = sum(int(item.get('quantity') or 0) for item in matched_items)
        revenue = sum((Decimal(str(item.get('total_price') or 0))
                       for item in matched_items), Decimal('0'))
        unit_cost = Decimal(str(data['unit_cost']))
        cost = unit_cost * total_sold
        profit = revenue - cost

        # 6. Ghi báo cáo sản phẩm vào CSDL
        product_report = ProductReport.objects.create(
            order_report=report,
            product_id=data['product_id'],
            total_sold=total_sold,
            revenue=_round2(revenue),
            cost=_round2(cost),
            profit=_round2(profit),
        )

        return Response({
            "message": "Tạo báo cáo sản phẩm thành công",
            "report": ProductReportSerializer(product_report).data,
        }, status=status.HTTP_201_CREATED)


class ProductReportDetailView(generics.RetrieveDestroyAPIView):
    """
    GET    /reports/products/id  -> Chi tiết một báo cáo sản phẩm
    DELETE /reports/products/id  -> Xoá báo cáo sản phẩm
    """
    queryset = ProductReport.objects.all()
    serializer_class = ProductReportSerializer
