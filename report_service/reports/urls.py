from django.urls import re_path

from .views import (OrderReportListCreateView, OrderReportDetailView,
                    ProductReportListCreateView, ProductReportDetailView)

# Mirror cách khai báo URL của order_service (Bài 4): dùng re_path với /?$
# để cả URL có và không có dấu "/" cuối đều hợp lệ (ví dụ /reports/orders và /reports/orders/).
urlpatterns = [
    # RESTful API báo cáo đơn hàng
    re_path(r'^reports/orders/?$', OrderReportListCreateView.as_view(), name='order-report-list'),
    re_path(r'^reports/orders/(?P<pk>\d+)/?$', OrderReportDetailView.as_view(), name='order-report-detail'),

    # RESTful API báo cáo sản phẩm
    re_path(r'^reports/products/?$', ProductReportListCreateView.as_view(), name='product-report-list'),
    re_path(r'^reports/products/(?P<pk>\d+)/?$', ProductReportDetailView.as_view(), name='product-report-detail'),
]
