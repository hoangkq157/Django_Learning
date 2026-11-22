import requests
from django.conf import settings


class OrderNotFound(Exception):
    """Ném ra khi Service quản lý đơn hàng trả về 404 (đơn hàng không tồn tại)."""


class OrderServiceUnavailable(Exception):
    """Ném ra khi không gọi được Service đơn hàng hoặc nó báo lỗi hệ thống (5xx)."""


class ProductNotFound(Exception):
    """Ném ra khi Service quản lý sản phẩm trả về 404 (sản phẩm không tồn tại)."""


class ProductServiceUnavailable(Exception):
    """Ném ra khi không gọi được Service sản phẩm hoặc nó báo lỗi hệ thống (5xx)."""


class OrderServiceClient:
    """
    Client HTTP gọi sang Service quản lý đơn hàng (Bài 4, cổng 8002).

    Theo tinh thần SOA: service báo cáo KHÔNG đọc trực tiếp DB đơn hàng
    mà gọi API /orders/<id>/, đồng thời forward header Authorization của
    client sang để Service đơn hàng tự xác thực JWT với Service xác thực.
    """

    def get_order(self, order_id, auth_header):
        """
        Lấy thông tin đơn hàng (total_amount + danh sách items) từ Service 3.

        - 200   -> trả về dict {id, customer_name, total_amount, items: [...], ...}
        - 404   -> ném OrderNotFound
        - Lỗi kết nối / timeout / mã 5xx -> ném OrderServiceUnavailable

        Lưu ý: logic tính doanh thu / chi phí KHÔNG nằm ở client này,
        view sẽ tự tổng hợp số liệu từ JSON nhận được.
        """
        base_url = settings.ORDER_SERVICE_URL.rstrip('/')
        url = f"{base_url}/orders/{order_id}"

        try:
            response = requests.get(
                url,
                headers={"Authorization": auth_header},
                timeout=5,
            )
        except requests.exceptions.RequestException:
            # Service đơn hàng đang tắt hoặc phản hồi chậm quá timeout
            raise OrderServiceUnavailable(
                f"Không gọi được Service quản lý đơn hàng tại {url}.")

        if response.status_code == 200:
            return response.json()

        if response.status_code == 404:
            raise OrderNotFound(f"Đơn hàng #{order_id} không tồn tại.")

        # 5xx hoặc các mã không lường trước (401/403 do token hỏng, ...)
        # -> coi như Service đơn hàng hiện không dùng được
        raise OrderServiceUnavailable(
            f"Service quản lý đơn hàng trả về mã {response.status_code}.")


class ProductServiceClient:
    """
    Client HTTP gọi sang Service quản lý sản phẩm (Bài 3, cổng 8001).

    Dùng để kiểm tra sản phẩm còn tồn tại hay không trước khi tạo
    báo cáo sản phẩm cho một đơn hàng.
    """

    def get_product(self, product_id, auth_header):
        """
        Lấy thông tin sản phẩm (tên, giá, tồn kho...) từ Service 2.

        - 200   -> trả về dict {id, name, price, quantity, ...}
        - 404   -> ném ProductNotFound
        - Lỗi kết nối / timeout / mã 5xx -> ném ProductServiceUnavailable
        """
        base_url = settings.PRODUCT_SERVICE_URL.rstrip('/')
        url = f"{base_url}/products/{product_id}"

        try:
            response = requests.get(
                url,
                headers={"Authorization": auth_header},
                timeout=5,
            )
        except requests.exceptions.RequestException:
            # Service sản phẩm đang tắt hoặc phản hồi chậm quá timeout
            raise ProductServiceUnavailable(
                f"Không gọi được Service quản lý sản phẩm tại {url}.")

        if response.status_code == 200:
            return response.json()

        if response.status_code == 404:
            raise ProductNotFound(f"Sản phẩm #{product_id} không tồn tại.")

        # 5xx hoặc các mã không lường trước (401/403 do token hỏng, ...)
        # -> coi như Service sản phẩm hiện không dùng được
        raise ProductServiceUnavailable(
            f"Service quản lý sản phẩm trả về mã {response.status_code}.")
