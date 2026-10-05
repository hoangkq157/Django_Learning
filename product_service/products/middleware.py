import requests as http_client
from django.http import JsonResponse
from django.conf import settings


class AuthServiceMiddleware:
    """
    Middleware xác thực token bằng cách GỌI SANG Service xác thực (Bài 2)
    tại địa chỉ settings.AUTH_SERVICE_URL — tuân thủ nguyên tắc SOA:
    service sản phẩm không tự giải mã JWT mà delegating cho service chuyên trách.

    Chỉ áp dụng cho các route bắt đầu bằng /products.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.protected_routes = ['/products']
        self.auth_url = settings.AUTH_SERVICE_URL.rstrip('/')

    def __call__(self, request):
        path = request.path.rstrip('/')
        is_protected = any(
            path == r or path.startswith(r + '/') for r in self.protected_routes
        )
        if not is_protected:
            return self.get_response(request)

        # 1. Trích token từ header Authorization (hỗ trợ cả query ?token=)
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.lower().startswith('bearer '):
            token = auth_header[7:].strip()
        elif auth_header:
            token = auth_header.strip()
        elif 'token' in request.GET:
            token = request.GET.get('token')
        else:
            token = None

        if not token:
            return JsonResponse({
                "error": "Unauthorized",
                "detail": "Vui lòng cung cấp JWT token qua Header 'Authorization: Bearer <token>'.",
            }, status=401)

        # 2. GỌI SANG SERVICE XÁC THỰC (service-to-service call)
        try:
            resp = http_client.get(
                f"{self.auth_url}/auth",
                headers={"Authorization": f"Bearer {token}"},
                timeout=5,
            )
        except http_client.RequestException:
            # Service xác thực đang tắt / không phản hồi
            return JsonResponse({
                "error": "Service Unavailable",
                "detail": "Service xác thực (Bài 2) hiện không khả dụng. Vui lòng thử lại sau.",
            }, status=503)

        # 3. Dựa vào kết quả của service cũ để quyết định cho đi hay chặn
        if resp.status_code != 200:
            detail = "Token không hợp lệ theo Service xác thực."
            try:
                body = resp.json()
                detail = body.get('detail') or body.get('error') or detail
            except Exception:
                pass
            return JsonResponse({"error": "Unauthorized", "detail": detail}, status=401)

        # Hợp lệ → gắn payload vào request cho view sử dụng nếu cần
        try:
            request.jwt_payload = resp.json().get('payload')
        except Exception:
            request.jwt_payload = None

        return self.get_response(request)
