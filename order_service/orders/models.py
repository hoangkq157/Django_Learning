from django.db import models


class Order(models.Model):
    """
    Bảng orders — đối chiếu contract Bài thực hành số 4.
    """

    class StatusChoices(models.TextChoices):
        PENDING = 'pending', 'Chờ xử lý'
        COMPLETED = 'completed', 'Hoàn thành'
        CANCELLED = 'cancelled', 'Đã hủy'

    id = models.AutoField(primary_key=True)                      # INT (PRIMARY KEY)
    customer_name = models.CharField(max_length=255)             # VARCHAR(255)
    customer_email = models.CharField(max_length=255)            # VARCHAR(255)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # DECIMAL(10,2)
    status = models.CharField(max_length=50, choices=StatusChoices.choices, default='pending')  # VARCHAR(50)
    created_at = models.DateTimeField(auto_now_add=True)         # TIMESTAMP (tự ghi khi tạo)
    updated_at = models.DateTimeField(auto_now=True)             # TIMESTAMP (tự cập nhật khi sửa)

    class Meta:
        verbose_name = 'Đơn hàng'
        verbose_name_plural = 'Đơn hàng'

    def __str__(self):
        return f'Đơn hàng #{self.id} — {self.customer_name}'


# Alias mức module để tiện import: from orders.models import StatusChoices
StatusChoices = Order.StatusChoices


class OrderItem(models.Model):
    """
    Bảng order items — mỗi dòng là một sản phẩm thuộc về đơn hàng,
    lưu snapshot (tên, giá) tại thời điểm đặt hàng để không phụ thuộc
    vào sự tồn tại của sản phẩm ở Service 2 (Bài 3).
    """

    id = models.AutoField(primary_key=True)                      # INT (PRIMARY KEY)
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE, db_column='order_id')  # FK orders.id
    product_id = models.IntegerField()                           # INT — id sản phẩm ở Service 2
    product_name = models.CharField(max_length=255)              # VARCHAR(255) — snapshot tên sản phẩm
    quantity = models.IntegerField(default=1)                    # INT
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)  # DECIMAL(10,2) — snapshot giá
    total_price = models.DecimalField(max_digits=10, decimal_places=2)  # DECIMAL(10,2) = quantity * unit_price

    class Meta:
        verbose_name = 'Chi tiết đơn hàng'
        verbose_name_plural = 'Chi tiết đơn hàng'

    def __str__(self):
        return f'Chi tiết #{self.id}: {self.product_name} x{self.quantity}'
