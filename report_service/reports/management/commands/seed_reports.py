from decimal import Decimal

from django.core.management.base import BaseCommand
from reports.models import OrderReport, ProductReport


class Command(BaseCommand):
    help = 'Tạo sẵn báo cáo mẫu (kèm báo cáo sản phẩm) để kiểm thử API báo cáo (Bài 5)'

    def handle(self, *args, **options):
        # Dữ liệu TĨNH — không gọi sang order/product service,
        # chạy nhiều lần không trùng lặp nhờ update_or_create.
        # order_id 1, 2 trùng ID các đơn hàng seed của order_service (Bài 4).
        samples = [
            {
                'order_id': 1,
                'products': [
                    {
                        'product_id': 1,   # Laptop Dell XPS 15
                        'total_sold': 1,
                        'revenue': Decimal('35000000'),
                        'cost': Decimal('30000000'),
                    },
                    {
                        'product_id': 2,   # Chuột Logitech MX Master 3S
                        'total_sold': 2,
                        'revenue': Decimal('5000000'),
                        'cost': Decimal('3600000'),
                    },
                ],
            },
            {
                'order_id': 2,
                'products': [
                    {
                        'product_id': 3,   # Bàn phím Keychron K2
                        'total_sold': 1,
                        'revenue': Decimal('3200000'),
                        'cost': Decimal('2400000'),
                    },
                    {
                        'product_id': 2,   # Chuột Logitech MX Master 3S
                        'total_sold': 1,
                        'revenue': Decimal('2500000'),
                        'cost': Decimal('1800000'),
                    },
                ],
            },
        ]

        for sample in samples:
            total_revenue = sum(
                (p['revenue'] for p in sample['products']),
                Decimal('0'),
            )
            total_cost = sum(
                (p['cost'] for p in sample['products']),
                Decimal('0'),
            )
            order_report, created = OrderReport.objects.update_or_create(
                order_id=sample['order_id'],
                defaults={
                    'total_revenue': total_revenue,
                    'total_cost': total_cost,
                    'total_profit': total_revenue - total_cost,
                },
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Đã tạo báo cáo đơn hàng mới: {order_report}"))
            else:
                self.stdout.write(self.style.WARNING(f"Đã tồn tại, cập nhật: {order_report}"))

            for product in sample['products']:
                _, product_created = ProductReport.objects.update_or_create(
                    order_report=order_report,
                    product_id=product['product_id'],
                    defaults={
                        'total_sold': product['total_sold'],
                        'revenue': product['revenue'],
                        'cost': product['cost'],
                        'profit': product['revenue'] - product['cost'],
                    },
                )
                action = 'tạo' if product_created else 'cập nhật'
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  Đã {action} báo cáo SP {product['product_id']} x{product['total_sold']}"
                    )
                )

        total_order_reports = OrderReport.objects.count()
        total_product_reports = ProductReport.objects.count()
        self.stdout.write(
            self.style.SUCCESS(
                f"Hoàn tất! Hiện có {total_order_reports} báo cáo đơn hàng "
                f"và {total_product_reports} báo cáo sản phẩm trong cơ sở dữ liệu."
            )
        )
