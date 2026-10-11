# 🖥️ EduRisk AI — Modern React Frontend SPA

Giao diện Single Page Application (SPA) chuẩn công nghiệp dành cho hệ thống dự đoán và can thiệp nguy cơ học tập cá nhân hóa (**EduRisk AI Platform Enterprise Edition**).

Được xây dựng trên nền tảng **React 18 + TypeScript + Vite + Tailwind CSS**, tích hợp trực tiếp với Backend **FastAPI** và chia sẻ kiểu dữ liệu với package `packages/shared`.

---

## 🚀 Điểm Nổi Bật & Tính Năng

- **Công nghệ Hiện Đại**: React 18, TypeScript nghiêm ngặt, Tailwind CSS v3, Vite 6 và icon Lucide.
- **Chia sẻ Schemas & Types toàn dự án**: Tận dụng triệt để `packages/shared/types` và `packages/shared/constants` làm Single Source of Truth cho 17 đặc trưng học tập OULAD.
- **Biểu Đồ Đối Sánh Năng Lực (Radar Competency Chart)**: Biểu đồ mạng nhện SVG tương tác độ phân giải cao, so sánh sinh viên với trung vị chuẩn của nhóm đạt Pass/Distinction trên 6 trục sư phạm.
- **Đồng Hồ Đo Nguy Cơ (Radial Risk Gauge)**: Đồng hồ đo rủi ro sinh động bằng SVG, hiệu ứng gradient và phân loại nhãn rủi ro (Nguy cơ cao / An toàn).
- **Kê Đơn Can Thiệp Sư Phạm (Prescriptive Interventions)**: Tự động phân tích điểm yếu (chuyên cần, hạn nộp, tỷ lệ ngày học, khối lượng tín chỉ), gắn nhãn độ ưu tiên (High / Medium / Low) và nút sao chép 1-click.
- **Quản Lý Lịch Sử & Xuất CSV**: Lưu trữ tự động các lần dự đoán trong phiên, hỗ trợ tìm kiếm/lọc từ khóa, xóa bản ghi và xuất báo cáo CSV có UTF-8 BOM hiển thị chuẩn tiếng Việt trên Excel.
- **Quản Trị Phiên Đăng Nhập (Auth State)**: Hỗ trợ tài khoản Demo 1-Click (Cố vấn học tập, Quản trị viên) và form Đăng nhập / Đăng ký.
- **Giám Sát & Điều Chỉnh Backend Linh Hoạt**: Live Ping Monitor đo độ trễ API thời gian thực, kiểm tra trạng thái model LightGBM và cho phép đổi URL host API mà không cần build lại mã nguồn.

---

## 📂 Cấu Trúc Thư Mục

```text
apps/frontend/
├── index.html                   # Entry point HTML cho Vite
├── package.json                 # Scripts và dependencies (React 18, TypeScript, Tailwind, Lucide)
├── vite.config.ts               # Cấu hình Vite với alias (@ và @shared), dev proxy, relative base
├── tailwind.config.js           # Cấu hình Theme, Palette và Typography
├── tsconfig.json                # TypeScript compiler config với alias tới packages/shared
│
├── dist/                        # Production build (tự động mount vào FastAPI tại /app)
│   ├── index.html
│   └── assets/
│
├── src/
│   ├── main.tsx                 # Khởi tạo React DOM Root
│   ├── App.tsx                  # Layout khung, Điều hướng view và Global Modals
│   ├── index.css                # Tailwind directives & Custom animations
│   │
│   ├── components/
│   │   ├── common/
│   │   │   ├── Sidebar.tsx            # Thanh điều hướng cánh trái (Dashboard, Profile, thu phóng)
│   │   │   ├── Navbar.tsx             # Thanh tiêu đề trên, Breadcrumbs & Ping indicator
│   │   │   ├── Footer.tsx             # Chân trang & Thông tin bản quyền ISO/IEC 27001
│   │   │   ├── ToastContainer.tsx     # Thông báo nổi động (Success, Warning, Error, Info)
│   │   │   ├── AuthModal.tsx          # Modal Đăng nhập/Đăng ký & Demo 1-Click
│   │   │   └── BackendStatusModal.tsx # Cấu hình URL backend & kiểm tra trạng thái model
│   │   ├── dashboard/
│   │   │   ├── FeatureForm.tsx        # Form 17 đặc trưng theo 3 nhóm tab & Preset SV Yếu / Tốt
│   │   │   ├── RiskGauge.tsx          # Đồng hồ đo xác suất rủi ro bằng SVG Radial Dial
│   │   │   └── HistoryTable.tsx       # Bảng lịch sử, bộ lọc tìm kiếm & nút Xuất CSV
│   │   └── recommendation/
│   │       ├── InterventionList.tsx   # Danh sách giải pháp can thiệp kèm mục tiêu & Copy
│   │       └── RadarCompetencyChart.tsx # Biểu đồ Radar đối sánh chuẩn sinh viên Giỏi
│   │
│   ├── pages/
│   │   ├── HomePage.tsx               # Trang chủ, Hero banner, chỉ số KPI mô hình
│   │   ├── DashboardPage.tsx          # Trang phân tích 2 cột chính
│   │   ├── AboutPage.tsx              # Giới thiệu kiến trúc giải pháp HCO-VNLS & bảng so sánh
│   │   ├── ContactPage.tsx            # Thông tin liên hệ tư vấn doanh nghiệp & FAQ Accordion
│   │   └── ProfilePage.tsx            # Hồ sơ chuyên gia cố vấn, thống kê ca rủi ro & LMS API Key
│   │
│   ├── services/
│   │   └── api.ts                     # API client gọi /health và /predictions/ kèm timeout
│   ├── state/
│   │   └── AppContext.tsx             # Quản lý State toàn cục (User, History, Ping, Toasts)
│   └── utils/
│       ├── recommendations.ts         # Bộ sinh khuyến nghị can thiệp sư phạm
│       └── csv.ts                     # Hàm xuất dữ liệu CSV kèm UTF-8 BOM
│
└── legacy/                      # Bản sao lưu phiên bản Vanilla HTML/CSS/JS cũ
```

---

## 🏃 Hướng Dẫn Khởi Chạy

### 1. Chạy trong Môi Trường Phát Triển (Development with HMR)

Cài đặt phụ thuộc và khởi động Vite dev server:
```bash
cd apps/frontend
npm install
npm run dev
```
Trình duyệt mở tại: **`http://localhost:5173/`**  
*(Vite đã được cấu hình proxy tự động chuyển tiếp request `/api` sang backend `http://127.0.0.1:8000`).*

### 2. Đóng Gói Sản Phẩm (Production Build)

Biên dịch ứng dụng TypeScript sang thư mục `dist/`:
```bash
cd apps/frontend
npm run build
```

### 3. Chạy Tích Hợp Trực Tiếp từ Backend FastAPI

Khi khởi chạy backend:
```bash
cd apps/backend
uvicorn main:app --reload
```
FastAPI sẽ tự động phát hiện và phục vụ toàn bộ thư mục `apps/frontend/dist/` tại:  
👉 **[http://127.0.0.1:8000/app/](http://127.0.0.1:8000/app/)**
