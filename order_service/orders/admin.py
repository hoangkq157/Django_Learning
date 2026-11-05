from django.contrib import admin

from orders.models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    """Hiển thị các dòng sản phẩm ngay trong trang sửa đơn hàng."""
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer_name', 'customer_email', 'total_amount', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('customer_name', 'customer_email')
    inlines = (OrderItemInline,)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'product_id', 'product_name', 'quantity', 'unit_price', 'total_price')
