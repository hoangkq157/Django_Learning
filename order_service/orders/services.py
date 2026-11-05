import requests
from django.conf import settings


class ProductNotFound(Exception):
    """Ném ra khi Service quản lý sản phẩm trả về 404 (sản phẩm không tồn tại)."""


class ProductServiceUnavailable(Exception):
    """Ném ra khi không gọi được Service sản phẩm hoặc nó báo lỗi hệ thống (5xx)."""


class ProductServiceClient:
    """
    Client HTTP gọi sang Service quản lý sản phẩm (Bài 3, cổng 8001).

    Theo tinh thần SOA: service đơn hàng KHÔNG đọc trực tiếp DB sản phẩm
    mà gọi API /products/<id>/, đồng thời forward header Authorization của
    client sang để Service sản phẩm tự xác thực JWT với Service xác thực.
    """

    def get_product(self, product_id, auth_header):
        """
        Lấy thông tin sản phẩm (tên, giá, tồn kho...) từ Service 2.

        - 200   -> trả về dict {id, name, price, quantity, ...}
        - 404   -> ném ProductNotFound
        - Lỗi kết nối / timeout / mã 5xx -> ném ProductServiceUnavailable

        Lưu ý: logic "tồn kho có đủ hay không" KHÔNG nằm ở client này,
        view sẽ tự so sánh quantity yêu cầu với tồn kho nhận được.
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
