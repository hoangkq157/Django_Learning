"""
Bộ kiểm thử tự động cho Service Báo cáo (Bài thực hành số 5).

Đặc biệt: toàn bộ 12 test KHÔNG yêu cầu chạy thật bất kỳ server nào
(8000 / 8001 / 8002 / 8003). Các lời gọi HTTP service-to-service được giả lập
(mock) bằng `unittest.mock`:
  - `reports.middleware` -> gọi `GET http://localhost:8000/auth` (xác thực JWT qua Service 1)
  - `reports.services`   -> gọi `GET http://localhost:8002/orders/<id>` (dữ liệu đơn hàng qua Service 3)
                            và `GET http://localhost:8001/products/<id>` (kiểm tra sản phẩm qua Service 2)

Cả hai module đều `import requests` nên mỗi module giữ đối tượng riêng;
mỗi test gắn cho mock một `side_effect` điều hướng theo URL — dù lời gọi
`requests.get` phát ra từ middleware hay từ services, mock đều trả về
phản hồi đúng cho service tương ứng.

Chạy bộ test (trong thư mục `report_service`, không cần bật server):
    python manage.py test
"""
import re
from decimal import Decimal
from unittest.mock import patch, Mock

import requests
from rest_framework import status
from rest_framework.test import APITestCase

from reports.models import OrderReport, ProductReport


class ReportServiceTestCase(APITestCase):
    """Bộ 12 bài kiểm thử tự động cho /reports/orders và /reports/products (Service 4)."""

    def setUp(self):
        # Token giả lập — middleware đã được mock nên không cần JWT thật
        self.auth_header = {'HTTP_AUTHORIZATION': 'Bearer fake.jwt.token-for-testing'}

        # Dữ liệu đơn hàng mẫu (Service 3 trả về cho GET /orders/3):
        # total_amount = 73200000.00 gồm 2 Laptop Dell XPS 15 (70000000.00)
        # và 1 Bàn phím Keychron K2 (3200000.00)
        self.order_data = {
            "id": 3,
            "customer_name": "Le Van C",
            "customer_email": "l@e.com",
            "total_amount": "73200000.00",
            "status": "pending",
            "items": [
                {"id": 5, "order_id": 3, "product_id": 1, "product_name": "Laptop Dell XPS 15",
                 "quantity": 2, "unit_price": "35000000.00", "total_price": "70000000.00"},
                {"id": 6, "order_id": 3, "product_id": 3, "product_name": "Bàn phím Keychron K2",
                 "quantity": 1, "unit_price": "3200000.00", "total_price": "3200000.0"},
            ],
        }

        # Dữ liệu sản phẩm mẫu (Service 2 trả về cho GET /products/<id>)
        self.product_data = {
            "id": 2,
            "name": "Chuột Logitech",
            "description": "Chuột không dây",
            "price": "2500000.00",
            "quantity": 5,
            "created_at": "2026-11-05T10:00:00Z",
            "updated_at": "2026-11-05T10:00:00Z",
        }

        # Trạng thái giả lập của 3 service phụ thuộc (mỗi test tự tinh chỉnh)
        self.auth_status_code = 200      # Service 1: 200 = token hợp lệ
        self.order_status_code = 200     # Service 3: 200 = đơn hàng tồn tại
        self.product_status_code = 200   # Service 2: 200 = sản phẩm tồn tại
        self.order_exception = None      # Ngoại lệ mạng khi Service 3 bị tắt
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
        """Dispatcher điều hướng theo URL: /auth -> Service 1,
        /orders/<id> -> Service 3, /products/<id> -> Service 2."""
        if '/auth' in url:
            return self._mock_response(self.auth_status_code, {
                "valid": self.auth_status_code == 200,
                "user": {"UserName": "testuser"},
            })
        if '/orders/' in url:
            if self.order_exception is not None:
                raise self.order_exception
            return self._mock_response(self.order_status_code, self.order_data)
        if '/products/' in url:
            if self.product_exception is not None:
                raise self.product_exception
            # Gắn id theo URL cho giống Service 2 thật (GET /products/2 -> {"id": 2, ...})
            product_id = int(re.search(r'/products/(\d+)', url).group(1))
            return self._mock_response(
                self.product_status_code, dict(self.product_data, id=product_id))
        raise AssertionError(
            "Test chỉ mong đợi lời gọi tới /auth, /orders/<id> hoặc /products/<id>, nhận: %s" % url
        )

    @staticmethod
    def _as_decimal(value):
        """Ép kiểu an toàn: '73200000.00' (str) hoặc 73200000.0 (float) -> Decimal."""
        return Decimal(str(value))

    @staticmethod
    def _report_from_response(response_data):
        """Trích dữ liệu báo cáo từ response tạo mới.

        View trả về {"message": ..., "report": {...}}; helper này chịu được
        cả dạng response phẳng (báo cáo nằm ngay cấp gốc) cho đỡ phụ thuộc
        vào cách gói response của view.
        """
        return response_data.get('report', response_data)

    def _assert_json_body(self, response):
        """Mọi response lỗi đều phải là JSON (dict) không rỗng mô tả nguyên nhân."""
        body = response.json()
        self.assertIsInstance(body, dict)
        self.assertTrue(len(body) > 0, "Response lỗi phải kèm nội dung JSON mô tả nguyên nhân")
        return body

    @staticmethod
    def _find_product_report(product_reports, product_id):
        """Tìm báo cáo sản phẩm của một product_id trong response lồng nhau."""
        for item in product_reports:
            if item['product_id'] == product_id:
                return item
        raise AssertionError(
            "Không tìm thấy báo cáo sản phẩm cho product_id=%s trong: %s"
            % (product_id, product_reports)
        )

    def _create_order_report_in_db(self, order_id=3, product_ids=(1, 3)):
        """Tạo trực tiếp một báo cáo đơn hàng (và các báo cáo sản phẩm) trong DB để kiểm thử."""
        report = OrderReport.objects.create(
            order_id=order_id,
            total_revenue=Decimal('73200000.00'),
            total_cost=Decimal('51240000.00'),
            total_profit=Decimal('21960000.00'),
        )
        # Số liệu khớp cost_rate 0.7 của đơn hàng mẫu #3
        samples = {
            1: (2, Decimal('70000000.00'), Decimal('49000000.00'), Decimal('21000000.00')),
            3: (1, Decimal('3200000.00'), Decimal('2240000.00'), Decimal('960000.00')),
        }
        for pid in product_ids:
            total_sold, revenue, cost, profit = samples[pid]
            ProductReport.objects.create(
                order_report=report,
                product_id=pid,
                total_sold=total_sold,
                revenue=revenue,
                cost=cost,
                profit=profit,
            )
        return report

    # ------------------------------------------------------------------
    # 1-2. Middleware & xác thực qua Service 1
    # ------------------------------------------------------------------

    def test_01_get_reports_without_token_returns_401(self):
        """Middleware chặn GET /reports/orders và /reports/products khi không có token -> 401 Unauthorized"""
        for path in ('/reports/orders', '/reports/products'):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
                body = self._assert_json_body(response)
                self.assertTrue(
                    any(k in body for k in ('error', 'detail', 'message')),
                    "Response 401 phải chứa khóa error/detail/message: %s" % body,
                )

    @patch('reports.middleware.requests.get')
    def test_02_get_reports_with_valid_token_returns_200(self, mock_auth_get):
        """GET /reports/orders và /reports/products kèm token hợp lệ -> 200 OK; detail trả product_reports lồng nhau"""
        mock_auth_get.side_effect = self._fake_http_get
        report = self._create_order_report_in_db()

        # GET /reports/orders -> danh sách phẳng (không lồng product_reports)
        response = self.client.get('/reports/orders', **self.auth_header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['order_id'], 3)
        self.assertEqual(self._as_decimal(response.data[0]['total_profit']), Decimal('21960000.00'))
        self.assertNotIn('product_reports', response.data[0])

        # GET /reports/orders/id -> chi tiết kèm danh sách product_reports lồng nhau
        response_detail = self.client.get('/reports/orders/%d' % report.id, **self.auth_header)
        self.assertEqual(response_detail.status_code, status.HTTP_200_OK)
        self.assertIn('product_reports', response_detail.data)
        nested = response_detail.data['product_reports']
        self.assertEqual(len(nested), 2)
        laptop = self._find_product_report(nested, 1)
        self.assertEqual(laptop['total_sold'], 2)
        self.assertEqual(self._as_decimal(laptop['revenue']), Decimal('70000000.00'))

        # GET /reports/products -> danh sách 2 báo cáo sản phẩm; detail -> 200
        response_products = self.client.get('/reports/products', **self.auth_header)
        self.assertEqual(response_products.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_products.data), 2)
        product_report = ProductReport.objects.get(product_id=3)
        response_product_detail = self.client.get(
            '/reports/products/%d' % product_report.id, **self.auth_header)
        self.assertEqual(response_product_detail.status_code, status.HTTP_200_OK)
        self.assertEqual(response_product_detail.data['product_id'], 3)

        # Báo cáo với id không tồn tại -> 404 Not Found
        self.assertEqual(
            self.client.get('/reports/orders/99999', **self.auth_header).status_code,
            status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            self.client.get('/reports/products/99999', **self.auth_header).status_code,
            status.HTTP_404_NOT_FOUND)

        # Token bị Service 1 từ chối (auth trả 401) -> middleware cũng phải chặn 401
        self.auth_status_code = 401
        response_rejected = self.client.get('/reports/orders', **self.auth_header)
        self.assertEqual(response_rejected.status_code, status.HTTP_401_UNAUTHORIZED)

    # ------------------------------------------------------------------
    # 3-7. POST /reports/orders — tổng hợp báo cáo từ Service 3
    # ------------------------------------------------------------------

    @patch('reports.services.requests.get')
    @patch('reports.middleware.requests.get')
    def test_03_create_order_report_success(self, mock_auth_get, mock_order_get):
        """POST /reports/orders (cost_rate mặc định 0.7) -> 201; revenue/cost/profit đúng; tự sinh ProductReport cho từng item"""
        mock_auth_get.side_effect = self._fake_http_get
        mock_order_get.side_effect = self._fake_http_get

        response = self.client.post('/reports/orders', {"order_id": 3},
                                    format='json', **self.auth_header)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('message', response.data)
        report = self._report_from_response(response.data)
        self.assertEqual(report['order_id'], 3)
        # total_revenue = total_amount của đơn; total_cost = 73200000 x 0.7 = 51240000
        self.assertEqual(self._as_decimal(report['total_revenue']), Decimal('73200000.00'))
        self.assertEqual(self._as_decimal(report['total_cost']), Decimal('51240000.00'))
        self.assertEqual(self._as_decimal(report['total_profit']), Decimal('21960000.00'))

        # 2 ProductReport được sinh ra cho 2 dòng hàng, số liệu đúng contract
        product_reports = report['product_reports']
        self.assertEqual(len(product_reports), 2)
        laptop = self._find_product_report(product_reports, 1)
        self.assertEqual(laptop['total_sold'], 2)
        self.assertEqual(self._as_decimal(laptop['revenue']), Decimal('70000000.00'))
        self.assertEqual(self._as_decimal(laptop['cost']), Decimal('49000000.00'))
        self.assertEqual(self._as_decimal(laptop['profit']), Decimal('21000000.00'))
        keyboard = self._find_product_report(product_reports, 3)
        self.assertEqual(keyboard['total_sold'], 1)
        self.assertEqual(self._as_decimal(keyboard['revenue']), Decimal('3200000.00'))
        self.assertEqual(self._as_decimal(keyboard['cost']), Decimal('2240000.00'))
        self.assertEqual(self._as_decimal(keyboard['profit']), Decimal('960000.00'))

        # Kiểm tra database: 1 báo cáo đơn + 2 báo cáo sản phẩm
        self.assertEqual(OrderReport.objects.count(), 1)
        self.assertEqual(ProductReport.objects.count(), 2)
        saved = OrderReport.objects.first()
        self.assertEqual(saved.order_id, 3)
        self.assertEqual(saved.total_revenue, Decimal('73200000.00'))
        self.assertEqual(saved.total_cost, Decimal('51240000.00'))
        self.assertEqual(saved.total_profit, Decimal('21960000.00'))

    @patch('reports.services.requests.get')
    @patch('reports.middleware.requests.get')
    def test_04_create_order_report_custom_cost_rate(self, mock_auth_get, mock_order_get):
        """POST /reports/orders với cost_rate=0.5 -> 201; tính lại chi phí/lợi nhuận theo tỷ lệ tùy chọn"""
        mock_auth_get.side_effect = self._fake_http_get
        mock_order_get.side_effect = self._fake_http_get

        response = self.client.post('/reports/orders',
                                    {"order_id": 3, "cost_rate": 0.5},
                                    format='json', **self.auth_header)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        report = self._report_from_response(response.data)
        # 73200000 x 0.5 = 36600000 -> lợi nhuận = doanh thu - chi phí = 36600000
        self.assertEqual(self._as_decimal(report['total_revenue']), Decimal('73200000.00'))
        self.assertEqual(self._as_decimal(report['total_cost']), Decimal('36600000.00'))
        self.assertEqual(self._as_decimal(report['total_profit']), Decimal('36600000.00'))

        laptop = self._find_product_report(report['product_reports'], 1)
        self.assertEqual(self._as_decimal(laptop['cost']), Decimal('35000000.00'))
        self.assertEqual(self._as_decimal(laptop['profit']), Decimal('35000000.00'))
        keyboard = self._find_product_report(report['product_reports'], 3)
        self.assertEqual(self._as_decimal(keyboard['cost']), Decimal('1600000.00'))
        self.assertEqual(self._as_decimal(keyboard['profit']), Decimal('1600000.00'))

    @patch('reports.services.requests.get')
    @patch('reports.middleware.requests.get')
    def test_05_create_order_report_invalid_cost_rate(self, mock_auth_get, mock_order_get):
        """POST /reports/orders với cost_rate ngoài [0, 1] (1.5 và -1) -> 400, không tạo báo cáo"""
        mock_auth_get.side_effect = self._fake_http_get
        mock_order_get.side_effect = self._fake_http_get

        for bad_rate in (1.5, -1):
            with self.subTest(cost_rate=bad_rate):
                response = self.client.post('/reports/orders',
                                            {"order_id": 3, "cost_rate": bad_rate},
                                            format='json', **self.auth_header)
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self._assert_json_body(response)
                self.assertEqual(OrderReport.objects.count(), 0)
                self.assertEqual(ProductReport.objects.count(), 0)

    @patch('reports.services.requests.get')
    @patch('reports.middleware.requests.get')
    def test_06_create_order_report_order_not_found(self, mock_auth_get, mock_order_get):
        """POST /reports/orders khi Service 3 trả 404 (đơn không tồn tại) -> 404, không tạo báo cáo"""
        mock_auth_get.side_effect = self._fake_http_get
        mock_order_get.side_effect = self._fake_http_get
        self.order_status_code = 404  # Service 3 báo không thấy đơn hàng

        response = self.client.post('/reports/orders', {"order_id": 999},
                                    format='json', **self.auth_header)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self._assert_json_body(response)
        self.assertEqual(OrderReport.objects.count(), 0)
        self.assertEqual(ProductReport.objects.count(), 0)

    @patch('reports.services.requests.get')
    @patch('reports.middleware.requests.get')
    def test_07_create_order_report_order_service_down(self, mock_auth_get, mock_order_get):
        """POST /reports/orders khi Service đơn hàng bị tắt (lỗi mạng) -> 503 Service Unavailable"""
        mock_auth_get.side_effect = self._fake_http_get
        mock_order_get.side_effect = self._fake_http_get
        self.order_exception = requests.exceptions.RequestException("connection refused")

        response = self.client.post('/reports/orders', {"order_id": 3},
                                    format='json', **self.auth_header)

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self._assert_json_body(response)
        self.assertEqual(OrderReport.objects.count(), 0)
        self.assertEqual(ProductReport.objects.count(), 0)

    # ------------------------------------------------------------------
    # 8. DELETE /reports/orders — cascade báo cáo sản phẩm
    # ------------------------------------------------------------------

    @patch('reports.middleware.requests.get')
    def test_08_delete_order_report_cascades(self, mock_auth_get):
        """DELETE /reports/orders/id -> 204 No Content; các product_reports con bị xóa theo (CASCADE)"""
        mock_auth_get.side_effect = self._fake_http_get
        report = self._create_order_report_in_db()
        self.assertEqual(OrderReport.objects.count(), 1)
        self.assertEqual(ProductReport.objects.count(), 2)

        response = self.client.delete('/reports/orders/%d' % report.id, **self.auth_header)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(OrderReport.objects.count(), 0)
        self.assertEqual(ProductReport.objects.count(), 0)  # cascade theo FK

        # Xóa lần nữa -> 404 Not Found
        response_again = self.client.delete('/reports/orders/%d' % report.id, **self.auth_header)
        self.assertEqual(response_again.status_code, status.HTTP_404_NOT_FOUND)

    # ------------------------------------------------------------------
    # 9-12. POST/DELETE /reports/products — tổng hợp từ Service 2 + Service 3
    # ------------------------------------------------------------------

    @patch('reports.services.requests.get')
    @patch('reports.middleware.requests.get')
    def test_09_create_product_report_success(self, mock_auth_get, mock_service_get):
        """POST /reports/products (product_id=3 có trong đơn 3, unit_cost=2500000) -> 201, profit đúng"""
        mock_auth_get.side_effect = self._fake_http_get
        mock_service_get.side_effect = self._fake_http_get
        report = self._create_order_report_in_db(product_ids=())  # báo cáo đơn chưa có sản phẩm

        payload = {"order_report_id": report.id, "product_id": 3, "unit_cost": 2500000}
        response = self.client.post('/reports/products', payload,
                                    format='json', **self.auth_header)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('message', response.data)
        product_report = self._report_from_response(response.data)
        self.assertEqual(product_report['order_report_id'], report.id)
        self.assertEqual(product_report['product_id'], 3)
        # Đơn 3 có 1 Bàn phím (3200000.00): sold=1, cost=2500000x1, profit=700000
        self.assertEqual(product_report['total_sold'], 1)
        self.assertEqual(self._as_decimal(product_report['revenue']), Decimal('3200000.00'))
        self.assertEqual(self._as_decimal(product_report['cost']), Decimal('2500000.00'))
        self.assertEqual(self._as_decimal(product_report['profit']), Decimal('700000.00'))

        self.assertEqual(ProductReport.objects.count(), 1)
        saved = ProductReport.objects.first()
        self.assertEqual(saved.order_report_id, report.id)
        self.assertEqual(saved.total_sold, 1)
        self.assertEqual(saved.profit, Decimal('700000.00'))

    @patch('reports.services.requests.get')
    @patch('reports.middleware.requests.get')
    def test_10_create_product_report_order_report_missing(self, mock_auth_get, mock_service_get):
        """POST /reports/products với order_report_id không có trong DB -> 400, không tạo báo cáo"""
        mock_auth_get.side_effect = self._fake_http_get
        mock_service_get.side_effect = self._fake_http_get

        payload = {"order_report_id": 99999, "product_id": 3, "unit_cost": 2500000}
        response = self.client.post('/reports/products', payload,
                                    format='json', **self.auth_header)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self._assert_json_body(response)
        self.assertEqual(ProductReport.objects.count(), 0)

    @patch('reports.services.requests.get')
    @patch('reports.middleware.requests.get')
    def test_11_create_product_report_not_in_order(self, mock_auth_get, mock_service_get):
        """POST /reports/products: product không có item nào trong đơn -> 400; Service 2 trả 404 -> 400"""
        mock_auth_get.side_effect = self._fake_http_get
        mock_service_get.side_effect = self._fake_http_get
        report = self._create_order_report_in_db(product_ids=())

        # 1. Sản phẩm không xuất hiện trong đơn hàng #3 (đơn chỉ có product 1 và 3) -> 400
        payload = {"order_report_id": report.id, "product_id": 2, "unit_cost": 2500000}
        response = self.client.post('/reports/products', payload,
                                    format='json', **self.auth_header)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self._assert_json_body(response)

        # 2. Service quản lý sản phẩm trả 404 (sản phẩm không tồn tại) -> 400
        self.product_status_code = 404
        payload_not_found = {"order_report_id": report.id, "product_id": 999, "unit_cost": 2500000}
        response_not_found = self.client.post('/reports/products', payload_not_found,
                                              format='json', **self.auth_header)
        self.assertEqual(response_not_found.status_code, status.HTTP_400_BAD_REQUEST)
        self._assert_json_body(response_not_found)

        self.assertEqual(ProductReport.objects.count(), 0)

    @patch('reports.middleware.requests.get')
    def test_12_delete_product_report_returns_204(self, mock_auth_get):
        """DELETE /reports/products/id -> 204 No Content (báo cáo đơn vẫn còn); xóa lần nữa -> 404"""
        mock_auth_get.side_effect = self._fake_http_get
        report = self._create_order_report_in_db(product_ids=(1,))
        product_report = ProductReport.objects.get(order_report=report, product_id=1)

        response = self.client.delete('/reports/products/%d' % product_report.id,
                                      **self.auth_header)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(ProductReport.objects.count(), 0)
        # Báo cáo đơn hàng KHÔNG bị xóa theo (chỉ có con -> cha)
        self.assertEqual(OrderReport.objects.count(), 1)

        response_again = self.client.delete('/reports/products/%d' % product_report.id,
                                            **self.auth_header)
        self.assertEqual(response_again.status_code, status.HTTP_404_NOT_FOUND)
