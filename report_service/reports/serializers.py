from rest_framework import serializers

from .models import OrderReport, ProductReport


# ---------------------------------------------------------------------------
# Serializer xuất dữ liệu (output) — dùng khi trả JSON về cho client
# ---------------------------------------------------------------------------

class ProductReportSerializer(serializers.ModelSerializer):
    """Một dòng báo cáo sản phẩm — dùng cho GET /reports/products."""
    # FK 'order_report' được trả về dưới dạng order_report_id cho client dễ đọc
    order_report_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = ProductReport
        fields = ['id', 'order_report_id', 'product_id', 'total_sold',
                  'revenue', 'cost', 'profit']
        read_only_fields = ['id', 'product_id', 'total_sold',
                            'revenue', 'cost', 'profit']


class OrderReportSerializer(serializers.ModelSerializer):
    """Báo cáo đơn hàng dạng phẳng (không kèm product_reports) — dùng cho GET /reports/orders."""

    class Meta:
        model = OrderReport
        fields = ['id', 'order_id', 'total_revenue', 'total_cost', 'total_profit']
        read_only_fields = ['id', 'total_revenue', 'total_cost', 'total_profit']


class OrderReportDetailSerializer(serializers.ModelSerializer):
    """Báo cáo đơn hàng kèm danh sách báo cáo sản phẩm — dùng cho detail và response sau khi tạo."""
    product_reports = ProductReportSerializer(many=True, read_only=True)

    class Meta:
        model = OrderReport
        fields = ['id', 'order_id', 'total_revenue', 'total_cost',
                  'total_profit', 'product_reports']
        read_only_fields = ['id', 'total_revenue', 'total_cost', 'total_profit']


# ---------------------------------------------------------------------------
# Serializer nhận dữ liệu (input) — dùng để kiểm tra body client gửi lên
# ---------------------------------------------------------------------------

class OrderReportCreateSerializer(serializers.Serializer):
    """
    Body tạo báo cáo đơn hàng: {"order_id": 3, "cost_rate": 0.7}.
    cost_rate là tuỳ chọn (mặc định 0.7 = chi phí bằng 70% doanh thu).
    """
    order_id = serializers.IntegerField(min_value=1)
    cost_rate = serializers.FloatField(required=False, default=0.7)

    def validate_cost_rate(self, value):
        """Tỷ lệ chi phí phải nằm trong khoảng [0, 1]."""
        if value < 0 or value > 1:
            raise serializers.ValidationError(
                "Tỷ lệ chi phí phải nằm trong khoảng từ 0 đến 1.")
        return value


class ProductReportCreateSerializer(serializers.Serializer):
    """
    Body tạo báo cáo sản phẩm:
    {"order_report_id": 1, "product_id": 2, "unit_cost": 2500000}.
    """
    order_report_id = serializers.IntegerField(min_value=1)
    product_id = serializers.IntegerField(min_value=1)
    unit_cost = serializers.DecimalField(max_digits=10, decimal_places=2,
                                         min_value=0)
