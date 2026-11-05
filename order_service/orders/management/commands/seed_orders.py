from decimal import Decimal

from django.core.management.base import BaseCommand
from orders.models import Order, OrderItem


class Command(BaseCommand):
    help = 'Tạo sẵn đơn hàng mẫu (kèm order items) để kiểm thử API quản lý đơn hàng (Bài 4)'

    def handle(self, *args, **options):
        # Dữ liệu snapshot TĨNH — không gọi sang product service,
        # chạy nhiều lần không trùng lặp nhờ update_or_create.
        samples = [
            {
                'customer_name': 'Nguyễn Văn A',
                'customer_email': 'nguyenvana@example.com',
                'status': 'pending',
                'items': [
                    {
                        'product_id': 1,
                        'product_name': 'Laptop Dell XPS 15',
                        'quantity': 1,
                        'unit_price': Decimal('35000000'),
                    },
                    {
                        'product_id': 2,
                        'product_name': 'Chuột Logitech MX Master 3S',
                        'quantity': 2,
                        'unit_price': Decimal('2500000'),
                    },
                ],
            },
            {
                'customer_name': 'Trần Thị B',
                'customer_email': 'tranthib@example.com',
                'status': 'completed',
                'items': [
                    {
                        'product_id': 3,
                        'product_name': 'Bàn phím Keychron K2',
                        'quantity': 1,
                        'unit_price': Decimal('3200000'),
                    },
                    {
                        'product_id': 2,
                        'product_name': 'Chuột Logitech MX Master 3S',
                        'quantity': 1,
                        'unit_price': Decimal('2500000'),
                    },
                ],
            },
        ]

        for sample in samples:
            total_amount = sum(
                (item['unit_price'] * item['quantity'] for item in sample['items']),
                Decimal('0'),
            )
            order, created = Order.objects.update_or_create(
                customer_email=sample['customer_email'],
                defaults={
                    'customer_name': sample['customer_name'],
                    'total_amount': total_amount,
                    'status': sample['status'],
                },
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Đã tạo đơn hàng mới: {order}"))
            else:
                self.stdout.write(self.style.WARNING(f"Đã tồn tại, cập nhật: {order}"))

            for item in sample['items']:
                _, item_created = OrderItem.objects.update_or_create(
                    order=order,
                    product_id=item['product_id'],
                    defaults={
                        'product_name': item['product_name'],
                        'quantity': item['quantity'],
                        'unit_price': item['unit_price'],
                        'total_price': item['unit_price'] * item['quantity'],
                    },
                )
                action = 'tạo' if item_created else 'cập nhật'
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  Đã {action} item: {item['product_name']} x{item['quantity']}"
                    )
                )

        total_orders = Order.objects.count()
        total_items = OrderItem.objects.count()
        self.stdout.write(
            self.style.SUCCESS(
                f"Hoàn tất! Hiện có {total_orders} đơn hàng và {total_items} order items trong cơ sở dữ liệu."
            )
        )
