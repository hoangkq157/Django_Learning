"""
Bộ kiểm thử tự động cho Service Quản lý Đơn hàng (Bài thực hành số 4).

Đặc biệt: toàn bộ 12 test KHÔNG yêu cầu chạy thật bất kỳ server nào
(8000 / 8001 / 8002). Các lời gọi HTTP service-to-service được giả lập
(mock) bằng `unittest.mock`:
  - `orders.middleware` -> gọi `GET http://localhost:8000/auth` (xác thực JWT qua Service 1)
  - `orders.services`   -> gọi `GET http://localhost:8001/products/<id>` (kiểm tra tồn kho qua Service 2)

Cả hai module đều `import requests` nên dùng chung một đối tượng module;
mỗi test gắn cho mock một `side_effect` điều hướng theo URL — dù lời gọi
`requests.get` phát ra từ middleware hay từ services, mock đều trả về
phản hồi đúng cho service tương ứng.

Chạy bộ test (trong thư mục `order_service`, không cần bật server):
    python manage.py test
"""
from decimal import Decimal
from unittest.mock import patch, Mock

import requests
from rest_framework import status
from rest_framework.test import APITestCase

from orders.models import Order, OrderItem


class OrderServiceTestCase(APITestCase):
    """Bộ 12 bài kiểm thử tự động cho /orders và /order_items (Service 3)."""

    # Đơn giá & tồn kho của sản phẩm mẫu do Service 2 (đã mock) trả về
    PRODUCT_PRICE = Decimal('15000000.00')
    PRODUCT_STOCK = 10

    def setUp(self):
        # Token giả lập — middleware đã được mock nên không cần JWT thật
        self.auth_header = {'HTTP_AUTHORIZATION': 'Bearer fake.jwt.token-for-testing'}

        # Dữ liệu sản phẩm mẫu (Service 2 trả về cho GET /products/<id>)
        self.product_data = {
            "id": 1,
            "name": "Laptop Dell",
            "description": "Laptop phục vụ học tập",
            "price": "15000000.00",
            "quantity": self.PRODUCT_STOCK,
            "created_at": "2026-11-05T10:00:00Z",
            "updated_at": "2026-11-05T10:00:00Z",
        }

        # Trạng thái giả lập của 2 service phụ thuộc (mỗi test tự tinh chỉnh)
        self.auth_status_code = 200      # Service 1: 200 = token hợp lệ
        self.product_status_code = 200   # Service 2: 200 = sản phẩm tồn tại
        self.product_exception = None    # Ngoại lệ mạng khi Service 2 bị tắt

    # ------------------------------------------------------------------
    # Helper giả lập (mock) các lời gọi HTTP service-to-service
    # ------------------------------------------------------------------

    def _mock_response(self, status_code, payload):
        """Tạo đối tượng phản hồi HTTP giả lập."""
        resp = Mock()
        resp.status_code = status_code
        resp.json.return_value = payload
        return resp

    def _fake_http_get(self, url, *args, **kwargs):
        """Dispatcher điều hướng theo URL: /auth -> Service 1, /products/<id> -> Service 2."""
        if '/auth' in url:
            return self._mock_response(self.auth_status_code, {
                "valid": self.auth_status_code == 200,
                "user": {"UserName": "testuser"},
            })
        if '/products/' in url:
            if self.product_exception is not None:
                raise self.product_exception
            return self._mock_response(self.product_status_code, self.product_data)
        raise AssertionError(
            "Test chỉ mong đợi lời gọi tới /auth hoặc /products/<id>, nhận: %s" % url
        )

    @staticmethod
    def _as_decimal(value):
        """Ép kiểu an toàn: '45000000.00' (str) hoặc 45000000.0 (float) -> Decimal."""
        return Decimal(str(value))

    @staticmethod
    def _order_from_response(response_data):
        """Trích dữ liệu đơn hàng từ response tạo đơn.

        View trả về {"message": ..., "order": {...}}; helper này chịu được
        cả dạng response phẳng (order nằm ngay cấp gốc) cho đỡ phụ thuộc
        vào cách gói response của view.
        """
        return response_data.get('order', response_data)

    def _assert_json_body(self, response):
        """Mọi response lỗi đều phải là JSON (dict) không rỗng mô tả nguyên nhân."""
        body = response.json()
        self.assertIsInstance(body, dict)
        self.assertTrue(len(body) > 0, "Response lỗi phải kèm nội dung JSON mô tả nguyên nhân")
        return body

    def _create_order_in_db(self, total_amount=Decimal('0'), item_quantity=0):
        """Tạo trực tiếp một đơn hàng (và tùy chọn 1 mặt hàng) trong database để kiểm thử."""
        order = Order.objects.create(
            customer_name="Trần Thị B",
            customer_email="b@example.com",
            total_amount=total_amount,
            status="pending",
        )
        if item_quantity:
            OrderItem.objects.create(
                order=order,
                product_id=1,
                product_name="Laptop Dell",
                quantity=item_quantity,
                unit_price=self.PRODUCT_PRICE,
                total_price=self.PRODUCT_PRICE * item_quantity,
            )
        return order

    # ------------------------------------------------------------------
    # 1-2. Middleware & xác thực qua Service 1
    # ------------------------------------------------------------------

    def test_01_get_orders_without_token_returns_401(self):
        """Middleware chặn GET /orders và /order_items khi không có token -> 401 Unauthorized"""
        for path in ('/orders', '/order_items'):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
                body = self._assert_json_body(response)
                self.assertTrue(
                    any(k in body for k in ('error', 'detail', 'message')),
                    "Response 401 phải chứa khóa error/detail/message: %s" % body,
                )

    @patch('orders.middleware.requests.get')
    def test_02_get_orders_with_valid_token_returns_200(self, mock_auth_get):
        """GET /orders kèm token được Service 1 xác nhận -> 200 OK + danh sách đơn hàng"""
        mock_auth_get.side_effect = self._fake_http_get
        self._create_order_in_db()
        Order.objects.create(customer_name="Nguyễn Văn A", customer_email="a@example.com")

        response = self.client.get('/orders', **self.auth_header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = response.content.decode('utf-8')
        self.assertIn('Trần Thị B', content)
        self.assertIn('Nguyễn Văn A', content)

        # Token bị Service 1 từ chối (auth trả 401) -> middleware cũng phải chặn 401
        self.auth_status_code = 401
        response_rejected = self.client.get('/orders', **self.auth_header)
        self.assertEqual(response_rejected.status_code, status.HTTP_401_UNAUTHORIZED)

    # ------------------------------------------------------------------
    # 3-6. POST /orders — tạo đơn hàng có kiểm tra tồn kho qua Service 2
    # ------------------------------------------------------------------

    @patch('orders.services.requests.get')
    @patch('orders.middleware.requests.get')
    def test_03_create_order_with_items_success(self, mock_auth_get, mock_product_get):
        """POST /orders tạo đơn 2 mặt hàng -> 201, total_amount = Σ(quantity x unit_price), snapshot đúng sản phẩm"""
        mock_auth_get.side_effect = self._fake_http_get
        mock_product_get.side_effect = self._fake_http_get

        payload = {
            "customer_name": "Nguyễn Văn An",
            "customer_email": "an@example.com",
            "items": [
                {"product_id": 1, "quantity": 2},
                {"product_id": 1, "quantity": 1},
            ],
        }
        response = self.client.post('/orders', payload, format='json', **self.auth_header)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        order_data = self._order_from_response(response.data)
        self.assertEqual(self._as_decimal(order_data['total_amount']), Decimal('45000000.00'))

        # Kiểm tra database: 1 đơn hàng mới ở trạng thái pending
        self.assertEqual(Order.objects.count(), 1)
        order = Order.objects.first()
        self.assertEqual(order.customer_name, 'Nguyễn Văn An')
        self.assertEqual(order.status, 'pending')
        self.assertEqual(order.total_amount, Decimal('45000000.00'))
        self.assertEqual(OrderItem.objects.count(), 2)

        # Snapshot mặt hàng: lưu tên & đơn giá tại thời điểm đặt hàng
        item_2 = OrderItem.objects.get(quantity=2)
        self.assertEqual(item_2.order_id, order.id)
        self.assertEqual(item_2.product_id, 1)
        self.assertEqual(item_2.product_name, 'Laptop Dell')
        self.assertEqual(item_2.unit_price, self.PRODUCT_PRICE)
        self.assertEqual(item_2.total_price, Decimal('30000000.00'))
        item_1 = OrderItem.objects.get(quantity=1)
        self.assertEqual(item_1.total_price, Decimal('15000000.00'))

        # Thiếu customer_name -> 400 và KHÔNG tạo thêm đơn mới nào
        response_missing = self.client.post(
            '/orders',
            {"customer_email": "an@example.com", "items": [{"product_id": 1, "quantity": 1}]},
            format='json', **self.auth_header,
        )
        self.assertEqual(response_missing.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Order.objects.count(), 1)

    @patch('orders.services.requests.get')
    @patch('orders.middleware.requests.get')
    def test_04_create_order_insufficient_stock_returns_400(self, mock_auth_get, mock_product_get):
        """POST /orders với số lượng vượt tồn kho của Service 2 (15 > 10) -> 400, không tạo đơn"""
        mock_auth_get.side_effect = self._fake_http_get
        mock_product_get.side_effect = self._fake_http_get

        payload = {
            "customer_name": "Lê Văn C",
            "customer_email": "c@example.com",
            "items": [{"product_id": 1, "quantity": self.PRODUCT_STOCK + 5}],
        }
        response = self.client.post('/orders', payload, format='json', **self.auth_header)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self._assert_json_body(response)
        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(OrderItem.objects.count(), 0)

    @patch('orders.services.requests.get')
    @patch('orders.middleware.requests.get')
    def test_05_create_order_product_not_found_returns_400(self, mock_auth_get, mock_product_get):
        """POST /orders với sản phẩm không tồn tại (Service 2 trả 404) -> 400, không tạo đơn"""
        mock_auth_get.side_effect = self._fake_http_get
        mock_product_get.side_effect = self._fake_http_get
        self.product_status_code = 404  # Service 2 báo không thấy sản phẩm

        payload = {
            "customer_name": "Lê Văn C",
            "customer_email": "c@example.com",
            "items": [{"product_id": 999, "quantity": 1}],
        }
        response = self.client.post('/orders', payload, format='json', **self.auth_header)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self._assert_json_body(response)
        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(OrderItem.objects.count(), 0)

    @patch('orders.services.requests.get')
    @patch('orders.middleware.requests.get')
    def test_06_create_order_product_service_down_returns_503(self, mock_auth_get, mock_product_get):
        """POST /orders khi Service sản phẩm bị tắt (lỗi mạng) -> 503 Service Unavailable"""
        mock_auth_get.side_effect = self._fake_http_get
        mock_product_get.side_effect = self._fake_http_get
        self.product_exception = requests.exceptions.RequestException("connection refused")

        payload = {
            "customer_name": "Lê Văn C",
            "customer_email": "c@example.com",
            "items": [{"product_id": 1, "quantity": 1}],
        }
        response = self.client.post('/orders', payload, format='json', **self.auth_header)

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self._assert_json_body(response)
        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(OrderItem.objects.count(), 0)

    # ------------------------------------------------------------------
    # 7-9. GET/PUT/DELETE /orders
    # ------------------------------------------------------------------

    @patch('orders.services.requests.get')
    @patch('orders.middleware.requests.get')
    def test_07_get_order_detail_returns_nested_items(self, mock_auth_get, mock_product_get):
        """GET /orders/id trả chi tiết đơn kèm danh sách items lồng nhau; id không tồn tại -> 404"""
        mock_auth_get.side_effect = self._fake_http_get
        mock_product_get.side_effect = self._fake_http_get

        payload = {
            "customer_name": "Nguyễn Văn An",
            "customer_email": "an@example.com",
            "items": [{"product_id": 1, "quantity": 2}],
        }
        created = self.client.post('/orders', payload, format='json', **self.auth_header)
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        order_id = self._order_from_response(created.data)['id']

        response = self.client.get('/orders/%d' % order_id, **self.auth_header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['customer_name'], 'Nguyễn Văn An')
        self.assertIn('items', response.data)
        items = response.data['items']
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['product_name'], 'Laptop Dell')
        self.assertEqual(items[0]['quantity'], 2)

        # Đơn hàng / mặt hàng không tồn tại -> 404 Not Found
        response_order_404 = self.client.get('/orders/99999', **self.auth_header)
        self.assertEqual(response_order_404.status_code, status.HTTP_404_NOT_FOUND)
        response_item_404 = self.client.get('/order_items/99999', **self.auth_header)
        self.assertEqual(response_item_404.status_code, status.HTTP_404_NOT_FOUND)

    @patch('orders.middleware.requests.get')
    def test_08_update_order_status(self, mock_auth_get):
        """PUT /orders/id cập nhật trạng thái: hợp lệ -> 200, trạng thái sai -> 400, đơn không tồn tại -> 404"""
        mock_auth_get.side_effect = self._fake_http_get
        order = self._create_order_in_db()

        # 1. Cập nhật hợp lệ pending -> completed
        response = self.client.put(
            '/orders/%d' % order.id, {"status": "completed"}, format='json', **self.auth_header
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        order.refresh_from_db()
        self.assertEqual(order.status, 'completed')

        # 2. Trạng thái nằm ngoài choices (pending/completed/cancelled) -> 400
        response_invalid = self.client.put(
            '/orders/%d' % order.id, {"status": "shipping"}, format='json', **self.auth_header
        )
        self.assertEqual(response_invalid.status_code, status.HTTP_400_BAD_REQUEST)
        self._assert_json_body(response_invalid)
        order.refresh_from_db()
        self.assertEqual(order.status, 'completed')  # giữ nguyên giá trị cũ khi dữ liệu sai

        # 3. Đơn không tồn tại -> 404
        response_not_found = self.client.put(
            '/orders/99999', {"status": "cancelled"}, format='json', **self.auth_header
        )
        self.assertEqual(response_not_found.status_code, status.HTTP_404_NOT_FOUND)

    @patch('orders.middleware.requests.get')
    def test_09_delete_order_returns_204(self, mock_auth_get):
        """DELETE /orders/id xóa đơn hàng -> 204 No Content; xóa lần nữa -> 404"""
        mock_auth_get.side_effect = self._fake_http_get
        order = self._create_order_in_db(item_quantity=2)
        self.assertEqual(Order.objects.count(), 1)

        response = self.client.delete('/orders/%d' % order.id, **self.auth_header)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Order.objects.count(), 0)

        response_again = self.client.delete('/orders/%d' % order.id, **self.auth_header)
        self.assertEqual(response_again.status_code, status.HTTP_404_NOT_FOUND)

    # ------------------------------------------------------------------
    # 10-12. CRUD /order_items — tính lại tổng tiền đơn hàng
    # ------------------------------------------------------------------

    @patch('orders.services.requests.get')
    @patch('orders.middleware.requests.get')
    def test_10_add_order_item_updates_order_total(self, mock_auth_get, mock_product_get):
        """POST /order_items thêm mặt hàng vào đơn -> 201, đơn hàng có snapshot và tổng tiền tăng đúng"""
        mock_auth_get.side_effect = self._fake_http_get
        mock_product_get.side_effect = self._fake_http_get

        order = self._create_order_in_db()  # đơn rỗng, total_amount = 0
        payload = {"order_id": order.id, "product_id": 1, "quantity": 3}
        response = self.client.post('/order_items', payload, format='json', **self.auth_header)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(OrderItem.objects.count(), 1)
        item = OrderItem.objects.first()
        self.assertEqual(item.order_id, order.id)
        self.assertEqual(item.product_name, 'Laptop Dell')
        self.assertEqual(item.unit_price, self.PRODUCT_PRICE)
        self.assertEqual(item.total_price, Decimal('45000000.00'))

        # Tổng tiền đơn hàng phải được cộng dồn sau khi thêm mặt hàng
        order.refresh_from_db()
        self.assertEqual(order.total_amount, Decimal('45000000.00'))

        # Thêm mặt hàng vào đơn KHÔNG tồn tại -> 400
        response_bad = self.client.post(
            '/order_items', {"order_id": 99999, "product_id": 1, "quantity": 1},
            format='json', **self.auth_header,
        )
        self.assertEqual(response_bad.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(OrderItem.objects.count(), 1)

    @patch('orders.services.requests.get')
    @patch('orders.middleware.requests.get')
    def test_11_update_order_item_recomputes_totals(self, mock_auth_get, mock_product_get):
        """PUT /order_items/id đổi quantity -> 200, tính lại total_price của item và total_amount của đơn"""
        mock_auth_get.side_effect = self._fake_http_get
        mock_product_get.side_effect = self._fake_http_get

        order = self._create_order_in_db(
            total_amount=Decimal('30000000.00'), item_quantity=2
        )
        item = order.items.first()
        self.assertEqual(item.total_price, Decimal('30000000.00'))

        response = self.client.put(
            '/order_items/%d' % item.id, {"quantity": 4}, format='json', **self.auth_header
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        item.refresh_from_db()
        self.assertEqual(item.quantity, 4)
        self.assertEqual(item.total_price, Decimal('60000000.00'))
        order.refresh_from_db()
        self.assertEqual(order.total_amount, Decimal('60000000.00'))

        # Mặt hàng không tồn tại -> 404
        response_not_found = self.client.put(
            '/order_items/99999', {"quantity": 5}, format='json', **self.auth_header
        )
        self.assertEqual(response_not_found.status_code, status.HTTP_404_NOT_FOUND)

    @patch('orders.middleware.requests.get')
    def test_12_delete_order_item_recomputes_total(self, mock_auth_get):
        """DELETE /order_items/id xóa mặt hàng -> 204 và tổng tiền đơn được tính lại (về 0 khi hết item)"""
        mock_auth_get.side_effect = self._fake_http_get
        order = self._create_order_in_db(
            total_amount=Decimal('30000000.00'), item_quantity=2
        )
        item = order.items.first()

        response = self.client.delete('/order_items/%d' % item.id, **self.auth_header)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(OrderItem.objects.count(), 0)

        # Xóa mặt hàng cuối cùng -> tổng tiền đơn hàng về 0
        order.refresh_from_db()
        self.assertEqual(order.total_amount, Decimal('0'))
