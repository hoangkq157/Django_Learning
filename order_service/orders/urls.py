from django.urls import path, re_path

from .views import (OrderListCreateView, OrderDetailView,
                    OrderItemListCreateView, OrderItemDetailView)

# Mirror cách khai báo URL của product_service (Bài 3): dùng re_path với /?$
# để cả URL có và không có dấu "/" cuối đều hợp lệ (ví dụ /orders và /orders/).
urlpatterns = [
    # RESTful API quản lý đơn hàng
    re_path(r'^orders/?$', OrderListCreateView.as_view(), name='order-list'),
    re_path(r'^orders/(?P<pk>\d+)/?$', OrderDetailView.as_view(), name='order-detail'),

    # RESTful API quản lý dòng hàng trong đơn
    re_path(r'^order_items/?$', OrderItemListCreateView.as_view(), name='order-item-list'),
    re_path(r'^order_items/(?P<pk>\d+)/?$', OrderItemDetailView.as_view(), name='order-item-detail'),
]
