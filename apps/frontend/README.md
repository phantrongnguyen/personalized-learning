# 🖥️ EduRisk AI — Frontend Dashboard

Giao diện Single Page Application (SPA) chuyên nghiệp dành cho hệ thống dự đoán và can thiệp nguy cơ học tập cá nhân hóa.

---

## 🚀 Điểm Nổi Bật

- **Kiến trúc SPA thuần (Vanilla HTML5 / CSS3 / ES6+ JavaScript)**: Không phụ thuộc framework cồng kềnh, tải trang tức thì.
- **Điều hướng Hash Router**: Hỗ trợ chuyển đổi mượt mà giữa các trang:
  - `/#home`: Trang chủ & giới thiệu chỉ số KPI mô hình.
  - `/#dashboard`: Bảng điều khiển phân tích 17 đặc trưng, xem đồng hồ đo SVG Gauge và đề xuất can thiệp.
  - `/#about`: Thông tin chi tiết thuật toán lai HCO-VNLS, mô hình LightGBM và mốc Cutoff 75%.
  - `/#contact`: Form liên hệ, thông tin kết nối và FAQ dạng Accordion.
- **Xác thực người dùng (Auth)**:
  - Modal Đăng nhập / Đăng ký hiện đại.
  - Tài khoản Demo 1-Click: Cố vấn học tập & Quản trị viên.
  - Lưu phiên đăng nhập an toàn trong `localStorage`.
- **Phân tích nguy cơ & Can thiệp**:
  - Hỗ trợ nạp nhanh các mẫu hồ sơ (*Sinh viên yếu*, *Sinh viên tốt*, *Đặt lại*).
  - Tự động sinh danh sách khuyến nghị hành vi kèm nút sao chép (Copy) 1-click.
  - Lưu trữ lịch sử phân tích trong phiên, hỗ trợ lọc theo từ khóa và **Xuất file báo cáo CSV**.
- **Giám sát kết nối (Live Ping Monitor)**: Đèn trạng thái hiển thị thời gian thực độ trễ API và hỗ trợ đổi URL backend linh hoạt.
- **Hệ thống Toast Notification**: Thông báo nổi góc màn hình (Success, Warning, Error, Info) tự động tắt sau 3.5 giây.

---

## 📂 Cấu Trúc Thư Mục

```text
frontend/
├── index.html        # Khung giao diện HTML5 chuẩn ngữ nghĩa đa phân hệ
├── css/
│   └── style.css     # Thiết kế Pro SaaS, biến màu CSS, SVG Gauge, Responsive
└── js/
    └── app.js        # Controller: SPA router, Form renderer, API caller, Auth store, CSV
```

---

## 🏃 Cách Chạy Giao Diện

### Cách 1 (Khuyến nghị — Chạy tích hợp từ Backend)
Khi bạn chạy backend FastAPI, giao diện đã được mount sẵn tại địa chỉ:
👉 **[http://127.0.0.1:8000/app/](http://127.0.0.1:8000/app/)**

### Cách 2 (Mở độc lập qua Live Server / Static Server)
Khởi động máy chủ tĩnh:
```bash
python -m http.server 5500
# Mở trình duyệt tại: http://127.0.0.1:5500
```
*Lưu ý: Đảm bảo ô **Backend** ở góc trên bên phải được trỏ chính xác về `http://127.0.0.1:8000`.*
