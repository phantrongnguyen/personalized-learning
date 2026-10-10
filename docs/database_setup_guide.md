# HƯỚNG DẪN CHI TIẾT KHỞI ĐỘNG VÀ TRUY CẬP DATABASE POSTGRESQL DOCKER
### Hệ Thống Gợi Ý Chiến Lược Học Tập Cá Nhân Hóa (KLTN 13 - HUIT)

Tài liệu này hướng dẫn chi tiết từng bước cách khởi động hệ quản trị cơ sở dữ liệu **PostgreSQL 15** và công cụ quản trị **pgAdmin 4** bằng Docker, cùng 4 cách truy cập vào cơ sở dữ liệu để làm việc và kiểm tra dữ liệu.

---

## 📌 BẢNG THÔNG SỐ KẾT NỐI HỆ THỐNG

| Thông số | Giá trị kết nối từ Máy thật (Windows Host) | Giá trị kết nối Nội bộ Docker (Container) |
| :--- | :--- | :--- |
| **Host / IP** | `localhost` hoặc `127.0.0.1` | `postgres` |
| **Cổng (Port)** | **`5433`** *(Tránh xung đột port 5432 trên Windows)* | **`5432`** |
| **Database Name** | `personalized_learning_db` | `personalized_learning_db` |
| **Username** | `postgres` | `postgres` |
| **Password** | `123` | `123` |
| **pgAdmin 4 Web** | `http://localhost:5050` | `http://pgadmin:80` |
| **pgAdmin Login** | Email: `admin@huit.edu.vn`<br>Mật khẩu: `admin_secret_pass` | — |

---

## BƯỚC 1: KHỞI ĐỘNG DATABASE BẰNG DOCKER COMPOSE

### 1.1. Yêu cầu tiên quyết
Đảm bảo phần mềm **Docker Desktop** trên máy tính đang được mở và đang chạy (biểu tượng cá voi màu xanh lá cây ở khay hệ thống).

### 1.2. Mở Terminal / PowerShell
Mở **PowerShell** hoặc Terminal tại thư mục gốc của dự án:
```powershell
cd y:\study\sv4_hk1\kltn13-personalized-learning-recommendation
```

### 1.3. Lệnh khởi động Container
Chạy lệnh sau để khởi động 2 dịch vụ CSDL PostgreSQL và giao diện web pgAdmin ở chế độ chạy ngầm (`-d`):

```powershell
docker compose up -d postgres pgadmin
```

> **Ghi chú:**  
> - Khi chạy lần đầu, Docker sẽ tự động mount thư mục `docker/postgres/init-scripts/` để chạy `01_init_schema.sql` (tạo 14 bảng, indexes) và `02_seed_data.sql` (tạo vai trò, tài khoản admin, model ML, môn học OULAD).  
> - Dữ liệu được lưu trữ bền vững trong Docker Volume `postgres_data`, không bị mất khi tắt máy.

### 1.4. Kiểm tra trạng thái hoạt động
Chạy lệnh kiểm tra container:
```powershell
docker ps --filter "name=kltn13"
```
Kết quả hiển thị:
* Container `kltn13_postgres` có trạng thái: **`Up ... (healthy)`**
* Container `kltn13_pgadmin` có trạng thái: **`Up ...`**

Nếu muốn xem nhật ký hoạt động (Logs) của PostgreSQL:
```powershell
docker logs -f kltn13_postgres
```
*(Nhấn `Ctrl + C` để thoát màn hình xem log)*

---

## BƯỚC 2: CÁC CÁCH TRUY CẬP VÀO DATABASE

Bạn có thể chọn 1 trong 4 cách dưới đây tùy theo nhu cầu làm việc:

---

### CÁCH 1: TRUY CẬP TRỰC TIẾP QUA DÒNG LỆNH (PSQL CLI TRONG DOCKER)
*Cách này nhanh nhất, không cần cài bất kỳ phần mềm quản trị CSDL nào.*

#### 1. Mở giao diện `psql`:
Chạy lệnh sau trong PowerShell:
```powershell
docker exec -it kltn13_postgres psql -U postgres -d personalized_learning_db
```
Màn hình dòng lệnh chuyển sang giao diện psql:
```text
psql (15.18)
Type "help" for help.

personalized_learning_db=#
```

#### 2. Các câu lệnh thao tác cơ bản:
* **Xem toàn bộ danh sách 14 bảng:**
  ```sql
  \dt
  ```
* **Xem cấu trúc chi tiết của một bảng (các cột, kiểu dữ liệu, khóa ngoại):**
  ```sql
  \d users
  \d student_feature_snapshots
  \d prediction_runs
  ```
* **Chạy câu lệnh truy vấn SQL kiểm tra dữ liệu:**
  ```sql
  -- Xem danh sách vai trò
  SELECT * FROM roles;

  -- Xem tài khoản Quản trị viên mặc định
  SELECT id, email, full_name, is_active FROM users;

  -- Xem thông tin mô hình Machine Learning Cutoff 75%
  SELECT model_name, version, threshold, cutoff_fraction FROM ml_models;

  -- Xem danh sách môn học mẫu OULAD
  SELECT code_module, name, credits_default FROM courses;
  ```
* **Thoát khỏi psql về lại PowerShell:**
  ```sql
  \q
  ```

---

### CÁCH 2: TRUY CẬP QUA GIAO DIỆN WEB PGADMIN 4
*Dành cho người thích giao diện trực quan, dễ bấm chuột xem bảng và xuất dữ liệu ra Excel/CSV.*

#### Bước 2.1: Mở trình duyệt Web
Mở Chrome / Edge / Firefox và nhập đường link:
👉 **`http://localhost:5050`**

#### Bước 2.2: Đăng nhập pgAdmin
* **Email:** `admin@huit.edu.vn`
* **Password:** `admin_secret_pass`
* Nhấn **Login**.

#### Bước 2.3: Đăng ký kết nối đến PostgreSQL (Chỉ làm lần đầu)
1. Ở cây thư mục bên trái, chuột phải vào **Servers** $\rightarrow$ Chọn **Register** $\rightarrow$ **Server...**
2. **Tại tab "General":**
   * Ô **Name:** Nhập tên gợi nhớ, ví dụ: `KLTN13 Postgres`
3. **Tại tab "Connection":**
   * **Host name/address:** Nhập `postgres` *(do pgAdmin và Postgres cùng nằm trong mạng Docker)*
   * **Port:** Nhập `5432`
   * **Maintenance database:** Nhập `personalized_learning_db`
   * **Username:** Nhập `postgres`
   * **Password:** Nhập `123`
   * Tích chọn ô **Save password?**
4. Nhấn **Save**.

#### Bước 2.4: Xem và truy vấn dữ liệu trên pgAdmin
* Điều hướng theo cây thư mục bên trái:  
  `Servers` $\rightarrow$ `KLTN13 Postgres` $\rightarrow$ `Databases` $\rightarrow$ `personalized_learning_db` $\rightarrow$ `Schemas` $\rightarrow$ `public` $\rightarrow$ `Tables`.
* Bạn sẽ thấy danh sách toàn bộ **14 bảng dữ liệu**.
* Để truy vấn: Chuột phải vào bất kỳ bảng nào $\rightarrow$ Chọn **View/Edit Data** $\rightarrow$ **All Rows**.
* Để tự gõ câu lệnh SQL: Nhấn vào biểu tượng **Query Tool** (hình tam giác/bút) trên thanh công cụ.

---

### CÁCH 3: KẾT NỐI BẰNG CÁC PHẦN MỀM NGOÀI MÁY HOST (DBeaver, Navicat, DataGrip, VS Code)
*Nếu máy tính của bạn đã cài sẵn DBeaver, TablePlus, Navicat hoặc tiện ích mở rộng VS Code Database Client.*

* **Connection Type:** `PostgreSQL`
* **Host:** `localhost` hoặc `127.0.0.1`
* **Port:** **`5433`** *(Lưu ý: Phải là 5433, KHÔNG dùng 5432)*
* **Database:** `personalized_learning_db`
* **Username:** `postgres`
* **Password:** `123`
* Nhấn **Test Connection** $\rightarrow$ Kết nối thành công $\rightarrow$ Nhấn **Finish**.

---

### CÁCH 4: KẾT NỐI TỪ ỨNG DỤNG BACKEND FASTAPI (PYTHON)

Khi phát triển mã nguồn Backend, chuỗi kết nối (Connection String) được cấu hình tùy theo môi trường chạy:

#### 1. Khi Backend chạy trực tiếp từ Terminal trên máy Host:
Trong file `.env`:
```env
DATABASE_URL=postgresql://postgres:123@localhost:5433/personalized_learning_db
```
Đoạn mã Python kiểm tra kết nối với SQLAlchemy:
```python
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://postgres:123@localhost:5433/personalized_learning_db"
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    result = conn.execute(text("SELECT version();"))
    print("PostgreSQL Version:", result.fetchone()[0])
```

#### 2. Khi Backend chạy đóng gói bằng Docker Container:
Trong file `docker-compose.yml`:
```yaml
environment:
  - DATABASE_URL=postgresql://postgres:123@postgres:5432/personalized_learning_db
```

---

## BƯỚC 3: CÁC LỆNH QUẢN TRỊ THƯỜNG DÙNG

### 1. Tạm dừng các container (khi không làm việc):
```powershell
docker compose stop postgres pgadmin
```

### 2. Khởi động lại các container:
```powershell
docker compose start postgres pgadmin
```

### 3. Khởi động lại toàn bộ dịch vụ (Restart):
```powershell
docker compose restart postgres
```

### 4. Sao lưu (Backup) dữ liệu CSDL ra file SQL:
Chạy lệnh sau để xuất toàn bộ dữ liệu ra file `.sql`:
```powershell
docker exec -t kltn13_postgres pg_dump -U postgres personalized_learning_db > ./database/backup_data.sql
```

### 5. Phục hồi (Restore) dữ liệu từ file SQL:
```powershell
Get-Content ./database/backup_data.sql | docker exec -i kltn13_postgres psql -U postgres -d personalized_learning_db
```

### 6. Xóa sạch và tái tạo CSDL từ đầu (Reset Database):
> ⚠️ **Lưu ý:** Lệnh này sẽ xóa toàn bộ dữ liệu hiện tại trong volume và chạy lại từ đầu các script trong `init-scripts/`.
```powershell
# Dừng container và xóa volume
docker compose down -v

# Khởi chạy lại mới tinh
docker compose up -d postgres pgadmin
```

---

## 🛠️ XỬ LÝ SỰ CỐ THƯỜNG GẶP (TROUBLESHOOTING)

| Hiện tượng | Nguyên nhân | Cách xử lý |
| :--- | :--- | :--- |
| `Error response from daemon: Ports are not available: exposing port TCP 0.0.0.0:5432` | Cổng 5432 bị chiếm bởi service Windows Postgres | Kiểm tra file `.env` đã đặt `POSTGRES_HOST_PORT=5433` chưa. Kết nối từ ngoài máy tính phải dùng port `5433`. |
| `psql: error: connection to server on socket ... failed` | Container Postgres chưa sẵn sàng | Kiểm tra `docker ps`, đợi khoảng 5-10 giây để container đạt trạng thái `(healthy)`. |
| `pgAdmin không kết nối được đến server postgres` | Nhập Host là `localhost` bên trong pgAdmin container | Trong màn hình cấu hình pgAdmin, ô **Host name/address** phải điền là `postgres` (tên service trong docker-compose), không điền `localhost`. |
| Không thấy các bảng sau khi khởi động lại | Docker container bị tạo lại trên volume khác | Dữ liệu được bảo toàn tự động qua volume `postgres_data`. Đảm bảo không dùng cờ `-v` khi chạy lệnh `docker compose down`. |
