# TÀI LIỆU HƯỚNG DẪN TRIỂN KHAI HỆ THỐNG DOCKER
### Hệ Thống Gợi Ý Chiến Lược Học Tập Cá Nhân Hóa (KLTN 13 - HUIT)

Tài liệu này cung cấp hướng dẫn toàn diện từ A đến Z dành cho các thành viên phát triển, người đánh giá hoặc quản trị viên hệ thống để có thể tự triển khai toàn bộ môi trường cơ sở dữ liệu và các dịch vụ của đề tài **KLTN 13** bằng Docker một cách nhanh chóng, chuẩn xác.

---

## 📌 1. TỔNG QUAN HỆ THỐNG DOCKER

Môi trường Docker của dự án được cấu hình bằng Docker Compose, bao gồm các thành phần:

```
                                  ┌─────────────────────────────┐
                                  │       TRÌNH DUYỆT WEB       │
                                  │      (Người dùng / Dev)     │
                                  └──────────────┬──────────────┘
                                                 │
                   Port 5050                     │ Port 5433
         ┌───────────────────────────────────────┴───────────────────────────────────────┐
         │                                                                               │
         ▼                                                                               ▼
┌──────────────────┐                                                           ┌──────────────────┐
│  kltn13_pgadmin  │                                                           │ kltn13_postgres  │
│  (pgAdmin 4 GUI) │ ──── [Mạng nội bộ Docker: host='postgres', port=5432] ───►│ (PostgreSQL 15)  │
└──────────────────┘                                                           └─────────┬────────┘
                                                                                         │ Mount
                                                                               ┌─────────▼────────┐
                                                                               │  Volume Dữ Liệu  │
                                                                               │ (postgres_data)  │
                                                                               └──────────────────┘
```

* **`kltn13_postgres` (PostgreSQL 15 Alpine):** Hệ quản trị cơ sở dữ liệu quan hệ chính. Tự động khởi tạo 14 bảng chuẩn 3NF, các chỉ mục tối ưu hóa và dữ liệu hạt giống ban đầu (Roles, Admin, ML Model, Courses).
* **`kltn13_pgadmin` (pgAdmin 4):** Bảng điều khiển giao diện trực quan trên nền Web để quản trị, tra cứu và trực quan hóa dữ liệu.
* **`kltn13_backend` & `kltn13_frontend`:** Các dịch vụ API FastAPI và giao diện người dùng (sẵn sàng kết nối qua mạng nội bộ Docker).

---

## 💻 2. YÊU CẦU TIÊN QUYẾT (PREREQUISITES)

Trước khi bắt đầu, hãy đảm bảo máy tính của bạn đã cài đặt các công cụ sau:
1. **Docker Desktop** (khuyến nghị phiên bản 24.x trở lên, hỗ trợ Docker Compose v2).
   * Tải về tại: [https://www.docker.com/products/docker-desktop/](https://www.docker.com/products/docker-desktop/)
   * Đảm bảo Docker Desktop đang ở trạng thái **Running** (biểu tượng cá voi xanh).
2. **Git** (để clone mã nguồn dự án).
3. Hệ điều hành: Windows 10/11 (bật WSL2), macOS hoặc Linux (Ubuntu, Debian, Fedora...).

---

## 📂 3. CẤU TRÚC THƯ MỤC DOCKER

```text
docker/
├── README.md                           # Tài liệu hướng dẫn triển khai này
├── postgres/
│   ├── .gitkeep
│   └── init-scripts/                   # Tự động nạp tuần tự khi CSDL khởi tạo lần đầu
│       ├── 01_init_schema.sql          # DDL tạo Extensions, 14 bảng 3NF & 8 Indexes
│       └── 02_seed_data.sql            # Nạp Roles, User Admin, ML Model, Môn học OULAD
├── backend/
│   └── Dockerfile                      # Khung Dockerfile cho API Backend FastAPI
└── frontend/
    └── .gitkeep                        # Khung triển khai giao diện Frontend
```

---

## 🚀 4. HƯỚNG DẪN TRIỂN KHAI TỪNG BƯỚC

### Bước 1: Mở Terminal tại thư mục gốc dự án
```bash
# Di chuyển vào thư mục dự án
cd kltn13-personalized-learning-recommendation
```

### Bước 2: Thiết lập tệp cấu hình môi trường (`.env`)
Nếu bạn mới clone mã nguồn về và chưa có file `.env`, hãy sao chép từ file mẫu `.env.example`:

* **Trên Windows PowerShell:**
  ```powershell
  Copy-Item .env.example .env
  ```
* **Trên Linux / macOS:**
  ```bash
  cp .env.example .env
  ```

Kiểm tra các biến môi trường quan trọng trong `.env`:
```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=123
POSTGRES_DB=personalized_learning_db
POSTGRES_HOST_PORT=5433
POSTGRES_CONTAINER_PORT=5432
DATABASE_URL=postgresql://postgres:123@localhost:5433/personalized_learning_db
DOCKER_DATABASE_URL=postgresql://postgres:123@postgres:5432/personalized_learning_db

PGADMIN_PORT=5050
PGADMIN_DEFAULT_EMAIL=admin@huit.edu.vn
PGADMIN_DEFAULT_PASSWORD=admin_secret_pass
```

> ⚠️ **Lưu ý quan trọng về Cổng (Port):**  
> Dự án thiết lập cổng ngoài máy Host là **`5433`** nhằm phòng tránh việc xung đột nếu máy tính của bạn đã cài sẵn một dịch vụ PostgreSQL cục bộ đang lắng nghe trên cổng mặc định `5432`.

### Bước 3: Khởi chạy các dịch vụ CSDL bằng Docker Compose
Chạy lệnh sau để Docker tự động tải Image, tạo Network, tạo Volume và khởi động các container ở chế độ chạy ngầm (`-d`):

```bash
docker compose up -d postgres pgadmin
```

> **Cơ chế tự động hóa (Auto-Initialization):**  
> Khi chạy lần đầu, container PostgreSQL sẽ tự động mount thư mục `docker/postgres/init-scripts/` vào `/docker-entrypoint-initdb.d/` để thực thi:  
> 1. `01_init_schema.sql`: Kích hoạt `uuid-ossp`, `pgcrypto`, tạo toàn bộ 14 bảng và các index tối ưu truy vấn.  
> 2. `02_seed_data.sql`: Nạp 4 vai trò, tài khoản quản trị mặc định, metadata mô hình LightGBM Cutoff 75% và các học phần OULAD.

### Bước 4: Kiểm tra trạng thái hoạt động
Kiểm tra xem các container đã khởi động thành công và đạt trạng thái "Healthy" chưa:

```bash
docker compose ps
```
Hoặc:
```bash
docker ps --filter "name=kltn13"
```

**Kết quả mong đợi:**
| Container Name | Image | Trạng thái (Status) | Cổng mở ngoài Host |
| :--- | :--- | :--- | :--- |
| `kltn13_postgres` | `postgres:15-alpine` | `Up ... (healthy)` | `0.0.0.0:5433->5432/tcp` |
| `kltn13_pgadmin` | `dpage/pgadmin4:latest`| `Up ...` | `0.0.0.0:5050->80/tcp` |

---

## 🔑 5. THÔNG TIN TRUY CẬP & ĐĂNG NHẬP

### 1. Kết nối vào Cơ sở dữ liệu PostgreSQL
* **Host:** `localhost` hoặc `127.0.0.1`
* **Port:** **`5433`** *(Dành cho công cụ ngoài host: DBeaver, Navicat, TablePlus, Backend)*
* **Port nội bộ Docker:** `5432` *(Dành cho các container kết nối với nhau)*
* **Database:** `personalized_learning_db`
* **Username:** `postgres`
* **Password:** `123`
* **Connection String:**
  ```text
  postgresql://postgres:123@localhost:5433/personalized_learning_db
  ```

### 2. Giao diện Web Quản trị pgAdmin 4
* **Đường dẫn truy cập:** [http://localhost:5050](http://localhost:5050)
* **Email đăng nhập:** `admin@huit.edu.vn`
* **Mật khẩu:** `admin_secret_pass`
* **Cách thêm Server vào pgAdmin (làm 1 lần duy nhất):**
  1. Chuột phải vào **Servers** $\rightarrow$ **Register** $\rightarrow$ **Server...**
  2. Tab **General** $\rightarrow$ Name: `KLTN13 Postgres`
  3. Tab **Connection**:
     * Host name / address: `postgres` *(lưu ý: gõ đúng chữ postgres, không dùng localhost)*
     * Port: `5432`
     * Maintenance database: `personalized_learning_db`
     * Username: `postgres`
     * Password: `123`
     * Tích chọn **Save password?**
  4. Nhấn **Save**.

### 3. Tài khoản Quản trị ứng dụng (Seed sẵn trong bảng `users`)
* **Email:** `admin@huit.edu.vn`
* **Mật khẩu ban đầu:** `admin_password_123`
* **Vai trò:** `ADMIN`

---

## 🛠️ 6. CÁC LỆNH VẬN HÀNH & BẢO TRÌ THƯỜNG DÙNG

### Truy cập psql CLI trực tiếp trong container:
```bash
docker exec -it kltn13_postgres psql -U postgres -d personalized_learning_db
```
*(Gõ `\dt` để xem bảng, `\q` để thoát)*

### Xem Logs container khi gặp sự cố:
```bash
# Xem log PostgreSQL
docker logs -f kltn13_postgres

# Xem log pgAdmin
docker logs -f kltn13_pgadmin
```

### Tạm dừng các container (tiết kiệm RAM/CPU khi nghỉ làm việc):
```bash
docker compose stop postgres pgadmin
```

### Khởi động lại các container đã dừng:
```bash
docker compose start postgres pgadmin
```

### Sao lưu (Backup) toàn bộ CSDL ra file `.sql`:
```bash
# Trên Windows PowerShell
docker exec -t kltn13_postgres pg_dump -U postgres personalized_learning_db > ./database/backup_$(Get-Date -Format "yyyyMMdd").sql

# Trên Linux / macOS
docker exec -t kltn13_postgres pg_dump -U postgres personalized_learning_db > ./database/backup_$(date +%Y%m%d).sql
```

### Phục hồi (Restore) CSDL từ file `.sql`:
```bash
# Trên Windows PowerShell
Get-Content ./database/backup_file.sql | docker exec -i kltn13_postgres psql -U postgres -d personalized_learning_db

# Trên Linux / macOS
cat ./database/backup_file.sql | docker exec -i kltn13_postgres psql -U postgres -d personalized_learning_db
```

### Xóa toàn bộ và khởi tạo lại CSDL từ đầu (Reset Database):
> ⚠️ **Cảnh báo:** Lệnh này sẽ xóa sạch dữ liệu trong volume và chạy lại toàn bộ script khởi tạo ban đầu!
```bash
# Dừng container và xóa bỏ volume dữ liệu
docker compose down -v

# Khởi động lại mới
docker compose up -d postgres pgadmin
```

---

## ❓ 7. XỬ LÝ SỰ CỐ THƯỜNG GẶP (TROUBLESHOOTING)

#### 1. Lỗi: `Bind for 0.0.0.0:5433 failed: port is already allocated`
* **Nguyên nhân:** Cổng `5433` trên máy bạn đang có một chương trình khác sử dụng.
* **Cách xử lý:** Mở file `.env`, đổi `POSTGRES_HOST_PORT` thành một cổng khác (ví dụ: `5434` hoặc `54321`), sau đó chạy lại `docker compose up -d postgres`.

#### 2. Lỗi pgAdmin: `Unable to connect to server: could not translate host name "localhost" to address`
* **Nguyên nhân:** Khi tạo Server trong pgAdmin, bạn đã điền Host là `localhost`. Do pgAdmin chạy trong container riêng nên `localhost` sẽ trỏ về chính nó chứ không phải container PostgreSQL.
* **Cách xử lý:** Điền **Host name/address** là `postgres` (tên dịch vụ trong docker network).

#### 3. Container `kltn13_postgres` liên tục báo trạng thái `unhealthy`
* **Nguyên nhân:** Có thể câu lệnh kiểm tra healthcheck chưa xác thực được do sai user hoặc DB name.
* **Cách xử lý:** Chạy `docker logs kltn13_postgres` để xem thông báo lỗi chi tiết. Đảm bảo biến `POSTGRES_USER` và `POSTGRES_DB` khớp nhau giữa `.env` và `docker-compose.yml`.

---
*Khoa Luận Tốt Nghiệp KLTN 13 — Trường Đại học Công Thương TP.HCM (HUIT)*
