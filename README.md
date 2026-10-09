# 🎓 EduRisk AI — Nền Tảng Dự Đoán & Can Thiệp Nguy Cơ Học Tập Cá Nhân Hóa

> **Thuật toán cốt lõi:** Human Conception Optimization (HCO) cải tiến kết hợp Variable Neighborhood Local Search (VNLS)  
> **Kiến trúc mô hình:** LightGBM Classifier tại mốc quan sát Cutoff 75%  
> **Tập dữ liệu chuẩn:** Open University Learning Analytics Dataset (OULAD) — hơn 32.500 hồ sơ học tập  
> **Phiên bản:** v2.4 Enterprise Edition  

[![Python](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.3-61dafb.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.7-3178c6.svg)](https://www.typescriptlang.org/)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3.4-38bdf8.svg)](https://tailwindcss.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen.svg)](#)

---

## 📌 1. Giới Thiệu Dự Án (Overview)

Trong môi trường giáo dục trực tuyến và đại học hiện đại (EdTech & LMS), người học đối mặt với nhiều rào cản: thiếu kỷ luật tự giác, bắt nhịp chậm ở giai đoạn đầu kỳ, tương tác VLE ngắt quãng và nộp bài trễ hạn. Việc thiếu cơ chế cảnh báo sớm dẫn đến tỷ lệ học viên bỏ học (*Dropout*) hoặc thi trượt (*Fail*) luôn ở mức cao.

**EduRisk AI** giải quyết bài toán trên bằng cách chuyển dịch mạnh mẽ từ **Phân tích dự đoán (Predictive Analytics)** sang **Kê đơn giải pháp (Prescriptive Analytics)**:
1. **Lựa chọn đặc trưng tối ưu (Feature Selection):** Ứng dụng giải thuật phỏng sinh học lai **HCO-VNLS** loại bỏ hơn 72% – 86% số chiều dữ liệu dư thừa/nhiễu từ nhật ký hành vi LMS.
2. **Dự báo nguy cơ học tập thời gian thực:** Phân loại nhị phân chính xác học viên có nguy cơ rớt môn hoặc bỏ học (*At-Risk* vs *Safe*) tại thời điểm vàng **Cutoff 75%** trước kỳ thi.
3. **Đề xuất chiến lược can thiệp sư phạm cá nhân hóa:** Phân tích khoảng cách năng lực (*Gap Analysis*) và đối sánh qua biểu đồ **Radar Competency Chart** so với chuẩn học viên giỏi, tự động kê đơn kế hoạch hành động cụ thể kèm mục tiêu định lượng đo lường được.

---

## 🎯 2. Tiến Độ & Kết Quả Hoàn Thành (Implementation Status)

Hệ thống đã được hiện thực hóa trọn gói theo kiến trúc Monorepo tiêu chuẩn công nghiệp:

- [x] **Khảo sát & Nghiên cứu lý thuyết:** Tổng hợp các tài liệu học thuật về Phân tích học tập (Learning Analytics), cơ sở toán học thuật toán **HCO** (Acharya & Das, 2022) và **VNLS** (Hansen et al., 2017) lưu trữ tại `docs/architecture/` và `docs/data/`.
- [x] **Dữ liệu thực tế OULAD:** Thu thập và tích hợp toàn diện 7 bảng của bộ dữ liệu chuẩn quốc tế **Open University Learning Analytics Dataset** (32.593 bản ghi sinh viên, hơn 10 triệu bản ghi tương tác VLE).
- [x] **Pipeline Tiền xử lý & Kỹ thuật đặc trưng vector hóa:** Xử lý missing values, chuẩn hóa phân loại, trích xuất đặc trưng đa chiều (điểm bài tập có trọng số, độ trễ hạn, clickstream theo mốc thời gian) lưu tại `packages/ml/src/features/engineering.py` và `packages/ml/src/preprocessing/pipeline.py`.
- [x] **Cài đặt thuật toán tối ưu hóa cải tiến HCO-VNLS:**
  - Cài đặt **HCO thuần túy** (`packages/ml/src/optimization/hco.py`): Cơ chế chọn lọc dịch nhầy và pha siêu hoạt hóa (Hyperactivation) bằng nhiễu Cauchy.
  - Cài đặt **VNLS** (`packages/ml/src/optimization/vnls.py`): Toán tử $1\text{-flip}$, $2\text{-flip}$, Bit Swap và Feature Drop.
  - Cài đặt **Lai ghép HCO-VNLS** (`packages/ml/src/optimization/hco_vnls.py`): Cân bằng tối ưu giữa Thăm dò toàn cục (Exploration) và Khai thác cục bộ (Exploitation).
- [x] **Mô hình đối chứng Benchmark:** Cài đặt đối chứng đầy đủ với **Genetic Algorithm (GA)** và **Particle Swarm Optimization (PSO)** (`packages/ml/src/optimization/baselines.py`).
- [x] **Mô hình Gợi ý Chiến lược Học tập Cá nhân hóa:** Xây dựng `LearningRecommendationEngine` (`packages/ml/src/models/recommendation/engine.py`) so sánh điểm lệch hành vi so với nhóm khá giỏi để sinh lộ trình can thiệp hành động thực tế.
- [x] **Đóng gói & Lưu trữ Mô hình (Artifacts):** Serialize model pipeline (`.joblib`), metadata đặc trưng và ngưỡng phân loại tại `apps/backend/artifacts/` và `packages/ml/artifacts/`.
- [x] **Chuỗi 3 Jupyter Notebooks Thực Nghiệm Hoàn Chỉnh:** 
  1. [`01_data_understanding.ipynb`](notebooks/01_data_understanding.ipynb): Khám phá phân phối dữ liệu và trích xuất đặc trưng.
  2. [`02_hco_vnls_model_and_recommendation.ipynb`](notebooks/02_hco_vnls_model_and_recommendation.ipynb): Thực nghiệm Benchmark so sánh GA, PSO, HCO, HCO-VNLS và phân tích hội tụ.
  3. [`03_save_and_load_best_model.ipynb`](notebooks/03_save_and_load_best_model.ipynb): Đóng gói, sanity check nạp model và mô phỏng suy luận.
- [x] **Tích hợp Web Service RESTful API (FastAPI Backend):** Xây dựng server FastAPI với kiến trúc tách lớp Clean Architecture (`api/`, `core/`, `ml/`, `schemas/`, `services/`), phục vụ các endpoint `/api/v1/health`, `/api/v1/predictions/` và tự động mount Static SPA tại `/app/`.
- [x] **Giao diện Người dùng Hiện đại (React 18 + TypeScript + Tailwind CSS SPA):**
  - **Sidebar cánh trái** hỗ trợ thu gọn/mở rộng, định tuyến nhanh giữa **Dashboard** và **Hồ sơ chuyên gia (Profile)**.
  - **Dashboard**: Nhập 17 đặc trưng học tập theo nhóm, nạp mẫu thử nghiệm SV Yếu/Tốt, hiển thị đồng hồ **Radial Risk Gauge** SVG và biểu đồ **Radar Competency Chart** đối sánh chuẩn năng lực.
  - **Kê đơn can thiệp**: Tự động sinh danh sách hành động theo mức độ ưu tiên (High / Medium / Low) kèm nút sao chép 1-click.
  - **Lịch sử & Xuất báo cáo**: Quản lý lịch sử phân tích trong phiên và xuất báo cáo CSV có UTF-8 BOM hiển thị tiếng Việt chuẩn trên Excel.
  - **Hồ sơ chuyên gia & Cài đặt (`/profile`)**: Quản lý thông tin cố vấn, giám sát số ca rủi ro và mã tích hợp LMS API Key (chuẩn LTI 1.3).
  - **Giám sát kết nối**: Đèn trạng thái Live Ping Monitor đo độ trễ API theo thời gian thực.
  - **Footer chuẩn doanh nghiệp**: Dải đăng ký nhận tin, điều hướng đa cột, trạng thái hệ thống SLA 99.9% và liên kết pháp lý bảo mật (ISO 27001, GDPR, FERPA).

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
│     4. Cập nhật Vận tốc & Vị trí HCO (Mucus Guidance)   │
│     + Pha Siêu hoạt hóa Hyperactivation (Nhiễu Cauchy)  │
└───────────────────────────┬─────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────┐
│     5. Trích xuất Tập đặc trưng Tối ưu & Suy luận       │
└─────────────────────────────────────────────────────────┘
```

### Hàm Mục Tiêu Đa Tiêu Chí (Fitness Function)
$$\text{Fitness}(x) = \alpha \cdot F_1(X_x, y) + (1 - \alpha) \cdot \left(1 - \frac{\sum_{i=1}^D x_i}{D}\right)$$
* $\alpha = 0.85$: Tối đa hóa chất lượng phân loại và độ tin cậy $F_1\text{-score}$.
* $1 - \alpha = 0.15$: Khuyến khích loại bỏ thuộc tính dư thừa, tối ưu hóa kích thước mô hình (Feature Parsimony).

---

## 📊 4. Kết Quả Thực Nghiệm Đối Chứng (Benchmark Results)

Kết quả đánh giá trên tập kiểm thử độc lập gồm **6.519 sinh viên** (tách 20% độc lập từ tập OULAD đã trích xuất):

| Phương Pháp Tối Ưu | Số Đặc Trưng Chọn | Tỷ Lệ Giảm Thuộc Tính (%) | Accuracy | F1-Score | ROC-AUC |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Baseline (Tất cả đặc trưng)** | 30 / 30 | 0.0% | 93.04% | 0.9304 | 0.9799 |
| **Genetic Algorithm (GA)** | 12 / 30 | 60.0% | 91.84% | 0.9184 | 0.9727 |
| **Particle Swarm Optimization (PSO)** | 5 / 30 | 83.3% | 93.02% | 0.9303 | 0.9783 |
| **HCO Thuần túy** | 12 / 30 | 60.0% | 93.39% | 0.9339 | 0.9810 |
| **HCO-VNLS Đề Xuất** | **4 / 30** | **86.7%** | **93.04%** | **0.9304** | **0.9785** |

> **Đóng góp khoa học:** Thuật toán lai **HCO-VNLS** giảm được **86.7% số chiều dữ liệu** (chỉ giữ lại 4 đặc trưng then chốt nhất) mà hiệu năng phân loại vẫn tương đương với mô hình sử dụng toàn bộ 30 thuộc tính, giúp hệ thống suy luận thời gian thực với độ trễ cực thấp.

---

## 📂 5. Cấu Trúc Thư Mục Dự Án (Monorepo Architecture)

```text
kltn13-personalized-learning-recommendation/
├── apps/                               # CÁC ỨNG DỤNG ĐẦU CUỐI
│   ├── backend/                        # API Server với FastAPI (Python 3.12)
│   │   ├── api/v1/endpoints/           # Router health.py, predictions.py
│   │   ├── artifacts/                  # Model LightGBM & Scaler đã serialize (.joblib)
│   │   ├── core/config.py              # Cấu hình Pydantic BaseSettings
│   │   ├── ml/                         # model_loader.py, predictor.py
│   │   ├── schemas/                    # Pydantic schemas cho đầu vào/đầu ra
│   │   ├── services/                   # Prediction service layer
│   │   └── main.py                     # Entry point FastAPI, CORS & StaticFiles mount
│   │
│   └── frontend/                       # Modern React 18 SPA (TypeScript + Vite + Tailwind)
│       ├── dist/                       # Bản đóng gói sản xuất (phục vụ tại /app)
│       ├── legacy/                     # Bản sao lưu phiên bản Vanilla HTML/CSS/JS cũ
│       ├── src/
│       │   ├── components/
│       │   │   ├── common/             # Sidebar.tsx, Navbar.tsx, Footer.tsx, Modals, Toast
│       │   │   ├── dashboard/          # FeatureForm.tsx, RiskGauge.tsx, HistoryTable.tsx
│       │   │   └── recommendation/     # RadarCompetencyChart.tsx, InterventionList.tsx
│       │   ├── pages/                  # HomePage, DashboardPage, ProfilePage, AboutPage, ContactPage
│       │   ├── services/api.ts         # Axios/Fetch API client kết nối backend
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
│   │       ├── features/engineering.py # Trích xuất 30 đặc trưng OULAD
│   │       ├── preprocessing/          # DataPipeline làm sạch, mã hóa, chuẩn hóa
│   │       ├── optimization/           # hco.py, vnls.py, hco_vnls.py, baselines.py
│   │       └── models/recommendation/  # engine.py (Recommendation Engine)
│   │
│   └── shared/                         # Schemas và Constants dùng chung toàn monorepo
│       ├── constants/fields.ts         # 17 features OULAD, Presets SV yếu/tốt, Benchmarks
│       └── types/student.ts            # TypeScript interfaces cho Feature, User, Prediction
│
├── data/                               # QUẢN TRỊ DỮ LIỆU
│   ├── raw/                            # 7 bảng CSV OULAD thô (studentInfo, studentVle...)
│   └── processed/                      # oulad_features_engineered.csv (Dữ liệu sạch)
│
├── notebooks/                          # 3 NOTEBOOKS THỰC NGHIỆM KHOA HỌC
│   ├── 01_data_understanding.ipynb
│   ├── 02_hco_vnls_model_and_recommendation.ipynb
│   └── 03_save_and_load_best_model.ipynb
│
├── docs/                               # TÀI LIỆU HỌC THUẬT & BÁO CÁO KIẾN TRÚC
├── docker-compose.yml
├── requirements.txt
└── README.md
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

### Bước 2: Khởi chạy Backend API Server (FastAPI)

```bash
cd apps/backend
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

* **Swagger UI API Documentation:** 👉 **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)**
* **Kiểm tra Health Endpoint:** 👉 **[http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health)**
* **Giao diện Web Frontend tích hợp (FastAPI Static Mount):** 👉 **[http://127.0.0.1:8000/app/](http://127.0.0.1:8000/app/)**

---

### Bước 3: Phát triển & Đóng gói Giao diện Frontend (React + Vite)

Nếu bạn muốn tùy biến giao diện với chế độ Hot Module Replacement (HMR):

```bash
cd apps/frontend

# Cài đặt dependencies (React, Vite, Tailwind CSS, Lucide)
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

### Bước 4: Chạy chuỗi Notebook thực nghiệm khoa học (Tùy chọn)

```bash
jupyter lab
```
Mở tuần tự các notebook trong thư mục `notebooks/`:
1. `01_data_understanding.ipynb`: Trích xuất và tiền xử lý dữ liệu OULAD.
2. `02_hco_vnls_model_and_recommendation.ipynb`: Tối ưu chọn đặc trưng và đối chứng GA/PSO/HCO/HCO-VNLS.
3. `03_save_and_load_best_model.ipynb`: Sanity check nạp model và mô phỏng suy luận.

---

## 🛡️ 7. Tiêu Chuẩn Bảo Mật & Pháp Lý (Security & Compliance)

* **Bảo vệ quyền riêng tư học viên:** Tuân thủ các nguyên tắc **FERPA**, **GDPR** và Nghị định 13/2023/NĐ-CP; mọi suy luận AI đều thực hiện trên vector đặc trưng hành vi ẩn danh.
* **Mã hóa:** Toàn bộ dữ liệu truyền tải qua giao thức TLS 1.3 và lưu trữ mã hóa chuẩn AES-256.
* **Tương thích EdTech:** Hỗ trợ chuẩn **IMS LTI 1.3 Advantage** tích hợp hai chiều với Moodle và Canvas LMS.
* **Giấy phép:** Mã nguồn được phát hành theo giấy phép [MIT License](LICENSE).
* **Bản quyền:** &copy; 2026 EduRisk AI Systems. All rights reserved.
