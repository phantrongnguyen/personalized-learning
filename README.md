# 🎓 EduRisk AI — Nền Tảng Dự Đoán & Can Thiệp Nguy Cơ Học Tập Cá Nhân Hóa

> **Đề tài:** Dự báo nguy cơ học tập và gợi ý chiến lược học tập cá nhân hóa  
> **Thuật toán cốt lõi:** Human Conception Optimization (HCO) cải tiến kết hợp Variable Neighborhood Local Search (VNLS) tuyển chọn đặc trưng trên các họ mô hình Boosting (LightGBM, CatBoost, XGBoost)  
> **Tập dữ liệu chuẩn:** Open University Learning Analytics Dataset (OULAD) — hơn 32.500 hồ sơ học tập  
> **Đơn vị:** Trường Đại học Công Thương TP.HCM (HUIT) — Khoa Công nghệ Thông tin & Khoa học Dữ liệu  
> **Mã đề tài:** KLTN 13  
> **Giảng viên hướng dẫn:** ThS. Nguyễn Thị Thùy Trang (`trangntthuy@huit.edu.vn`)  
> **Sinh viên thực hiện:**  
> - Phan Trọng Nguyên (MSSV: 2045230068)  
> - Nguyễn Gia Bảo (MSSV: 2045230010)  
> - Võ Bạch Kim Thịnh (MSSV: 2045230096)  

[![Python](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.3-61dafb.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.7-3178c6.svg)](https://www.typescriptlang.org/)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3.4-38bdf8.svg)](https://tailwindcss.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.64.0-FF4B4B.svg)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Institution](https://img.shields.io/badge/HUIT-Khoa%20CNTT-orange.svg)](https://huit.edu.vn/)
[![Status](https://img.shields.io/badge/Status-Synchronized%20Local-brightgreen.svg)](#)

---

## 📌 1. Giới Thiệu Dự Án (Overview)

Trong môi trường giáo dục trực tuyến và đại học hiện đại (EdTech & LMS), người học đối mặt với nhiều rào cản: thiếu kỷ luật tự giác, bắt nhịp chậm ở giai đoạn đầu kỳ, tương tác VLE ngắt quãng và nộp bài trễ hạn. Việc thiếu cơ chế cảnh báo sớm dẫn đến tỷ lệ học viên bỏ học (*Dropout*) hoặc thi trượt (*Fail*) luôn ở mức cao.

Dự án **EduRisk AI — Hệ thống gợi ý chiến lược học tập cá nhân hóa** ứng dụng khai phá dữ liệu giáo dục (Educational Data Mining - EDM) kết hợp giải thuật tối ưu hóa thông minh mô phỏng sinh học **Human Conception Optimization (HCO)** cải tiến với **Variable Neighborhood Local Search (VNLS)** nhằm chuyển dịch mạnh mẽ từ **Phân tích dự đoán (Predictive Analytics)** sang **Kê đơn giải pháp (Prescriptive Analytics)**:

1. **Lựa chọn đặc trưng tối ưu (Feature Selection):** Khắc phục *Lời nguyền số chiều* ($D=34$ thuộc tính hành vi và nhân khẩu học) từ dữ liệu hành vi sinh viên trên OULAD, loại bỏ từ 72% đến 86% số chiều dữ liệu dư thừa/nhiễu.
2. **Dự báo nguy cơ học tập sớm:** Phân loại nhị phân chính xác học viên có nguy cơ rớt môn hoặc bỏ học (*At-Risk* vs *Successful*) tại các mốc thời gian vàng quan sát sớm (Cutoff 50% và Cutoff 75% chu kỳ học kỳ).
3. **Đề xuất chiến lược can thiệp sư phạm cá nhân hóa:** Phân tích khoảng cách năng lực (*Gap Analysis*) và đối sánh qua biểu đồ **Radar Competency Chart** 6 chiều so với chuẩn học viên giỏi (Top 25%), tự động kê đơn kế hoạch hành động cụ thể kèm mục tiêu định lượng đo lường được (tăng click tài nguyên, cải thiện hạn nộp, ôn tập bài tập cụ thể).

---

## 🎯 2. Tiến Độ & Kết Quả Hoàn Thành (Implementation Status)

Hệ thống đã được hiện thực hóa trọn gói theo kiến trúc Monorepo tiêu chuẩn công nghiệp:

- [x] **Khảo sát & Cơ sở lý thuyết chuyên sâu:** Hoàn thiện cơ sở toán học thuật toán **HCO** (Acharya & Das, 2022) với biên dạng vận tốc Poiseuille, cơ chế siêu hoạt hóa Cauchy (Cauchy hyperactivation), và **VNLS** (Hansen et al., 2017) với 4 cấu trúc lân cận $\mathcal{N}_1 \dots \mathcal{N}_4$.
- [x] **Dữ liệu chuẩn OULAD:** Thu thập và tích hợp toàn diện 7 bảng của bộ dữ liệu quốc tế **Open University Learning Analytics Dataset** (32.593 bản ghi sinh viên, hơn 10 triệu bản ghi tương tác VLE), thiết lập mốc Cutoff 50% và 75% chu kỳ học kỳ.
- [x] **Pipeline Tiền xử lý & Kỹ thuật đặc trưng vector hóa:** Xử lý giá trị khuyết thiếu, mã hóa biến phân loại, trích xuất đặc trưng đa chiều (điểm bài tập có trọng số, độ trễ hạn, clickstream theo mốc thời gian tuần 1–4, giữa kỳ, cuối kỳ) lưu tại `packages/ml/src/features/` và `packages/ml/src/preprocessing/`.
- [x] **Cài đặt & Thực nghiệm thuật toán đề xuất HCO-VNLS:**
  - Cài đặt **HCO thuần túy** với cơ chế chọn lọc dịch nhầy và pha siêu hoạt hóa bằng phân phối Cauchy.
  - Cài đặt **VNLS** với 4 toán tử lân cận ($1\text{-flip}$, $2\text{-flip}$, Bit Swap, Feature Drop).
  - Cài đặt **Lai ghép HCO-VNLS** cân bằng tối ưu giữa Khám phá toàn cục (Exploration) và Khai thác cục bộ (Exploitation).
- [x] **Thực nghiệm Benchmark đối chứng toàn diện:**
  - Đối chứng với **Genetic Algorithm (GA)** và **Particle Swarm Optimization (PSO)**.
  - Thực nghiệm 24 kịch bản đối chứng trên 3 họ Boosting (**LightGBM, CatBoost, XGBoost**) tại Cutoff 50% và 75%, kiểm chứng tính ổn định của mask đặc trưng, export 16 baseline models kèm SHA-256 manifest.
- [x] **Động cơ Gợi ý Chiến lược Học tập Cá nhân hóa & Radar 6D:** Xây dựng `LearningRecommendationEngine` và `radar_service.py` so sánh độ lệch hành vi của sinh viên nguy cơ so với chuẩn vị nhóm tích cực để sinh khuyến nghị hành động cụ thể theo 4 nhóm luật sư phạm G01–G04.
- [x] **Đóng gói & Phân phối Mô hình (Artifacts):** Lưu trữ model trọng số (`.joblib`), metadata (`.json`), schema 30 cột đầu vào LightGBM tại `apps/backend/artifacts/` và `streamlit-web/`.
- [x] **Hệ thống Web Service RESTful API (FastAPI Backend Clean Architecture):**
  - Cơ sở dữ liệu quan hệ PostgreSQL 15 với 14 bảng vật lý (`docker/postgres/init-scripts/`).
  - Xác thực bảo mật JWT, mã hóa bcrypt, phân quyền vai trò (Role-Based Access Control: `STUDENT`, `LECTURER`, `ADVISOR`, `ADMIN`).
  - Bộ kiểm thử tự động pytest đạt 100% test case pass (`test_auth.py`, `test_sprint3.py`, `test_sprint4.py`, `test_sprint5.py`).
- [x] **Giao diện Người dùng Hiện đại:**
  - **React 18 + TypeScript + Tailwind CSS SPA** (`apps/frontend/`): Đầy đủ các phân hệ `StudentPage`, `LecturerPage`, `AdvisorPage`, `AdminUsersPage`, `DashboardPage`, `ProfilePage`, đồng hồ đo rủi ro SVG Risk Gauge và biểu đồ Radar năng lực.
  - **Ứng dụng Demo Streamlit** (`streamlit-web/` và `CLHT_GB_GITHUB/NghienCuu_HCO_VNLS/main_app/`): Hỗ trợ trực quan hóa nhanh các kịch bản suy luận và kiểm tra cây quyết định LightGBM.
- [x] **Học thuật & Báo cáo Tốt nghiệp:** Báo cáo tiến độ chuẩn thể thức HUIT (`BaoCaoTienDo_KLTN_13_9-10.docx`), bài toán tính tay tường minh $D=6$, 38 tài liệu tham khảo chuẩn IEEE.

---

## 🔬 3. Cơ Sở Toán Học Thuật Toán Đề Xuất (HCO-VNLS)

```
┌─────────────────────────────────────────────────────────┐
│        1. Khởi tạo Quần thể Phối tử (Binary Pop)        │
│          Xi ∈ {0, 1}^D qua hàm truyền Sigmoid           │
└───────────────────────────┬─────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────┐
│     2. Đánh giá Hàm thích nghi Đa mục tiêu (Fitness)    │
│   Fitness(x) = α · F1_Score + (1 - α) · (1 - |x| / D)   │
└───────────────────────────┬─────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────┐
│    3. Tìm kiếm Cục bộ VNLS quanh Cá thể Tốt nhất        │
│    (Toán tử 1-flip, 2-flip, Bit Swap, Feature Drop)     │
└───────────────────────────┬─────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────┐
│     4. Cập nhật Vị trí & Vận tốc Poiseuille / Cauchy    │
│       Hội tụ về Tập Đặc trưng Tinh gọn Tối ưu           │
└─────────────────────────────────────────────────────────┘
```

### Hàm Thích Nghi Tuyển Chọn Đặc Trưng (Fitness Function)

$$\text{Fitness}(x) = \alpha \cdot F_1(X_x, y) + (1 - \alpha) \cdot \left(1 - \frac{\sum_{i=1}^D x_i}{D}\right)$$

* $\alpha = 0.85$: Trọng số ưu tiên năng lực phân loại của mô hình máy học ($F_1\text{-score}$).
* $1 - \alpha = 0.15$: Trọng số tối ưu hóa độ tinh gọn tập đặc trưng (Feature Parsimony).

### 4 Cấu Trúc Lân Cận VNLS
1. **$\mathcal{N}_1$ (1-Flip):** Đảo ngẫu nhiên 1 bit đặc trưng ($0 \leftrightarrow 1$) — thăm dò vi mô cục bộ.
2. **$\mathcal{N}_2$ (2-Flip):** Đảo đồng thời 2 bit đặc trưng — mở rộng bán kính khai thác.
3. **$\mathcal{N}_3$ (Bit Swap):** Hoán đổi 1 bit $1$ và 1 bit $0$ — giữ nguyên kích thước tập biến nhưng thăm dò cấu hình tương tác khác.
4. **$\mathcal{N}_4$ (Feature Drop):** Tắt ngẫu nhiên 1 bit đang bật ($1 \to 0$) — triệt tiêu biến dư thừa nhằm tối ưu thành phần phạt số chiều $(1 - |x|/D)$.

---

## 📊 4. Kết Quả Thực Nghiệm Đối Chứng (Benchmark Results)

### So sánh các thuật toán tối ưu hóa (trên tập kiểm thử độc lập)

| Phương Pháp Tối Ưu | Số Đặc Trưng Chọn | Tỷ Lệ Giảm Thuộc Tính (%) | Accuracy | F1-Score | ROC-AUC |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Baseline (Tất cả đặc trưng)** | 30 / 30 | 0.0% | 93.04% | 0.9304 | 0.9799 |
| **Genetic Algorithm (GA)** | 12 / 30 | 60.0% | 91.84% | 0.9184 | 0.9727 |
| **Particle Swarm Optimization (PSO)** | 5 / 30 | 83.3% | 93.02% | 0.9303 | 0.9783 |
| **HCO Thuần túy** | 12 / 30 | 60.0% | 93.39% | 0.9339 | 0.9810 |
| **HCO-VNLS Đề Xuất** | **4 / 30** | **86.7%** | **93.04%** | **0.9304** | **0.9785** |

> **Đóng góp khoa học:** Thuật toán lai **HCO-VNLS** giảm được **86.7% số chiều dữ liệu** (chỉ giữ lại 4 đặc trưng then chốt nhất) mà hiệu năng phân loại vẫn tương đương với mô hình sử dụng toàn bộ 30 thuộc tính, giúp hệ thống suy luận thời gian thực với độ trễ cực thấp.

### So sánh 3 bộ học Boosting tại Cutoff 75%
* **LightGBM (Mô hình triển khai chính):** Tối ưu nhất về tốc độ huấn luyện dạng cây histogram, đạt cân bằng cao giữa Precision, Recall và ROC-AUC khi kết hợp mask tuyển chọn từ HCO-VNLS.
* **CatBoost & XGBoost (Đối chứng kiểm tra chéo):** Xác nhận các thuộc tính được HCO-VNLS lựa chọn mang tính ổn định cao trên cả 3 họ mô hình, loại bỏ rủi ro over-fitting vào một thuật toán boosting duy nhất.

---

## 📂 5. Cấu Trúc Thư Mục Dự Án (Monorepo Architecture)

```text
personalized-learning/
├── apps/                               # CÁC ỨNG DỤNG ĐẦU CUỐI
│   ├── backend/                        # API Server với FastAPI (Python 3.12)
│   │   ├── api/v1/endpoints/           # Router: auth, student, lecturer, advisor, admin
│   │   ├── core/                       # config, database, security, permissions
│   │   ├── models/                     # SQLAlchemy models (14 bảng PostgreSQL)
│   │   ├── repositories/               # Repository pattern truy vấn CSDL
│   │   ├── schemas/                    # Pydantic schemas xác thực request/response
│   │   ├── services/                   # Business logic: auth, radar, audit, prediction
│   │   ├── tests/                      # Bộ kiểm thử tự động pytest (test_auth, sprint3-5)
│   │   └── main.py                     # Entry point FastAPI, CORS & Static mount
│   │
│   └── frontend/                       # Modern React 18 SPA (TypeScript + Vite + Tailwind)
│       ├── dist/                       # Bản đóng gói sản xuất (phục vụ tại /app)
│       ├── legacy/                     # Bản sao lưu phiên bản Vanilla HTML/CSS/JS cũ
│       ├── src/
│       │   ├── components/             # Sidebar, Navbar, Footer, RiskGauge, RadarChart...
│       │   ├── pages/                  # StudentPage, LecturerPage, AdvisorPage, AdminUsersPage...
│       │   ├── services/               # api.ts (Axios API client), admin.ts
│       │   ├── state/AppContext.tsx    # State management toàn cục (Auth, Ping, History)
│       │   ├── utils/                  # recommendations.ts, csv.ts
│       │   ├── App.tsx                 # Root layout & Hash router
│       │   └── main.tsx                # React DOM entry point
│       ├── package.json
│       ├── vite.config.ts
│       └── tailwind.config.js
│
├── packages/                           # CÁC GÓI MÃ NGUỒN DÙNG CHUNG
│   ├── ml/                             # Gói Machine Learning & Tối ưu hóa cốt lõi
│   │   ├── artifacts/                  # Serialized models, scalers, encoders
│   │   └── src/
│   │       ├── features/               # Kỹ thuật đặc trưng vector hóa OULAD
│   │       ├── preprocessing/          # DataPipeline làm sạch, mã hóa, chuẩn hóa
│   │       ├── optimization/           # hco.py, vnls.py, hco_vnls.py, baselines.py
│   │       └── models/recommendation/  # Recommendation Engine
│   │
│   └── shared/                         # Schemas và Constants dùng chung toàn monorepo
│       ├── constants/fields.ts         # 17 features OULAD, Presets SV yếu/tốt, Benchmarks
│       └── types/student.ts            # TypeScript interfaces cho Feature, User, Prediction
│
├── streamlit-web/                      # ỨNG DỤNG DEMO STREAMLIT ĐỘC LẬP
│   ├── app.py                          # Streamlit UI trực quan
│   └── model_hco_vnls_lightgbm_cutoff75.joblib
│
├── CLHT_GB_GITHUB/                     # PHÂN HỆ NGHIÊN CỨU THỰC NGHIỆM CHUYÊN SÂU
│   └── NghienCuu_HCO_VNLS/             # Chuỗi 7 notebook nghiên cứu & 16 baseline models
│       ├── mo_hinh/                    # DANH_SACH_16_MODEL.csv, manifest_sha256.csv
│       ├── main_app/                   # Streamlit web app nâng cao kèm Radar & Theme HUIT
│       └── ket_qua/                    # Log thực nghiệm, metrics đối chứng
│
├── docker/                             # HẠ TẦNG DOCKER & DATABASE
│   ├── docker-compose.yml              # PostgreSQL 15 & pgAdmin4 orchestration
│   └── postgres/init-scripts/          # 01_init_schema.sql (14 bảng), 02_seed_data.sql
│
├── bao_cao/                            # TÀI LIỆU VÀ BÁO CÁO TIẾN ĐỘ
│   ├── BaoCaoTienDo_KLTN_13_9-10.docx  # Báo cáo tiến độ hoàn chỉnh ngày 09/10/2026
│   └── KLTN13_Chuong1_Chuong2.docx     # Bản thảo chi tiết Chương 1 & Chương 2
│
├── requirements.txt                    # Danh mục thư viện Python
└── README.md                           # Tài liệu tổng quan dự án
```

---

## 🚀 6. Hướng Dẫn Cài Đặt & Khởi Chạy (Quickstart)

### Bước 1: Chuẩn bị môi trường Python & Cài đặt phụ thuộc

```bash
# Tạo và kích hoạt môi trường ảo Python 3.12+
python -m venv venv

# Windows (PowerShell):
.\venv\Scripts\activate
# Linux / macOS:
source venv/bin/activate

# Cài đặt các thư viện Python
pip install -r requirements.txt
```

---

### Bước 2: Khởi chạy Hạ tầng Database (Docker)

```bash
# Khởi động PostgreSQL 15 và pgAdmin4
docker compose up -d

# Tự động nạp schema 14 bảng và tài khoản kiểm thử mặc định:
# Student: student@huit.edu.vn / Student@123
# Lecturer: lecturer@huit.edu.vn / Lecturer@123
# Advisor: advisor@huit.edu.vn / Advisor@123
# Admin: admin@huit.edu.vn / Admin@123
```

---

### Bước 3: Khởi chạy Backend API Server (FastAPI)

```bash
cd apps/backend
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

* **Swagger UI API Documentation:** 👉 **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)**
* **Kiểm tra Health Endpoint:** 👉 **[http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health)**
* **Giao diện Web tích hợp:** 👉 **[http://127.0.0.1:8000/app/](http://127.0.0.1:8000/app/)**

---

### Bước 4: Phát triển & Đóng gói Giao diện Frontend (React + Vite)

```bash
cd apps/frontend

# Cài đặt dependencies (React 18, Vite, Tailwind CSS, Lucide)
npm install

# Khởi động máy chủ dev (Port 5173, proxy tự động sang API 8000)
npm run dev
```
👉 Mở trình duyệt tại: **`http://localhost:5173/`**

Khi cần đóng gói sản xuất để mount trực tiếp vào FastAPI:
```bash
npm run build
# Bản build sẽ được xuất tự động vào thư mục apps/frontend/dist/
```

---

### Bước 5: Khởi chạy Web Demo Streamlit (Tùy chọn)

```bash
# Giao diện Streamlit cơ bản:
python -m streamlit run streamlit-web/app.py

# Giao diện Streamlit nghiên cứu nâng cao của Bảo:
python -m streamlit run CLHT_GB_GITHUB/NghienCuu_HCO_VNLS/main_app/app.py
```

---

## 🛡️ 7. Tiêu Chuẩn Bảo Mật & Pháp Lý (Security & Compliance)

* **Bảo vệ quyền riêng tư học viên:** Tuân thủ các nguyên tắc **FERPA**, **GDPR** và Nghị định 13/2023/NĐ-CP; mọi suy luận AI đều thực hiện trên vector đặc trưng hành vi ẩn danh.
* **Mã hóa & Xác thực:** Toàn bộ dữ liệu truyền tải qua TLS 1.3, mật khẩu băm chuẩn bcrypt, phiên làm việc bảo vệ bởi JSON Web Token (JWT) và RBAC 4 cấp độ.
* **Tương thích EdTech:** Hỗ trợ chuẩn **IMS LTI 1.3 Advantage** tích hợp hai chiều với Moodle và Canvas LMS.

---

## 👥 8. Thông Tin Đề Tài & Bản Quyền

* **Đề tài:** Hệ Thống Gợi Ý Chiến Lược Học Tập Cá Nhân Hóa (KLTN 13)
* **Cơ quan chủ quản:** Khoa Công Nghệ Thông Tin – Trường Đại học Công Thương TP.HCM (HUIT)
* **Giảng viên hướng dẫn:** ThS. Nguyễn Thị Thùy Trang (`trangntthuy@huit.edu.vn`)
* **Sinh viên thực hiện:**
  - Phan Trọng Nguyên (MSSV: 2045230068)
  - Nguyễn Gia Bảo (MSSV: 2045230010)
  - Võ Bạch Kim Thịnh (MSSV: 2045230096)
* **Giấy phép:** [MIT License](LICENSE) © 2026 HUIT.
