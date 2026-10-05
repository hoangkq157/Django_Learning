from rest_framework import generics
from .models import Product
from .serializers import ProductSerializer


class ProductListCreateView(generics.ListCreateAPIView):
    """
    GET    /products     -> Lấy danh sách tất cả sản phẩm
    POST   /products     -> Thêm sản phẩm mới
    """
    queryset = Product.objects.all().order_by('id')
    serializer_class = ProductSerializer


class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /products/id  -> Chi tiết một sản phẩm
    PUT    /products/id  -> Cập nhật sản phẩm
    DELETE /products/id  -> Xóa sản phẩm
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
