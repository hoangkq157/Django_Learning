from django.db import models


class OrderReport(models.Model):
    """
    Bảng orders_reports — đối chiếu contract Bài thực hành số 5.
    Lưu vết báo cáo doanh thu / chi phí / lợi nhuận cho một đơn hàng
    đang quản lý ở Service 3 (Bài 4), liên kết qua order_id
    (không dùng FK vì khác database — mỗi service có DB riêng).
    """

    id = models.AutoField(primary_key=True)                      # INT (PRIMARY KEY)
    order_id = models.IntegerField()                             # INT — lưu vết liên kết dịch vụ quản lý đơn hàng
    total_revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # DECIMAL(10,2)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)     # DECIMAL(10,2)
    total_profit = models.DecimalField(max_digits=10, decimal_places=2, default=0)   # DECIMAL(10,2)

    class Meta:
        db_table = 'orders_reports'
        verbose_name = 'Báo cáo đơn hàng'
        verbose_name_plural = 'Báo cáo đơn hàng'

    def __str__(self):
        return f'Báo cáo đơn hàng #{self.id} (order {self.order_id})'


class ProductReport(models.Model):
    """
    Bảng product_reports — mỗi dòng là báo cáo bán chạy của một sản phẩm
    thuộc về báo cáo đơn hàng cha, lưu vết qua product_id của Service 2 (Bài 3).
    """

    id = models.AutoField(primary_key=True)                      # INT (PRIMARY KEY)
    order_report = models.ForeignKey(OrderReport, related_name='product_reports', on_delete=models.CASCADE, db_column='order_report_id')  # FK orders_reports.id
    product_id = models.IntegerField()                           # INT — id sản phẩm ở Service 2
    total_sold = models.IntegerField(default=0)                  # INT
    revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # DECIMAL(10,2)
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)     # DECIMAL(10,2)
    profit = models.DecimalField(max_digits=10, decimal_places=2, default=0)   # DECIMAL(10,2)

    class Meta:
        db_table = 'product_reports'
        verbose_name = 'Báo cáo sản phẩm'
        verbose_name_plural = 'Báo cáo sản phẩm'

    def __str__(self):
        return f'Báo cáo SP #{self.id} — SP {self.product_id} x{self.total_sold}'
