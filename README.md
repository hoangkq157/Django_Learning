# 🚀 BÁO CÁO & HƯỚNG DẪN DỰ ÁN DJANGO RESTFUL API
## Học phần: Phát triển Dịch vụ Web / RESTful API
> **Bài Thực Hành Số 1:** Cài đặt và cấu hình môi trường xây dựng API ("Hello World")  
> **Bài Thực Hành Số 2:** Router, Middleware và Bảo mật với JWT trong RESTful API  
> **Bài Thực Hành Số 3:** Xây dựng dịch vụ Quản lý Sản phẩm độc lập theo kiến trúc SOA  
> **Bài Thực Hành Số 4:** Xây dựng dịch vụ Quản lý Đơn hàng với kiểm tra tồn kho liên service  

---

## 📑 MỤC LỤC

1. [Tổng quan dự án](#1-tổng-quan-dự-án)
2. [Yêu cầu đề bài & Bảng đối soát hoàn thành](#2-yêu-cầu-đề-bài--bảng-đối-soát-hoàn-thành)
3. [Kiến trúc hệ thống & Luồng xử lý (Workflow)](#3-kiến-trúc-hệ-thống--luồng-xử-lý-workflow)
4. [Cấu trúc cơ sở dữ liệu (Database Schema)](#4-cấu-trúc-cơ-sở-dữ-liệu-database-schema)
5. [Cấu trúc thư mục mã nguồn](#5-cấu-trúc-thư-mục-mã-nguồn)
6. [Yêu cầu môi trường & Công nghệ sử dụng](#6-yêu-cầu-môi-trường--công-nghệ-sử-dụng)
7. [Hướng dẫn cài đặt & Khởi chạy từ A-Z](#7-hướng-dẫn-cài-đặt--khởi-chạy-từ-a-z)
8. [Tài liệu API chi tiết (API Documentation)](#8-tài-liệu-api-chi-tiết-api-documentation)
9. [Hướng dẫn kiểm thử với Postman & Swagger UI](#9-hướng-dẫn-kiểm-thử-với-postman--swagger-ui)
10. [Kiểm thử tự động (Automated Unit Tests)](#10-kiểm-thử-tự-động-automated-unit-tests)
11. [Xử lý sự cố thường gặp (Troubleshooting)](#11-xử-lý-sự-cố-thường-gặp-troubleshooting)

---

## 1. TỔNG QUAN DỰ ÁN

Dự án này là chuỗi thực hành hoàn chỉnh nhằm xây dựng dịch vụ **RESTful API chuẩn hóa** sử dụng ngôn ngữ **Python** và nền tảng **Django / Django REST Framework (DRF)**.

Dự án tích hợp đầy đủ nội dung của 4 bài thực hành:
- **Bài thực hành số 1:** Thiết lập môi trường Python/Django, cài đặt REST Framework, xây dựng API đầu tiên in dòng chuỗi JSON `{"message": "hello-world"}` và kiểm thử qua Postman / Swagger.
- **Bài thực hành số 2:** Mở rộng hệ thống với:
  - Cơ chế định tuyến linh hoạt (**Router & URL Rewrite**).
  - Lớp lọc trung gian (**Custom Middleware**) để kiểm soát truy cập và xác thực token.
  - Cơ chế phân quyền và bảo mật qua **JSON Web Token (JWT)** với thuật toán HMAC-SHA256 (`HS256`).
  - Hỗ trợ giải mã mật khẩu truyền từ Client dưới dạng **Base64** hoặc mã băm **MD5**.
  - Tích hợp tài liệu tương tác tự động **Swagger UI (OpenAPI 3.0)**.
- **Bài thực hành số 3:** Xây dựng **Service Quản lý Sản phẩm** hoạt động độc lập theo nguyên tắc SOA:
  - Project Django thứ hai `product_service` chạy trên **cổng riêng 8001** với **cơ sở dữ liệu riêng** `db_products.sqlite3`.
  - RESTful API CRUD đầy đủ: `GET /products`, `GET /products/id`, `POST /products`, `PUT /products/id`, `DELETE /products/id`.
  - Xác thực **ủy quyền qua Service 1** (service-to-service): middleware gọi `GET /auth` để kiểm tra JWT; trả `401` khi token thiếu/sai và `503` khi Service xác thực không khả dụng.
- **Bài thực hành số 4:** Xây dựng **Service Quản lý Đơn hàng** — service thứ ba theo kiến trúc SOA:
  - Project Django thứ ba `order_service` chạy trên **cổng riêng 8002** với **cơ sở dữ liệu riêng** `db_orders.sqlite3`.
  - RESTful API CRUD đầy đủ cho đơn hàng (`GET/POST/PUT/DELETE /orders`) và chi tiết đơn hàng (`GET/POST/PUT/DELETE /order_items`).
  - **Kiểm tra tồn kho liên service**: khi tạo đơn/mặt hàng, service gọi `GET /products/id` sang Service quản lý sản phẩm và *snapshot* tên & đơn giá tại thời điểm đặt hàng; tổng tiền (`total_amount`) luôn được tính lại tự động.
  - Xác thực **ủy quyền qua Service 1** (service-to-service): middleware gọi `GET /auth` để kiểm tra JWT, sau đó **forward token** sang Service 2 khi kiểm tra tồn kho.

---

## 2. YÊU CẦU ĐỀ BÀI & BẢNG ĐỐI SOÁT HOÀN THÀNH

### Đối chiếu Bài Thực Hành Số 1:
- [x] Lựa chọn Framework: Python + Django REST Framework.
- [x] Cài đặt môi trường ảo `venv` sạch sẽ, cấu hình project `myapi` và app `core`.
- [x] Xây dựng API in chuỗi `{"message": "hello-world"}` kiểm thử được qua Postman / Swagger.

### Đối chiếu Bài Thực Hành Số 2:
| Yêu cầu trong PDF Bài 2 | Tình trạng | Vị trí triển khai trong Codebase |
| :--- | :---: | :--- |
| **1. Cài đặt thư viện JWT phù hợp** |  **100% Đạt** | Cài đặt `PyJWT 2.14.0`. Triển khai tại `core/utils.py` ([generate_jwt](file:///d:/CODES/Py/Django_Learning/core/utils.py#L9) & [decode_jwt](file:///d:/CODES/Py/Django_Learning/core/utils.py#L26)). |
| **2. Bảng User theo Phụ lục**<br>- `IdUser`: INT (PK)<br>- `UserName`: VARCHAR(255)<br>- `Password`: VARCHAR(255)<br>- `Token`: VARCHAR(255) |  **100% Đạt** | Model `User` tại `core/models.py`. Migration áp dụng tại `core/migrations/0001_initial.py`. Đã đăng ký hiển thị trong Django Admin tại `core/admin.py`. |
| **3. API Đăng nhập tại `localhost:****/`** |  **100% Đạt** | Định tuyến ngay tại gốc `http://localhost:8000/` và `http://localhost:8000/login` trong `myapi/urls.py` và `core/urls.py`. |
| **4. Tham số: userName, password (mã hóa Base64 hoặc MD5 từ client)** |  **100% Đạt** | `LoginSerializer` nhận `userName` (hoặc `username`). Hàm `verify_password` tại `core/utils.py` hỗ trợ giải mã Base64, so khớp băm MD5 và plain text. |
| **5. Kiểm tra tài khoản, sinh JWT & lưu vào cột Token** |  **100% Đạt** | Hàm `login_view` tại `core/views.py` sinh JWT hợp lệ và cập nhật trực tiếp vào thuộc tính `user.Token` trong database. |
| **6. API xác thực token `localhost:****/auth`** |  **100% Đạt** | Endpoint `/auth` tại `core/views.py` hỗ trợ nhận token qua Header `Authorization: Bearer <token>`, POST body `{"token": "..."}`, hoặc query string `?token=...`. |
| **7. Middleware bảo vệ API "Hello World" từ Bài 1** |  **100% Đạt** | `JWTAuthenticationMiddleware` tại `core/middleware.py`, đăng ký trong `settings.py`. Chặn `401 Unauthorized` nếu thiếu hoặc sai token; cho phép `200 OK` nếu token hợp lệ. |
| **8. Kiểm tra qua Postman / Swagger UI** |  **100% Đạt** | Tích hợp thư viện `drf-spectacular` tạo giao diện Swagger UI tại `http://localhost:8000/swagger/` và `http://localhost:8000/docs/`. |

### Đối chiếu Bài Thực Hành Số 3:
| Yêu cầu trong PDF Bài 3 | Tình trạng | Vị trí triển khai trong Codebase |
| :--- | :---: | :--- |
| **1. Service hoạt động độc lập trên một cổng** |  **100% Đạt** | Project Django thứ hai `product_service/` khởi chạy bằng `python manage.py runserver 8001` (đề gợi ý mẫu `localhost:***1/`). |
| **2. Cơ sở dữ liệu riêng (nguyên tắc SOA)** |  **100% Đạt** | File `product_service/db_products.sqlite3` cấu hình tại `product_service/product_service/settings.py` — tách biệt hoàn toàn với `db.sqlite3` của Service đăng nhập. |
| **3. GET /products — danh sách sản phẩm** |  **100% Đạt** | `ProductListCreateView` (ListCreateAPIView) tại `product_service/products/views.py`. |
| **4. POST /products — thêm sản phẩm mới** |  **100% Đạt** | `ProductListCreateView` + kiểm tra dữ liệu bằng `ProductSerializer` tại `product_service/products/serializers.py`. |
| **5. GET/PUT/DELETE /products/id** |  **100% Đạt** | `ProductDetailView` (RetrieveUpdateDestroyAPIView) tại `product_service/products/views.py`. |
| **6. Bảng products theo Phụ lục** |  **100% Đạt** | Model `Product` tại `product_service/products/models.py`: id INT PK, name VARCHAR(255), description TEXT, price DECIMAL(10,2), quantity INT, created_at/updated_at TIMESTAMP. Migration tại `products/migrations/0001_initial.py`. |
| **7. Xác thực qua service đã xây dựng ở Bài 2** |  **100% Đạt** | `AuthServiceMiddleware` tại `product_service/products/middleware.py`: trích Bearer token → gọi HTTP `GET http://localhost:8000/auth` (thư viện `requests`) → cho phép nếu `200`, chặn `401` nếu token thiếu/sai, trả `503` nếu Service xác thực đang tắt. |

### Đối chiếu Bài Thực Hành Số 4:
| Yêu cầu trong PDF Bài 4 | Tình trạng | Vị trí triển khai trong Codebase |
| :--- | :---: | :--- |
| **1. Service hoạt động độc lập trên một cổng** |  **100% Đạt** | Project Django thứ ba `order_service/` khởi chạy bằng `python manage.py runserver 8002` (đề gợi ý mẫu `localhost:***2/`). |
| **2. Cơ sở dữ liệu riêng (nguyên tắc SOA)** |  **100% Đạt** | File `order_service/db_orders.sqlite3` cấu hình tại `order_service/order_service/settings.py` — tách biệt hoàn toàn với `db.sqlite3` (Service 1) và `db_products.sqlite3` (Service 2). |
| **3. GET /orders — danh sách đơn hàng** |  **100% Đạt** | View danh sách (list phẳng) tại `order_service/orders/views.py`, định tuyến `^orders/?$` trong `order_service/order_service/urls.py`. |
| **4. GET /orders/id — chi tiết đơn hàng** |  **100% Đạt** | View chi tiết trả dữ liệu **lồng nhau** (order + `items` của đơn) tại `order_service/orders/views.py` / `serializers.py`. |
| **5. POST /orders — tạo đơn hàng (kiểm tra tồn kho)** |  **100% Đạt** | View tạo đơn tại `order_service/orders/views.py`: với mỗi mặt hàng gọi `ProductServiceClient.get_product()` (tại `order_service/orders/services.py`) sang `GET :8001/products/<id>` — sản phẩm không tồn tại → `400`, tồn kho không đủ → `400`, Service sản phẩm tắt → `503`; lưu *snapshot* `product_name` + `unit_price` và tính `total_amount = Σ(quantity × unit_price)`. |
| **6. PUT /orders/id — cập nhật trạng thái đơn** |  **100% Đạt** | View cập nhật chỉ cho phép status thuộc `pending / completed / cancelled` (choices của model `Order`); giá trị khác → `400`. |
| **7. DELETE /orders/id — xóa đơn hàng** |  **100% Đạt** | View xóa đơn tại `order_service/orders/views.py` → `204 No Content`. |
| **8. GET/POST/PUT/DELETE /order_items — CRUD chi tiết đơn** |  **100% Đạt** | Bộ view + serializer tại `order_service/orders/views.py` / `serializers.py`: thêm mặt hàng → `total_amount` tăng; sửa `quantity` → `total_price` & `total_amount` tính lại; xóa mặt hàng → `total_amount` tính lại. |
| **9. Bảng orders + order_items theo Phụ lục** |  **100% Đạt** | Model `Order` và `OrderItem` tại `order_service/orders/models.py` đủ mọi cột theo Phụ lục. *(Lưu ý: đề ghi tên bảng chi tiết là `other_items` — đây là lỗi đánh máy của đề bài, hệ thống dùng đúng `order_items` theo đúng danh mục API của đề.)* |
| **10. Xác thực qua service đã xây dựng ở Bài 2** |  **100% Đạt** | Middleware tại `order_service/orders/middleware.py`: bảo vệ mọi path `/orders` và `/order_items`; trích Bearer token → gọi HTTP `GET http://localhost:8000/auth` (thư viện `requests`) → cho phép nếu `200`, chặn `401` nếu token thiếu/sai, trả `503` nếu Service xác thực đang tắt. |

---

## 3. KIẾN TRÚC HỆ THỐNG & LUỒNG XỬ LÝ (WORKFLOW)

### 3.1. Sơ đồ luồng xác thực và bảo vệ API
```text
+---------------------------------------------------------------------------------------+
|                                    CLIENT (Browser / Postman / Swagger)               |
+---------------------------------------------------------------------------------------+
       |                                                |
  (1) POST / (Login)                               (2) GET /hello (Có kèm Bearer Token)
  {userName, password (Base64/MD5)}                     |
       |                                                v
       v                                       +----------------------------------------+
+------------------------------------+         |       Django MIDDLEWARE Pipeline       |
|            ROUTER                  |         +----------------------------------------+
| (myapi/urls.py -> core/urls.py)    |                     |
+------------------------------------+                     v
       |                                       +----------------------------------------+
       v                                       |     JWTAuthenticationMiddleware        |
+------------------------------------+         +----------------------------------------+
|             VIEWS                  |                     |
|          login_view                |            [Kiểm tra Token hợp lệ?]
|  - Verify Password (Base64/MD5)    |                     |
|  - Generate JWT Token              |            +--------+--------+
|  - Save Token to User.Token        |            |                 |
+------------------------------------+         (KHÔNG)             (CÓ)
       |                                          |                 |
       v                                          v                 v
+------------------------------------+      +-----------+     +-------------------------+
|           DATABASE                 |      |  HTTP 401 |     |   Chuyển tiếp tới View  |
|    Bảng User (db.sqlite3)          |      |  Từ chối  |     |   hello_world -> 200 OK |
+------------------------------------+      +-----------+     +-------------------------+
```

### 3.2. Cơ chế xử lý mật khẩu Client (`verify_password`)
Nhằm đáp ứng linh hoạt các giao diện Client khác nhau, hệ thống hỗ trợ 3 định dạng mật khẩu:
1. **Base64 Encoding**: Ví dụ `123456` -> Base64: `MTIzNDU2`. Hệ thống tự động giải mã Base64 trước khi so sánh với mã băm trong DB.
2. **MD5 Hashing**: Ví dụ `123456` -> MD5: `e10adc3949ba59abbe56e057f20f883e`. Hệ thống so khớp trực tiếp chuỗi hash 32 ký tự.
3. **Plain Text**: Phục vụ việc kiểm thử nhanh qua cURL hoặc giao diện Swagger.

### 3.3. Kiến trúc 2 service độc lập (Bài 3 — SOA)
```text
+-----------------------------+          +----------------------------------+
|   SERVICE 1: Auth           |          |   SERVICE 2: Product             |
|   localhost:8000            |          |   localhost:8001                 |
|   db.sqlite3 (bảng User)    |          |   db_products.sqlite3 (Product)  |
|                             |          |                                  |
|   POST /login  -> cấp JWT   |<---------|   AuthServiceMiddleware          |
|   GET  /auth   -> valid?    | (3) hỏi  |   với mọi request /products      |
+-----------------------------+          +----------------------------------+
        ^                                          ^
        | (1) đăng nhập                            | (2) CRUD /products
        |                                          |     kèm Bearer token
        v                                          v
+---------------------------------------------------------------------+
|                  CLIENT (Postman / Swagger UI / cURL)                |
+---------------------------------------------------------------------+
```
**Luồng xử lý:**
1. Client đăng nhập tại **Service 1** (`POST /login`) và nhận chuỗi JWT.
2. Client gọi API CRUD `/products` trên **Service 2** kèm Header `Authorization: Bearer <token>`.
3. Middleware của Service 2 **gọi sang Service 1** (`GET /auth`) để kiểm tra token — Service 2 không tự giải mã JWT (tách trách nhiệm xác thực theo đúng nguyên tắc SOA).
4. Token hợp lệ → thực thi nghiệp vụ trên DB riêng của Service 2. Token thiếu/sai → `401`. Service 1 không khả dụng → `503`.

### 3.4. Kiến trúc 3 service độc lập (Bài 4 — SOA)
```text
+-----------------------------+       +----------------------------------+
|   SERVICE 1: Auth           |       |   SERVICE 2: Product             |
|   localhost:8000            |       |   localhost:8001                 |
|   db.sqlite3 (bảng User)    |       |   db_products.sqlite3 (Product)  |
|                             |       |                                  |
|   POST /login  -> cấp JWT   |<------|   GET /auth được Product service |
|   GET  /auth   -> valid?    |       |   gọi khi kiểm tra token         |
+-----------------------------+       +----------------------------------+
        ^      ^                                    ^
        |      |                              (5) hỏi tồn kho
   (3) hỏi     |                                   GET /products/<id>
   /auth       |                                   (forward token)
        |      |                                   |
        |   +--+-----------------------------------+-----------+
        |   |   SERVICE 3: Order — Quản lý Đơn hàng            |
        |   |   localhost:8002                                 |
        |   |   db_orders.sqlite3 (Order + OrderItem)          |
        |   |                                                 |
        |   |   middleware: bảo vệ /orders, /order_items       |
        |   |   ProductServiceClient: kiểm tra tồn kho         |
        |   +-------------------------------------------------+
        |                         ^
        | (1) đăng nhập           | (2) CRUD /orders, /order_items
        |                         |     kèm Bearer token
        v                         v
+---------------------------------------------------------------------+
|                  CLIENT (Postman / Swagger UI / cURL)                |
+---------------------------------------------------------------------+
```
**Luồng xử lý khi tạo đơn hàng (`POST :8002/orders`):**
1. Client đăng nhập tại **Service 1** (`POST /login`, cổng 8000) và nhận chuỗi JWT.
2. Client gọi `POST http://localhost:8002/orders` kèm Header `Authorization: Bearer <token>` cùng danh sách `items`.
3. Middleware của Service 3 **gọi sang Service 1** (`GET /auth`) kiểm tra token — token thiếu/sai → `401`, Service 1 tắt → `503`.
4. Service 3 **gọi sang Service 2** (`GET /products/<id>`, forward token) kiểm tra tồn kho từng mặt hàng — không đủ tồn kho hoặc sản phẩm không tồn tại → `400`, Service 2 tắt → `503`.
5. Hợp lệ → tạo Order + OrderItem (snapshot `product_name`, `unit_price` tại thời điểm đặt) và tính `total_amount = Σ(quantity × unit_price)` trong **DB riêng** `db_orders.sqlite3` → trả `201 Created`.

---

## 4. CẤU TRÚC CƠ SỞ DỮ LIỆU (DATABASE SCHEMA)

Dự án sử dụng bảng dữ liệu **`User`** được cấu hình trong `core/models.py`:

```python
class User(models.Model):
    IdUser = models.AutoField(primary_key=True, db_column='IdUser')
    UserName = models.CharField(max_length=255, unique=True, db_column='UserName')
    Password = models.CharField(max_length=255, db_column='Password')
    Token = models.CharField(max_length=255, blank=True, null=True, db_column='Token')
```

### Bảng mô tả trường dữ liệu:

| Tên trường (Column) | Kiểu dữ liệu (Data Type) | Thuộc tính / Ràng buộc | Mục đích sử dụng |
| :--- | :--- | :--- | :--- |
| **`IdUser`** | `INTEGER` (`AutoField`) | **PRIMARY KEY**, Auto Increment | Khóa chính định danh duy nhất cho người dùng |
| **`UserName`** | `VARCHAR(255)` | `UNIQUE`, `NOT NULL` | Tên tài khoản hoặc email đăng nhập |
| **`Password`** | `VARCHAR(255)` | `NOT NULL` | Mật khẩu (được lưu trữ dưới dạng mã băm MD5 an toàn) |
| **`Token`** | `VARCHAR(255)` | `NULLABLE` | Lưu trữ chuỗi JWT mới nhất được cấp phát |

> 💡 **Tối ưu hóa độ dài chuỗi JWT:**  
> Chuỗi JWT tiêu chuẩn gồm 3 phần: `Header.Payload.Signature`. Để đảm bảo chuỗi JWT không bao giờ vượt quá giới hạn `VARCHAR(255)` của cột `Token`, payload trong `core/utils.py` được tối giản chỉ lưu các trường cốt lõi:
> `{"id": user.IdUser, "username": user.UserName, "exp": ..., "iat": ...}`.  
> Chiều dài chuỗi sinh ra luôn ổn định ở mức **~140 - 160 ký tự**, tránh triệt để lỗi tràn cột dữ liệu (Database Data Truncation).

### Bảng `products` (Service Quản lý Sản phẩm — Bài 3)
Service 2 sử dụng bảng dữ liệu **`Product`** được cấu hình trong `product_service/products/models.py`:

```python
class Product(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

| Tên cột (Column) | Kiểu dữ liệu (Data Type) | Thuộc tính / Ràng buộc | Mục đích sử dụng |
| :--- | :--- | :--- | :--- |
| **`id`** | `INTEGER` (`AutoField`) | **PRIMARY KEY**, Auto Increment | Khóa chính định danh duy nhất cho sản phẩm |
| **`name`** | `VARCHAR(255)` | `NOT NULL` | Tên sản phẩm |
| **`description`** | `TEXT` | `NULLABLE` | Mô tả chi tiết sản phẩm |
| **`price`** | `DECIMAL(10,2)` | `NOT NULL` | Giá bán sản phẩm |
| **`quantity`** | `INTEGER` | `DEFAULT 0` | Số lượng sản phẩm trong kho |
| **`created_at`** | `TIMESTAMP` | Tự động khi tạo (`auto_now_add`) | Ngày sản phẩm được tạo |
| **`updated_at`** | `TIMESTAMP` | Tự động khi cập nhật (`auto_now`) | Ngày sản phẩm được cập nhật lần cuối |

> 💡 Service 2 dùng **file SQLite riêng** `db_products.sqlite3` — dữ liệu sản phẩm và dữ liệu người dùng nằm ở hai cơ sở dữ liệu độc lập, tuân thủ nguyên tắc tách service trong SOA.

### Bảng `orders` (Service Quản lý Đơn hàng — Bài 4)
Service 3 sử dụng bảng **`Order`** được cấu hình trong `order_service/orders/models.py`:

```python
class Order(models.Model):
    id = models.AutoField(primary_key=True)
    customer_name = models.CharField(max_length=255)
    customer_email = models.CharField(max_length=255)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=50, default='pending',
                              choices=[('pending', 'Pending'), ('completed', 'Completed'),
                                       ('cancelled', 'Cancelled')])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class OrderItem(models.Model):
    id = models.AutoField(primary_key=True)
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product_id = models.IntegerField()
    product_name = models.CharField(max_length=255)
    quantity = models.IntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
```

| Tên cột (Column) | Kiểu dữ liệu (Data Type) | Thuộc tính / Ràng buộc | Mục đích sử dụng |
| :--- | :--- | :--- | :--- |
| **`id`** | `INTEGER` (`AutoField`) | **PRIMARY KEY**, Auto Increment | Khóa chính định danh duy nhất cho đơn hàng |
| **`customer_name`** | `VARCHAR(255)` | `NOT NULL` | Tên khách hàng đặt đơn |
| **`customer_email`** | `VARCHAR(255)` | `NOT NULL` | Email liên hệ khách hàng |
| **`total_amount`** | `DECIMAL(10,2)` | `DEFAULT 0` | Tổng số tiền của đơn hàng (tự động tính lại khi thêm/sửa/xóa mặt hàng) |
| **`status`** | `VARCHAR(50)` | `DEFAULT 'pending'`, choices: `pending / completed / cancelled` | Trạng thái của đơn hàng |
| **`created_at`** | `TIMESTAMP` | Tự động khi tạo (`auto_now_add`) | Ngày đơn hàng được tạo |
| **`updated_at`** | `TIMESTAMP` | Tự động khi cập nhật (`auto_now`) | Ngày đơn hàng được cập nhật lần cuối |

### Bảng `order_items` (chi tiết đơn hàng — Service Quản lý Đơn hàng, Bài 4)

| Tên cột (Column) | Kiểu dữ liệu (Data Type) | Thuộc tính / Ràng buộc | Mục đích sử dụng |
| :--- | :--- | :--- | :--- |
| **`id`** | `INTEGER` (`AutoField`) | **PRIMARY KEY**, Auto Increment | Khóa chính định danh duy nhất cho chi tiết đơn hàng |
| **`order_id`** | `INTEGER` | **FOREIGN KEY** → `orders.id` (related_name `items`) | ID đơn hàng sở hữu mặt hàng này |
| **`product_id`** | `INTEGER` | `NOT NULL` | ID sản phẩm — **lưu vết** để liên kết với dịch vụ quản lý sản phẩm (Service 2) |
| **`product_name`** | `VARCHAR(255)` | `NOT NULL` | *Snapshot* tên sản phẩm tại thời điểm đặt hàng |
| **`quantity`** | `INTEGER` | `DEFAULT 1` | Số lượng sản phẩm trong đơn hàng |
| **`unit_price`** | `DECIMAL(10,2)` | `NOT NULL` | *Snapshot* giá sản phẩm tại thời điểm đặt hàng |
| **`total_price`** | `DECIMAL(10,2)` | `NOT NULL` | Tổng giá trị mặt hàng = `quantity × unit_price` |

> ⚠️ **Lưu ý về tên bảng:** Phụ lục đề bài ghi tên bảng chi tiết đơn hàng là `other_items` — đây là **lỗi đánh máy của đề bài** (cả mục API của đề cũng dùng `GET /order_items`). Hệ thống triển khai đúng theo danh mục API: bảng/model `order_items` / `OrderItem`.
>
> 💡 Service 3 dùng **file SQLite riêng** `db_orders.sqlite3` — dữ liệu đơn hàng tách biệt hoàn toàn với người dùng (Service 1) và sản phẩm (Service 2); thông tin sản phẩm trong đơn được **snapshot** (`product_name`, `unit_price`) nên đơn hàng vẫn đọc được lịch sử giá dù sản phẩm sau đó bị đổi tên/đổi giá/xóa.

---

## 5. CẤU TRÚC THƯ MỤC MÃ NGUỒN

```text
Django_Learning/
│
├── core/                               # Ứng dụng chính xử lý logic API
│   ├── management/
│   │   └── commands/
│   │       └── seed_user.py            # Lệnh tạo tài khoản mẫu kiểm thử nhanh
│   ├── migrations/
│   │   └── 0001_initial.py             # File khởi tạo lược đồ bảng User
│   ├── admin.py                        # Đăng ký quản trị bảng User trong Django Admin
│   ├── apps.py                         # Khai báo cấu hình ứng dụng Core
│   ├── middleware.py                   # JWTAuthenticationMiddleware lọc token cho /hello
│   ├── models.py                       # Model User (IdUser, UserName, Password, Token)
│   ├── serializers.py                  # Bộ tuần tự hóa dữ liệu cho Login, Auth, Register
│   ├── tests.py                        # Bộ 9 bài kiểm thử tự động toàn diện
│   ├── urls.py                         # Tuyến đường API cấp ứng dụng (/api/...)
│   ├── utils.py                        # Tiện ích: generate_jwt, decode_jwt, verify_password
│   └── views.py                        # Views: login_view, auth_view, hello_world, register_view
│
├── myapi/                              # Cấu hình dự án Django
│   ├── __init__.py
│   ├── asgi.py                         # Cấu hình ASGI Server
│   ├── settings.py                     # Khai báo INSTALLED_APPS, MIDDLEWARE, SPECTACULAR
│   ├── urls.py                         # Tuyến đường cấp hệ thống (Root routes & Swagger)
│   └── wsgi.py                         # Cấu hình WSGI Server
│
├── docs/                               # Thư mục chứa đề bài thực hành
│   ├── BÀI THỰC HÀNH SỐ 1.pdf          # Đề bài 1: Cài đặt môi trường & Hello World API
│   ├── BÀI THỰC HÀNH SỐ 2.pdf          # Đề bài 2: Router, Middleware & JWT
│   ├── BÀI THỰC HÀNH SỐ 3.pdf          # Đề bài 3: Service Quản lý Sản phẩm (SOA)
│   └── BÀI THỰC HÀNH SỐ 4.pdf          # Đề bài 4: Service Quản lý Đơn hàng (kiểm tra tồn kho)
│
├── product_service/                   # SERVICE 2 — Quản lý Sản phẩm (Bài 3, cổng 8001)
│   ├── product_service/               # Cấu hình project Service 2
│   │   ├── settings.py                # DB riêng + AUTH_SERVICE_URL trỏ về Service 1
│   │   └── urls.py                    # Tuyến đường /products & Swagger (cổng 8001)
│   ├── products/                      # App chính của Service 2
│   │   ├── management/commands/
│   │   │   └── seed_products.py       # Lệnh tạo sản phẩm mẫu kiểm thử nhanh
│   │   ├── migrations/
│   │   │   └── 0001_initial.py        # File khởi tạo lược đồ bảng products
│   │   ├── middleware.py              # AuthServiceMiddleware gọi sang Service 1
│   │   ├── models.py                  # Model Product (7 cột theo Phụ lục)
│   │   ├── serializers.py             # ProductSerializer
│   │   └── views.py                   # ProductListCreateView, ProductDetailView
│   ├── db_products.sqlite3            # Cơ sở dữ liệu riêng của Service 2
│   └── manage.py                      # Tập lệnh quản trị Django CLI của Service 2
│
├── order_service/                    # SERVICE 3 — Quản lý Đơn hàng (Bài 4, cổng 8002)
│   ├── order_service/                # Cấu hình project Service 3
│   │   ├── settings.py               # DB riêng + PRODUCT_SERVICE_URL/AUTH_SERVICE_URL
│   │   └── urls.py                   # Tuyến đường /orders & /order_items (cổng 8002)
│   ├── orders/                       # App chính của Service 3
│   │   ├── management/commands/
│   │   │   └── seed_orders.py        # Lệnh tạo đơn hàng mẫu kiểm thử nhanh
│   │   ├── migrations/
│   │   │   └── 0001_initial.py       # File khởi tạo lược đồ bảng orders + order_items
│   │   ├── middleware.py             # Middleware gọi /auth (Service 1) bảo vệ API
│   │   ├── models.py                 # Model Order + OrderItem (theo Phụ lục đề bài)
│   │   ├── serializers.py            # Serializer cho Order (lồng items) & OrderItem
│   │   ├── services.py               # ProductServiceClient: kiểm tra tồn kho qua Service 2
│   │   ├── tests.py                  # Bộ 12 kiểm thử tự động (mock, không cần server)
│   │   └── views.py                  # Controller CRUD /orders & /order_items
│   ├── db_orders.sqlite3             # Cơ sở dữ liệu riêng của Service 3
│   └── manage.py                     # Tập lệnh quản trị Django CLI của Service 3
│
├── db.sqlite3                          # Cơ sở dữ liệu SQLite cục bộ (Service 1)
├── manage.py                           # Tập lệnh quản trị Django CLI
├── requirements.txt                    # Danh sách các gói thư viện phụ thuộc
├── tutorial.md                         # Ghi chú hướng dẫn bài thực hành số 1
└── README.md                           # Báo cáo và tài liệu hướng dẫn toàn diện
```

---

## 6. YÊU CẦU MÔI TRƯỜNG & CÔNG NGHỆ SỬ DỤNG

### Công nghệ nền tảng:
- **Python:** Phiên bản `>= 3.10`
- **Django:** Phiên bản `6.1.1` (hoặc các phiên bản `5.x / 6.x`)
- **Django REST Framework (DRF):** `3.18.1`
- **PyJWT:** `2.15.1` (Thư viện xử lý JWT)
- **drf-spectacular:** `0.30.0` (Bộ sinh tài liệu OpenAPI 3.0 & Swagger UI)
- **requests:** `2.34.2` (Gọi HTTP service-to-service: Service sản phẩm → Service xác thực)
- **SQLite3:** Hệ quản trị cơ sở dữ liệu nhúng

---

## 7. HƯỚNG DẪN CÀI ĐẶT & KHỞI CHẠY TỪ A-Z

### Bước 1: Mở Terminal và Kích hoạt Môi trường ảo (Virtualenv)

Di chuyển vào thư mục dự án `Django_Learning`:

- **Trên Windows (PowerShell):**
  ```powershell
  # Nếu bị chặn bởi chính sách ExecutionPolicy, chạy lệnh sau trước:
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process

  # Kích hoạt venv
  .\venv\Scripts\Activate.ps1
  ```
- **Trên Windows (Command Prompt - CMD):**
  ```cmd
  venv\Scripts\activate.bat
  ```
- **Trên macOS / Linux:**
  ```bash
  source venv/bin/activate
  ```
*(Khi kích hoạt thành công, đầu dòng lệnh terminal sẽ xuất hiện tiền tố `(venv)`)*

---

### Bước 2: Cài đặt thư viện phụ thuộc
Nếu bạn clone mã nguồn sang máy mới chưa có sẵn thư mục `venv`, thực hiện:
```bash
python -m venv venv
pip install -r requirements.txt
```

---

### Bước 3: Đồng bộ Cơ sở dữ liệu (Migration)
Khởi tạo và cập nhật cấu trúc bảng `User` vào file `db.sqlite3`:
```bash
python manage.py makemigrations
python manage.py migrate
```

---

### Bước 4: Tạo tài khoản mẫu để kiểm thử (Seed Data)
Dự án đã tích hợp sẵn lệnh tạo nhanh tài khoản mẫu:
```bash
python manage.py seed_user
```
**Thông tin tài khoản mẫu được tạo sẵn:**
- **Tài khoản (`userName`):** `testuser`
- **Mật khẩu gốc (Plain text):** `123456`
- **Mật khẩu Base64:** `MTIzNDU2`
- **Mật khẩu băm MD5:** `e10adc3949ba59abbe56e057f20f883e`

*(Tùy chọn: Nếu muốn truy cập trang quản trị `/admin/`, tạo tài khoản Superuser bằng lệnh: `python manage.py createsuperuser`)*

---

### Bước 5: Khởi động máy chủ phát triển (Development Server)
```bash
python manage.py runserver
```
Máy chủ sẽ lắng nghe tại địa chỉ: `http://127.0.0.1:8000/` (hoặc `http://localhost:8000/`)

---

### Bước 6: Khởi động Service Quản lý Sản phẩm (Bài 3)

Hệ thống gồm **2 service độc lập** chạy trên 2 cổng khác nhau — cần mở **2 terminal riêng** (đều kích hoạt `venv` như Bước 1):

**Terminal 1 — Service đăng nhập (cổng 8000):**
```powershell
cd Django_Learning
.\venv\Scripts\Activate.ps1
python manage.py runserver 8000
```

**Terminal 2 — Service quản lý sản phẩm (cổng 8001):**
```powershell
cd Django_Learning\product_service
..\venv\Scripts\Activate.ps1
python manage.py runserver 8001
```

Khởi tạo cơ sở dữ liệu và tạo nhanh sản phẩm mẫu để kiểm thử (chạy trong thư mục `product_service`):
```bash
python manage.py migrate
python manage.py seed_products
```

> ⚠️ Service sản phẩm **phụ thuộc** Service xác thực: nếu tắt Terminal 1, mọi request `/products` sẽ nhận `503 Service Unavailable`.

---

### Bước 7: Khởi động Service Quản lý Đơn hàng (Bài 4)

Từ Bài 4, hệ thống gồm **3 service độc lập** chạy trên 3 cổng khác nhau — cần mở **terminal riêng thứ 3** (kích hoạt `venv` như Bước 1; Terminal 1 và Terminal 2 vẫn phải đang chạy):

**Terminal 3 — Service quản lý đơn hàng (cổng 8002):**
```powershell
cd Django_Learning\order_service
..\venv\Scripts\Activate.ps1
python manage.py migrate
python manage.py seed_orders
python manage.py runserver 8002
```

Máy chủ Service 3 sẽ lắng nghe tại địa chỉ: `http://localhost:8002/`.

> ⚠️ Service đơn hàng **phụ thuộc cả 2 service còn lại**: tắt Terminal 1 (cổng 8000) → mọi request `/orders`, `/order_items` nhận `503`; tắt Terminal 2 (cổng 8001) → không tạo được đơn/cụ thể là nhận `503` khi kiểm tra tồn kho.

---

## 8. TÀI LIỆU API CHI TIẾT (API DOCUMENTATION)

### Danh sách Endpoint tổng quan:

| Nhóm chức năng | Phương thức | Đường dẫn (URL) | Mô tả tóm tắt | Quyền truy cập |
| :--- | :---: | :--- | :--- | :---: |
| **Login** | `POST` | `/` hoặc `/login` | Đăng nhập và cấp phát chuỗi JWT | Public |
| **Auth** | `GET` / `POST` | `/auth` | Xác thực tính hợp lệ của Token | Public |
| **Hello World** | `GET` | `/hello` hoặc `/api/hello/` | API Bài 1 in dòng `hello-world` |  **Cần Bearer Token** |
| **Register** | `POST` | `/register` | Đăng ký tài khoản người dùng mới | Public |
| **Products — Danh sách** | `GET` | `http://localhost:8001/products` | Lấy danh sách tất cả sản phẩm (Service 2) |  **Cần Bearer Token** |
| **Products — Chi tiết** | `GET` | `http://localhost:8001/products/id` | Lấy thông tin chi tiết một sản phẩm (Service 2) |  **Cần Bearer Token** |
| **Products — Thêm mới** | `POST` | `http://localhost:8001/products` | Thêm một sản phẩm mới (Service 2) |  **Cần Bearer Token** |
| **Products — Cập nhật** | `PUT` | `http://localhost:8001/products/id` | Cập nhật thông tin sản phẩm (Service 2) |  **Cần Bearer Token** |
| **Products — Xóa** | `DELETE` | `http://localhost:8001/products/id` | Xóa một sản phẩm (Service 2) |  **Cần Bearer Token** |
| **Swagger UI (Service 2)** | `GET` | `http://localhost:8001/swagger/` | Giao diện tài liệu API dịch vụ sản phẩm | Public |
| **Orders — Danh sách** | `GET` | `http://localhost:8002/orders` | Lấy danh sách tất cả đơn hàng (Service 3) |  **Cần Bearer Token** |
| **Orders — Chi tiết** | `GET` | `http://localhost:8002/orders/id` | Lấy chi tiết một đơn hàng kèm danh sách items (Service 3) |  **Cần Bearer Token** |
| **Orders — Tạo đơn** | `POST` | `http://localhost:8002/orders` | Tạo đơn hàng mới có kiểm tra tồn kho (Service 3) |  **Cần Bearer Token** |
| **Orders — Cập nhật trạng thái** | `PUT` | `http://localhost:8002/orders/id` | Cập nhật trạng thái đơn hàng (Service 3) |  **Cần Bearer Token** |
| **Orders — Xóa** | `DELETE` | `http://localhost:8002/orders/id` | Xóa một đơn hàng (Service 3) |  **Cần Bearer Token** |
| **Order Items — Danh sách/Chi tiết** | `GET` | `http://localhost:8002/order_items` hoặc `/order_items/id` | Lấy danh sách/chi tiết các mặt hàng trong đơn (Service 3) |  **Cần Bearer Token** |
| **Order Items — Thêm/Sửa/Xóa** | `POST`/`PUT`/`DELETE` | `http://localhost:8002/order_items` hoặc `/order_items/id` | Thêm, sửa số lượng, xóa mặt hàng — tổng tiền tự tính lại (Service 3) |  **Cần Bearer Token** |
| **Swagger UI (Service 3)** | `GET` | `http://localhost:8002/swagger/` | Giao diện tài liệu API dịch vụ đơn hàng | Public |
| **Swagger UI** | `GET` | `/swagger/` hoặc `/docs/` | Giao diện tài liệu API trực quan | Public |
| **OpenAPI Schema** | `GET` | `/api/schema/` | Tải về cấu hình JSON/YAML OpenAPI | Public |
| **Django Admin** | `GET` | `/admin/` | Trang quản trị dữ liệu hệ thống | Cần tài khoản Admin |

---

### Chi tiết từng Endpoint

#### 8.1. API Đăng nhập (Sinh JWT Token)
- **Phương thức:** `POST`
- **Đường dẫn:** `http://localhost:8000/` hoặc `http://localhost:8000/login`
- **Headers:** `Content-Type: application/json`
- **Body JSON (Hỗ trợ Base64 hoặc MD5):**
  - *Ví dụ 1: Gửi mật khẩu dạng Base64 (`123456` -> `MTIzNDU2`):*
    ```json
    {
      "userName": "testuser",
      "password": "MTIzNDU2"
    }
    ```
  - *Ví dụ 2: Gửi mật khẩu dạng mã băm MD5:*
    ```json
    {
      "userName": "testuser",
      "password": "e10adc3949ba59abbe56e057f20f883e"
    }
    ```
- **Phản hồi thành công (`200 OK`):**
  ```json
  {
    "message": "Đăng nhập thành công",
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MSwidXNlcm5hbWUiOiJ0ZXN0dXNlciIsImV4cCI6MTc4OTk2MzkxOSwiaWF0IjoxNzg5OTU2NzE5fQ.xxx...",
    "user": {
      "IdUser": 1,
      "UserName": "testuser"
    }
  }
  ```
- **Phản hồi khi sai tài khoản/mật khẩu (`401 Unauthorized`):**
  ```json
  {
    "error": "Unauthorized",
    "detail": "Mật khẩu không chính xác."
  }
  ```
- **Lệnh cURL kiểm thử nhanh:**
  ```bash
  curl -X POST http://localhost:8000/ \
    -H "Content-Type: application/json" \
    -d "{\"userName\": \"testuser\", \"password\": \"MTIzNDU2\"}"
  ```

---

#### 8.2. API Xác thực Token (Auth)
- **Phương thức:** `GET` hoặc `POST`
- **Đường dẫn:** `http://localhost:8000/auth`
- **Cách truyền Token (chọn 1 trong 3 cách):**
  - **Cách 1 (Khuyên dùng):** Qua Header `Authorization: Bearer <chuỗi_token>`
  - **Cách 2:** Qua Body `{"token": "<chuỗi_token>"}` (Phương thức `POST`)
  - **Cách 3:** Qua Query param: `http://localhost:8000/auth?token=<chuỗi_token>`
- **Phản hồi khi Token hợp lệ (`200 OK`):**
  ```json
  {
    "valid": true,
    "message": "Token hợp lệ và còn hiệu lực.",
    "payload": {
      "id": 1,
      "username": "testuser",
      "exp": 1789963919,
      "iat": 1789956719
    },
    "user": {
      "IdUser": 1,
      "UserName": "testuser",
      "Token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
  }
  ```
- **Phản hồi khi Token hết hạn hoặc sai chữ ký (`401 Unauthorized`):**
  ```json
  {
    "valid": false,
    "error": "Invalid Token",
    "detail": "Chữ ký Token không hợp lệ (Invalid Signature)."
  }
  ```
- **Lệnh cURL kiểm thử nhanh:**
  ```bash
  curl -X GET http://localhost:8000/auth \
    -H "Authorization: Bearer <DÁN_CHUỖI_TOKEN_VÀO_ĐÂY>"
  ```

---

#### 8.3. API "Hello World" (Được bảo vệ bởi Middleware)
- **Phương thức:** `GET`
- **Đường dẫn:** `http://localhost:8000/hello` hoặc `http://localhost:8000/api/hello/`
- **Yêu cầu:** Bắt buộc phải đính kèm Header `Authorization: Bearer <chuỗi_token>`
- **Trường hợp 1: Không có Header Authorization hoặc Token sai (`401 Unauthorized` do Middleware chặn):**
  ```json
  {
    "error": "Unauthorized",
    "detail": "Vui lòng cung cấp JWT token qua Header 'Authorization: Bearer <token>' để truy cập API này."
  }
  ```
- **Trường hợp 2: Có Token hợp lệ (`200 OK` do Middleware phê duyệt):**
  ```json
  {
    "message": "hello-world",
    "authenticated_user": {
      "IdUser": 1,
      "UserName": "testuser"
    }
  }
  ```
- **Lệnh cURL kiểm thử:**
  ```bash
  # Thử nghiệm 1: Gọi không có token -> Sẽ nhận lỗi 401
  curl -i http://localhost:8000/hello

  # Thử nghiệm 2: Gọi kèm Bearer token -> Nhận kết quả hello-world 200 OK
  curl -X GET http://localhost:8000/hello \
    -H "Authorization: Bearer <DÁN_CHUỖI_TOKEN_VÀO_ĐÂY>"
  ```

---

#### 8.4. API Đăng ký tài khoản mới (Register)
- **Phương thức:** `POST`
- **Đường dẫn:** `http://localhost:8000/register`
- **Body JSON:**
  ```json
  {
    "userName": "sinhvien_cntt",
    "password": "Password@2026"
  }
  ```
- **Phản hồi thành công (`201 Created`):**
  ```json
  {
    "message": "Tạo tài khoản thành công!",
    "user": {
      "IdUser": 2,
      "UserName": "sinhvien_cntt"
    }
  }
  ```

#### 8.5. API Quản lý Sản phẩm (Service 2 — Bài 3)

Toàn bộ endpoint của Service sản phẩm yêu cầu Header `Authorization: Bearer <token>` — token lấy từ Service 1 (xem mục 8.1).

- **Đường dẫn gốc:** `http://localhost:8001/products`
- **Body JSON (dùng cho POST/PUT):**
  ```json
  {
    "name": "Tai nghe Sony WH-1000XM5",
    "description": "Chống ồn chủ động",
    "price": 7500000,
    "quantity": 15
  }
  ```

| Phương thức | Đường dẫn | Chức năng | Phản hồi |
| :--- | :--- | :--- | :--- |
| `GET` | `/products` | Lấy danh sách tất cả sản phẩm | `200 OK` |
| `POST` | `/products` | Thêm sản phẩm mới | `201 Created` |
| `GET` | `/products/id` | Lấy thông tin chi tiết một sản phẩm | `200 OK` / `404 Not Found` |
| `PUT` | `/products/id` | Cập nhật thông tin sản phẩm | `200 OK` / `404 Not Found` |
| `DELETE` | `/products/id` | Xóa sản phẩm | `204 No Content` / `404 Not Found` |

- **Lỗi xác thực (`401 Unauthorized`)** — thiếu token, token sai hoặc hết hạn (middleware hỏi Service 1):
  ```json
  {
    "error": "Unauthorized",
    "detail": "Vui lòng cung cấp JWT token qua Header 'Authorization: Bearer <token>'."
  }
  ```
- **Service xác thực không khả dụng (`503`)** — minh chứng sự phụ thuộc giữa các service trong SOA:
  ```json
  {
    "error": "Service Unavailable",
    "detail": "Service xác thực (Bài 2) hiện không khả dụng. Vui lòng thử lại sau."
  }
  ```
- **Lệnh cURL kiểm thử nhanh:**
  ```bash
  # 1) Lấy token từ Service 1
  curl -X POST http://localhost:8000/login -H "Content-Type: application/json" \
    -d "{\"userName\": \"testuser\", \"password\": \"MTIzNDU2\"}"

  # 2) Gọi danh sách sản phẩm (thay <TOKEN> bằng chuỗi token vừa nhận)
  curl http://localhost:8001/products -H "Authorization: Bearer <TOKEN>"
  ```

#### 8.6. API Quản lý Đơn hàng (Service 3 — Bài 4)

Toàn bộ endpoint của Service đơn hàng yêu cầu Header `Authorization: Bearer <token>` — token lấy từ Service 1 (xem mục 8.1).

- **Đường dẫn gốc:** `http://localhost:8002/orders` và `http://localhost:8002/order_items`
- **Body JSON tạo đơn hàng (`POST /orders`)** — với mỗi mặt hàng service gọi Service 2 kiểm tra tồn kho rồi *snapshot* tên & đơn giá; `total_amount = Σ(quantity × unit_price)`:
  ```json
  {
    "customer_name": "Nguyễn Văn An",
    "customer_email": "an@example.com",
    "items": [
      {"product_id": 1, "quantity": 2},
      {"product_id": 3, "quantity": 1}
    ]
  }
  ```
- **Body JSON cập nhật trạng thái (`PUT /orders/id`)** — chỉ nhận `pending` / `completed` / `cancelled`:
  ```json
  {"status": "completed"}
  ```

| Phương thức | Đường dẫn | Chức năng | Phản hồi |
| :--- | :--- | :--- | :--- |
| `GET` | `/orders` | Lấy danh sách tất cả đơn hàng (dạng phẳng) | `200 OK` |
| `POST` | `/orders` | Tạo đơn hàng mới (kiểm tra tồn kho qua Service 2) | `201 Created` / `400` / `503` |
| `GET` | `/orders/id` | Chi tiết đơn hàng kèm danh sách `items` lồng nhau | `200 OK` / `404 Not Found` |
| `PUT` | `/orders/id` | Cập nhật trạng thái đơn hàng | `200 OK` / `400` / `404 Not Found` |
| `DELETE` | `/orders/id` | Xóa một đơn hàng | `204 No Content` / `404 Not Found` |
| `GET` | `/order_items` | Lấy danh sách tất cả mặt hàng trong đơn | `200 OK` |
| `POST` | `/order_items` | Thêm mặt hàng `{order_id, product_id, quantity}` — `total_amount` tăng | `201 Created` / `400` / `503` |
| `GET` | `/order_items/id` | Chi tiết một mặt hàng | `200 OK` / `404 Not Found` |
| `PUT` | `/order_items/id` | Cập nhật số lượng `{"quantity": n}` — tính lại `total_price` & `total_amount` | `200 OK` / `404 Not Found` |
| `DELETE` | `/order_items/id` | Xóa mặt hàng — tính lại `total_amount` | `204 No Content` / `404 Not Found` |

- **Phản hồi tạo đơn hàng thành công (`201 Created`):**
  ```json
  {
    "message": "Tạo đơn hàng thành công",
    "order": {
      "id": 1,
      "customer_name": "Nguyễn Văn An",
      "customer_email": "an@example.com",
      "total_amount": "31500000.00",
      "status": "pending",
      "created_at": "2026-11-05T10:30:00Z",
      "updated_at": "2026-11-05T10:30:00Z",
      "items": [
        {
          "id": 1,
          "product_id": 1,
          "product_name": "Laptop Dell",
          "quantity": 2,
          "unit_price": "15000000.00",
          "total_price": "30000000.00"
        },
        {
          "id": 2,
          "product_id": 3,
          "product_name": "Chuột Logitech MX",
          "quantity": 1,
          "unit_price": "1500000.00",
          "total_price": "1500000.00"
        }
      ]
    }
  }
  ```
- **Các mã lỗi thường gặp:**
  - **`401 Unauthorized`** — thiếu token, token sai hoặc hết hạn (middleware hỏi Service 1):
    ```json
    {"error": "Unauthorized", "detail": "Vui lòng cung cấp JWT token qua Header 'Authorization: Bearer <token>'."}
    ```
  - **`400 Bad Request` — tồn kho không đủ** (Service 2 trả về sản phẩm nhưng `quantity` trong kho nhỏ hơn số lượng đặt):
    ```json
    {"error": "Tồn kho không đủ", "detail": "Sản phẩm 'Laptop Dell' chỉ còn 2 sản phẩm trong kho."}
    ```
  - **`400 Bad Request` — sản phẩm không tồn tại** (Service 2 trả `404` cho `product_id`):
    ```json
    {"error": "Sản phẩm không tồn tại", "detail": "Sản phẩm #999 không tồn tại trong dịch vụ quản lý sản phẩm."}
    ```
  - **`400 Bad Request` — dữ liệu không hợp lệ** (ví dụ thiếu `customer_name`, `quantity` nhỏ hơn 1):
    ```json
    {"error": "Dữ liệu không hợp lệ", "detail": "customer_name: Trường này là bắt buộc."}
    ```
    ```json
    {"customer_name": ["Trường này là bắt buộc."]}
    ```
  - **`404 Not Found`** — đơn hàng/mặt hàng với `id` không tồn tại:
    ```json
    {"detail": "Không tìm thấy."}
    ```
  - **`503 Service Unavailable`** — Service quản lý sản phẩm (cổng 8001) đang tắt khi cần kiểm tra tồn kho:
    ```json
    {"error": "Service Unavailable", "detail": "Service quản lý sản phẩm hiện không khả dụng. Vui lòng thử lại sau."}
    ```
- **Lệnh cURL kiểm thử nhanh:**
  ```bash
  # 1) Lấy token từ Service 1
  curl -X POST http://localhost:8000/login -H "Content-Type: application/json" \
    -d "{\"userName\": \"testuser\", \"password\": \"MTIzNDU2\"}"

  # 2) Tạo đơn hàng có 2 Laptop Dell (thay <TOKEN> bằng chuỗi token vừa nhận)
  curl -X POST http://localhost:8002/orders -H "Content-Type: application/json" \
    -H "Authorization: Bearer <TOKEN>" \
    -d "{\"customer_name\": \"Nguyễn Văn An\", \"customer_email\": \"an@example.com\", \"items\": [{\"product_id\": 1, \"quantity\": 2}]}"

  # 3) Xem chi tiết đơn hàng vừa tạo (kèm danh sách items)
  curl http://localhost:8002/orders/1 -H "Authorization: Bearer <TOKEN>"
  ```

---

## 9. HƯỚNG DẪN KIỂM THỬ VỚI POSTMAN & SWAGGER UI

### 9.1. Kiểm thử trực quan trên Swagger UI
1. Mở trình duyệt web và truy cập: **`http://localhost:8000/swagger/`**
2. Tìm đến mục **`POST /` (Dịch vụ Đăng nhập)**:
   - Nhấn **Try it out**.
   - Nhập thông tin đăng nhập: `userName: testuser`, `password: MTIzNDU2`.
   - Bấm **Execute**.
   - Copy toàn bộ chuỗi token nằm trong trường `"token": "..."` ở phần kết quả trả về.
3. Kéo lên đầu trang Swagger, nhấn vào nút **Authorize 🔓** (có biểu tượng ổ khóa màu xanh lá cây):
   - Nhập vào ô Value: chuỗi token vừa copy (Swagger tự động hỗ trợ định dạng Bearer).
   - Nhấn **Authorize** rồi nhấn **Close**.
4. Tìm đến mục **`GET /hello` (API Hello World)**:
   - Nhấn **Try it out** -> **Execute**.
   - Quan sát kết quả: Hệ thống trả về `200 OK` cùng chuỗi `{"message": "hello-world"}`.
   - Thử nhấn **Logout** ở nút Authorize rồi gọi lại `/hello` để thấy Middleware chặn lại với mã lỗi `401 Unauthorized`.

---

### 9.2. Kiểm thử trên Postman
1. **Request 1 - Đăng nhập:**
   - Method: `POST` | URL: `http://localhost:8000/login`
   - Body -> chọn `raw` -> `JSON`:
     ```json
     {
       "userName": "testuser",
       "password": "MTIzNDU2"
     }
     ```
   - Gửi request và sao chép chuỗi `token`.
2. **Request 2 - Xác thực Token:**
   - Method: `GET` | URL: `http://localhost:8000/auth`
   - Headers: Thêm Key `Authorization`, Value: `Bearer <chuỗi_token>`.
3. **Request 3 - Gọi API Hello World:**
   - Method: `GET` | URL: `http://localhost:8000/hello`
   - Tab **Authorization**: Chọn Type là `Bearer Token`, dán mã token vào ô Token.
   - Nhấn **Send** -> Kết quả hiển thị `"message": "hello-world"`.

### 9.3. Kịch bản kiểm thử Service Quản lý Sản phẩm (Bài 3) & kết quả thực tế

Quy trình trên Swagger UI:
1. Mở `http://localhost:8000/swagger/` → mục **POST /login** → **Try it out** → nhập `userName: testuser`, `password: MTIzNDU2` → **Execute** → copy chuỗi `token`.
2. Mở tab mới `http://localhost:8001/swagger/` → nhấn nút **Authorize 🔓** → dán token vào ô Value → **Authorize** → **Close**.
3. Lần lượt **Try it out** các endpoint `/products` (GET, POST, PUT, DELETE).

Bảng kết quả chạy thực tế 9 kịch bản kiểm thử:

| # | Kịch bản | Kết quả thực tế |
| :---: | :--- | :--- |
| 1 | `POST :8000/login` (testuser / mật khẩu Base64) | `200 OK` + chuỗi JWT token |
| 2 | `GET :8001/products` **không kèm token** | `401 Unauthorized` — middleware chặn |
| 3 | `GET :8001/products` kèm Bearer token | `200 OK` + danh sách 3 sản phẩm mẫu |
| 4 | `POST :8001/products` tạo sản phẩm mới | `201 Created` |
| 5 | `GET :8001/products/4` xem chi tiết | `200 OK` |
| 6 | `PUT :8001/products/4` cập nhật giá/số lượng | `200 OK` — `updated_at` tự thay đổi |
| 7 | `DELETE :8001/products/4` | `204 No Content` |
| 8 | `GET :8001/products/4` sau khi xóa | `404 Not Found` |
| 9 | Token giả mạo / **tắt Service 1** | `401` (lý do do Service 1 trả về) / `503 Service Unavailable` |

### 9.4. Kịch bản kiểm thử Service Quản lý Đơn hàng (Bài 4) & kết quả thực tế

Quy trình trên Swagger UI:
1. Mở `http://localhost:8000/swagger/` → mục **POST /login** → **Try it out** → nhập `userName: testuser`, `password: MTIzNDU2` → **Execute** → copy chuỗi `token`.
2. Mở tab mới `http://localhost:8002/swagger/` → nhấn nút **Authorize 🔓** → dán token vào ô Value → **Authorize** → **Close**.
3. Lần lượt **Try it out** các endpoint `/orders` và `/order_items` (GET, POST, PUT, DELETE).

Bảng kết quả chạy thực tế 12 kịch bản kiểm thử:

| # | Kịch bản | Kết quả thực tế |
| :---: | :--- | :--- |
| 1 | `POST :8000/login` (testuser / mật khẩu Base64) | `200 OK` + chuỗi JWT token |
| 2 | `GET :8002/orders` **không kèm token** | `401 Unauthorized` — middleware chặn |
| 3 | `POST :8002/orders` tạo đơn gồm 2 mặt hàng (`items` có `product_id`, `quantity`) | `201 Created` + `total_amount = Σ(quantity × unit_price)`, `status: pending`, items snapshot `product_name` & `unit_price` |
| 4 | `GET :8002/orders/id` xem chi tiết | `200 OK` + danh sách `items` lồng trong đơn hàng |
| 5 | `POST :8002/orders` với `quantity` **vượt tồn kho** Service 2 | `400 Bad Request` — không tạo đơn |
| 6 | `POST :8002/orders` với `product_id` không tồn tại (Service 2 trả `404`) | `400 Bad Request` — không tạo đơn |
| 7 | `PUT :8002/orders/id` đổi `status: completed` / giá trị ngoài choices | `200 OK` / `400 Bad Request` |
| 8 | `POST :8002/order_items` thêm mặt hàng vào đơn | `201 Created` + `total_amount` của đơn tăng đúng |
| 9 | `PUT :8002/order_items/id` đổi `quantity` | `200 OK` + `total_price` & `total_amount` được tính lại |
| 10 | `DELETE :8002/order_items/id` xóa mặt hàng | `204 No Content` + `total_amount` tính lại |
| 11 | `DELETE :8002/orders/id` xóa đơn hàng | `204 No Content` |
| 12 | **Tắt Service 1 (8000)** / **tắt Service 2 (8001)** rồi gọi API | Mọi request → `503` / tạo đơn nhận `503` khi kiểm tra tồn kho |

---

## 10. KIỂM THỬ TỰ ĐỘNG (AUTOMATED UNIT TESTS)

Dự án được xây dựng kèm bộ test tự động độc lập tại file [core/tests.py](file:///d:/CODES/Py/Django_Learning/core/tests.py) sử dụng `APITestCase` của Django REST Framework.

Từ Bài 4, Service Quản lý Đơn hàng có thêm bộ **12 test tự động** tại `order_service/orders/tests.py`. Điểm đặc biệt: toàn bộ test dùng `unittest.mock` để **giả lập (mock)** các lời gọi HTTP sang Service 1 (`GET /auth`) và Service 2 (`GET /products/<id>`), nên **không cần khởi động bất kỳ server nào** (8000/8001/8002) vẫn chạy được đầy đủ — kể cả các kịch bản "Service tắt" hay "tồn kho không đủ".

### Lệnh chạy toàn bộ test:
```powershell
# Bộ test Service 1 (đăng nhập / JWT)
python manage.py test

# Bộ test Service 3 (đơn hàng — chạy trong thư mục order_service, không cần bật server)
cd order_service
python manage.py test
```

### Kết quả chạy kiểm thử thực tế:
```text
Creating test database for alias 'default'...
System check identified no issues (0 silenced).
.........
----------------------------------------------------------------------
Ran 9 tests in 2.400s

OK
Destroying test database for alias 'default'...
```

### Chi tiết 9 trường hợp kiểm thử (Test Cases):
1. `test_01_login_with_base64_password`: Xác minh đăng nhập thành công với mật khẩu mã hóa Base64 và kiểm tra việc lưu chuỗi token vào cột `Token` trong database.
2. `test_02_login_with_md5_password`: Xác minh đăng nhập thành công khi client gửi mật khẩu dạng băm MD5.
3. `test_03_login_with_plain_password`: Xác minh đăng nhập bằng mật khẩu văn bản thô.
4. `test_04_login_wrong_password`: Xác minh hệ thống từ chối và trả về mã lỗi `401 Unauthorized` khi nhập sai mật khẩu.
5. `test_05_auth_token_endpoint`: Kiểm tra API `/auth` giải mã và xác nhận tính hợp lệ của token qua cả Header Authorization và POST body.
6. `test_06_middleware_blocks_hello_world_without_token`: Kiểm tra Middleware chặn request truy cập `/hello` khi không có token (trả về mã 401).
7. `test_07_middleware_blocks_hello_world_with_invalid_token`: Kiểm tra Middleware chặn request truy cập `/hello` khi token giả mạo hoặc sai định dạng.
8. `test_08_middleware_allows_hello_world_with_valid_token`: Kiểm tra Middleware cho phép truy cập `/hello` khi cung cấp token JWT hợp lệ.
9. `test_09_register_endpoint`: Kiểm tra quy trình đăng ký tài khoản mới và lưu mật khẩu dạng băm an toàn vào cơ sở dữ liệu.

### Chi tiết 12 test cases của Service Quản lý Đơn hàng (`order_service/orders/tests.py`):

| # | Tên test | Ý nghĩa |
| :---: | :--- | :--- |
| 1 | `test_01_get_orders_without_token_returns_401` | Middleware chặn `/orders` và `/order_items` khi thiếu Bearer token → `401` (không gọi network). |
| 2 | `test_02_get_orders_with_valid_token_returns_200` | Token được Service 1 (mock) xác nhận → `200 OK` + danh sách đơn hàng; Service 1 từ chối → `401`. |
| 3 | `test_03_create_order_with_items_success` | Tạo đơn 2 mặt hàng → `201`, `total_amount = Σ(quantity × unit_price)`, items snapshot `product_name`/`unit_price`, `status: pending`; thiếu `customer_name` → `400`. |
| 4 | `test_04_create_order_insufficient_stock_returns_400` | Số lượng đặt vượt tồn kho Service 2 (15 > 10) → `400`, không tạo đơn. |
| 5 | `test_05_create_order_product_not_found_returns_400` | Service 2 trả `404` cho `product_id` → `400`, không tạo đơn. |
| 6 | `test_06_create_order_product_service_down_returns_503` | Service 2 "tắt" (giả lập `RequestException`) → `503 Service Unavailable`. |
| 7 | `test_07_get_order_detail_returns_nested_items` | `GET /orders/id` trả chi tiết kèm `items` lồng nhau; `id` không tồn tại → `404` (cả `/order_items/id`). |
| 8 | `test_08_update_order_status` | `PUT /orders/id`: status hợp lệ → `200` + cập nhật DB; status sai → `400`; đơn không tồn tại → `404`. |
| 9 | `test_09_delete_order_returns_204` | `DELETE /orders/id` → `204 No Content`; xóa lần nữa → `404`. |
| 10 | `test_10_add_order_item_updates_order_total` | `POST /order_items` → `201` + `total_amount` của đơn tăng đúng; `order_id` không tồn tại → `400`. |
| 11 | `test_11_update_order_item_recomputes_totals` | `PUT /order_items/id` đổi `quantity` → `total_price` của item và `total_amount` của đơn được tính lại. |
| 12 | `test_12_delete_order_item_recomputes_total` | `DELETE /order_items/id` → `204` + `total_amount` của đơn giảm về 0 khi hết item. |

> 💡 Kỹ thuật mock: cả middleware và ProductServiceClient đều `import requests`, nên test gắn cho `requests.get` một `side_effect` điều hướng theo URL — lời gọi `/auth` nhận phản hồi của Service 1, lời gọi `/products/<id>` nhận phản hồi của Service 2; các kịch bản lỗi (404, hết tồn kho, mất kết nối) được mô phỏng bằng cách thay đổi trạng thái phản hồi giả lập.

---

## 11. XỬ LÝ SỰ CỐ THƯỜNG GẶP (TROUBLESHOOTING)

### 1. Lỗi PowerShell không cho kích hoạt `venv` (`running scripts is disabled on this system`)
- **Nguyên nhân:** Chính sách bảo mật ExecutionPolicy của Windows hạn chế chạy script `.ps1`.
- **Cách khắc phục:** Mở PowerShell và chạy:
  ```powershell
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
  .\venv\Scripts\Activate.ps1
  ```

### 2. Gọi `/hello` luôn nhận thông báo lỗi 401 Unauthorized
- **Nguyên nhân:** Bạn chưa truyền Header `Authorization` hoặc chưa thêm tiền tố `Bearer ` trước chuỗi token.
- **Cách khắc phục:** Đảm bảo Header có định dạng chính xác:
  ```text
  Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6...
  ```
  *(Chú ý có dấu cách giữa từ `Bearer` và chuỗi token)*.

### 3. Cổng 8000 bị xung đột hoặc đang được tiến trình khác sử dụng
- **Cách khắc phục:** Khởi chạy máy chủ trên cổng khác (ví dụ cổng 8080):
  ```powershell
  python manage.py runserver 8080
  ```
  Khi đó đường dẫn API sẽ là `http://localhost:8080/`.

### 4. Gọi `/products` nhận lỗi `503 Service Unavailable` (Bài 3)
- **Nguyên nhân:** Service xác thực (terminal chạy `runserver 8000`) đã bị tắt hoặc chưa khởi động.
- **Cách khắc phục:** Mở lại Terminal 1 và chạy `python manage.py runserver 8000` — Service sản phẩm phụ thuộc Service xác thực theo đúng kiến trúc SOA.

### 5. Lỗi `can't open file 'manage.py'` khi chạy lệnh của Service 2
- **Nguyên nhân:** Đang đứng sai thư mục — mỗi service có file `manage.py` riêng.
- **Cách khắc phục:** Service sản phẩm phải chạy trong thư mục `Django_Learning\product_service` (gõ `cd product_service` trước khi chạy lệnh).

### 6. Lỗi cú pháp khi dán lệnh `curl` vào PowerShell
- **Nguyên nhân:** Trong Windows PowerShell, `curl` là bí danh của lệnh khác (`Invoke-WebRequest`).
- **Cách khắc phục:** Chạy các lệnh cURL trong **Git Bash**, hoặc dùng Swagger UI / Postman.

### 7. Tạo đơn hàng nhận `503` kèm thông báo "Service quản lý sản phẩm không khả dụng" (Bài 4)
- **Nguyên nhân:** Service quản lý sản phẩm (Terminal 2 chạy `runserver 8001`) đã bị tắt hoặc chưa khởi động — Service đơn hàng không kiểm tra được tồn kho.
- **Cách khắc phục:** Mở lại Terminal 2, trong thư mục `Django_Learning\product_service` chạy `python manage.py runserver 8001`.

### 8. Mọi request `/orders`, `/order_items` nhận `503 Service Unavailable` (Bài 4)
- **Nguyên nhân:** Service xác thực (Terminal 1 chạy `runserver 8000`) đã bị tắt hoặc chưa khởi động — middleware của Service đơn hàng không gọi được `GET /auth`.
- **Cách khắc phục:** Mở lại Terminal 1, trong thư mục `Django_Learning` chạy `python manage.py runserver 8000` — Service đơn hàng phụ thuộc Service xác thực theo đúng kiến trúc SOA.

---

## 👨‍💻 THÔNG TIN DỰ ÁN & TÁC GIẢ

- **Đơn vị đào tạo:** Bộ môn Mạng máy tính & Truyền thông / Kỹ thuật Phần mềm
- **Môn học:** Phát triển Ứng dụng Phân tán & Web Services (RESTful API)
- **Tài liệu tham chiếu:** [BÀI THỰC HÀNH SỐ 1.pdf](file:///d:/CODES/Py/Django_Learning/docs/B%C3%80I%20TH%E1%BB%B0C%20H%C3%80NH%20S%E1%BB%90%201.pdf) và [BÀI THỰC HÀNH SỐ 2.pdf](file:///d:/CODES/Py/Django_Learning/docs/B%C3%80I%20TH%E1%BB%B0C%20H%C3%80NH%20S%E1%BB%90%202.pdf) và [BÀI THỰC HÀNH SỐ 3.pdf](file:///d:/CODES/Py/Django_Learning/docs/B%C3%80I%20TH%E1%BB%B0C%20H%C3%80NH%20S%E1%BB%90%203.pdf) và [BÀI THỰC HÀNH SỐ 4.pdf](file:///d:/CODES/Py/Django_Learning/docs/B%C3%80I%20TH%E1%BB%B0C%20H%C3%80NH%20S%E1%BB%90%204.pdf)
