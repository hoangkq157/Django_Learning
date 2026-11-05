from rest_framework import serializers

from .models import Order, OrderItem

# Các trạng thái hợp lệ của một đơn hàng (khớp với choices trong models.py)
VALID_ORDER_STATUSES = ('pending', 'completed', 'cancelled')


# ---------------------------------------------------------------------------
# Serializer xuất dữ liệu (output) — dùng khi trả JSON về cho client
# ---------------------------------------------------------------------------

class OrderSerializer(serializers.ModelSerializer):
    """Đơn hàng dạng phẳng (không kèm items) — dùng cho GET /orders."""

    class Meta:
        model = Order
        fields = ['id', 'customer_name', 'customer_email', 'total_amount',
                  'status', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class OrderItemSerializer(serializers.ModelSerializer):
    """Một dòng hàng trong đơn hàng — dùng cho GET /order_items."""
    # FK 'order' được trả về dưới dạng order_id cho client dễ đọc
    order_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'order_id', 'product_id', 'product_name', 'quantity',
                  'unit_price', 'total_price']
        read_only_fields = ['id', 'product_id', 'product_name', 'quantity',
                            'unit_price', 'total_price']


class OrderDetailSerializer(serializers.ModelSerializer):
    """Đơn hàng kèm danh sách dòng hàng — dùng cho detail và response sau khi tạo."""
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'customer_name', 'customer_email', 'total_amount',
                  'status', 'created_at', 'updated_at', 'items']
        read_only_fields = ['id', 'created_at', 'updated_at']


# ---------------------------------------------------------------------------
# Serializer nhận dữ liệu (input) — dùng để kiểm tra body client gửi lên
# ---------------------------------------------------------------------------

class OrderItemInputSerializer(serializers.Serializer):
    """Mỗi dòng sản phẩm trong body tạo đơn: {"product_id": 1, "quantity": 2}."""
    product_id = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1, default=1)


class OrderCreateSerializer(serializers.Serializer):
    """
    Body tạo đơn hàng mới:
    {"customer_name": "...", "customer_email": "...", "items": [{...}, ...]}
    items là tuỳ chọn (cho phép tạo đơn rỗng rồi thêm sau qua /order_items).
    """
    customer_name = serializers.CharField()
    customer_email = serializers.EmailField()
    items = OrderItemInputSerializer(many=True, required=False, default=list)


class OrderStatusUpdateSerializer(serializers.Serializer):
    """
    Body cập nhật đơn hàng qua PUT /orders/<id>:
    {"status": "completed", "customer_name"?: "...", "customer_email"?: "..."}
    """
    status = serializers.CharField(required=True)
    customer_name = serializers.CharField(required=False)
    customer_email = serializers.EmailField(required=False)

    def validate_status(self, value):
        """Status phải thuộc bộ trạng thái hợp lệ của đơn hàng."""
        if value not in VALID_ORDER_STATUSES:
            raise serializers.ValidationError(
                "Trạng thái phải là một trong: pending, completed, cancelled.")
        return value


class OrderItemCreateSerializer(serializers.Serializer):
    """Body thêm dòng hàng vào đơn hiện có: {"order_id": 1, "product_id": 2, "quantity": 1}."""
    order_id = serializers.IntegerField(min_value=1)
    product_id = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1, default=1)


class OrderItemUpdateSerializer(serializers.Serializer):
    """Body cập nhật dòng hàng: quantity bắt buộc, product_id tuỳ chọn (đổi sản phẩm)."""
    quantity = serializers.IntegerField(min_value=1, required=True)
    product_id = serializers.IntegerField(min_value=1, required=False)
