from django.core.management.base import BaseCommand
from products.models import Product


class Command(BaseCommand):
    help = 'Tạo sẵn sản phẩm mẫu để kiểm thử API quản lý sản phẩm (Bài 3)'

    def handle(self, *args, **options):
        samples = [
            {
                'name': 'Laptop Dell XPS 15',
                'description': 'Laptop hiệu năng cao cho lập trình và đồ họa',
                'price': 35000000,
                'quantity': 10,
            },
            {
                'name': 'Chuột Logitech MX Master 3S',
                'description': 'Chuột không dây, pin 70 ngày',
                'price': 2500000,
                'quantity': 50,
            },
            {
                'name': 'Bàn phím Keychron K2',
                'description': 'Bàn phím cơ 75%, kết nối Bluetooth / Type-C',
                'price': 3200000,
                'quantity': 25,
            },
        ]

        for item in samples:
            product, created = Product.objects.get_or_create(
                name=item['name'],
                defaults={
                    'description': item['description'],
                    'price': item['price'],
                    'quantity': item['quantity'],
                },
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Da tao san pham moi: {product}"))
            else:
                self.stdout.write(self.style.WARNING(f"Da ton tai, bo qua: {product}"))

        total = Product.objects.count()
        self.stdout.write(self.style.SUCCESS(f"Hoan tat! Hien co {total} san pham trong co so du lieu."))
