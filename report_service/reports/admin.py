from django.contrib import admin

from reports.models import OrderReport, ProductReport


class ProductReportInline(admin.TabularInline):
    """Hiển thị các dòng báo cáo sản phẩm ngay trong trang sửa báo cáo đơn hàng."""
    model = ProductReport
    extra = 0


@admin.register(OrderReport)
class OrderReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'order_id', 'total_revenue', 'total_cost', 'total_profit')
    list_filter = ('order_id',)
    search_fields = ('order_id',)
    inlines = (ProductReportInline,)


@admin.register(ProductReport)
class ProductReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'order_report', 'product_id', 'total_sold', 'revenue', 'cost', 'profit')
    list_filter = ('product_id',)
    search_fields = ('product_id',)
