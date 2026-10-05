from django.db import models

class Product(models.Model):
    """
    Bảng products — đối chiếu Phụ lục Bài thực hành số 3.
    """
    id = models.AutoField(primary_key=True)                      # INT (PRIMARY KEY)
    name = models.CharField(max_length=255)                      # VARCHAR(255)
    description = models.TextField(blank=True, null=True)        # TEXT
    price = models.DecimalField(max_digits=10, decimal_places=2) # DECIMAL(10,2)
    quantity = models.IntegerField(default=0)                    # INT
    created_at = models.DateTimeField(auto_now_add=True)         # TIMESTAMP (tự ghi khi tạo)
    updated_at = models.DateTimeField(auto_now=True)             # TIMESTAMP (tự cập nhật khi sửa)

    def __str__(self):
        return f"[{self.id}] {self.name}"
