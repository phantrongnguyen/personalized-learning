# Hệ Thống Gợi Ý Chiến Lược Học Tập Cá Nhân Hóa

> **Thuật toán:** Human Conception Optimization (HCO) cải tiến kết hợp Variable Neighborhood Local Search (VNLS)  
> **Đơn vị:** Trường Đại học Công Thương TP.HCM (HUIT)  
> **Mã đề tài:** KLTN 13  
> **Giảng viên hướng dẫn:** ThS. Nguyễn Thị Thùy Trang (trangntthuy@huit.edu.vn)  

[![Python](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Institution](https://img.shields.io/badge/HUIT-Khoa%20CNTT-orange.svg)](https://huit.edu.vn/)
[![Status](https://img.shields.io/badge/Status-Core%20Algorithms%20Completed-brightgreen.svg)](#)

---

## 📌 1. Giới Thiệu Dự Án (Overview)

Trong kỷ nguyên giáo dục số (EdTech và E-Learning), mỗi sinh viên có tốc độ tiếp thu, thời gian biểu và thói quen tương tác trên hệ thống quản lý học tập (LMS) hoàn toàn khác nhau. Việc thiếu sự theo dõi và can thiệp kịp thời dẫn đến tỷ lệ sinh viên bỏ học (Dropout) hoặc rớt môn cao.

Dự án **Hệ thống gợi ý chiến lược học tập cá nhân hóa** ứng dụng khai phá dữ liệu giáo dục (Educational Data Mining) kết hợp giải thuật tối ưu hóa thông minh mô phỏng sinh học **Human Conception Optimization (HCO)** cải tiến với **Variable Neighborhood Local Search (VNLS)** nhằm:
1. **Lựa chọn đặc trưng tối ưu (Feature Selection):** Loại bỏ các đặc trưng dư thừa/nhiễu từ dữ liệu hành vi sinh viên.
2. **Dự báo nguy cơ học tập:** Phân loại sớm sinh viên có nguy cơ rớt môn hoặc bỏ học (*At-Risk* vs *Successful*).
3. **Đề xuất chiến lược học tập cá nhân hóa:** Đưa ra các giải pháp can thiệp cụ thể (tăng giờ tự học, đổi phương pháp học, tham gia diễn đàn, khắc phục trễ hạn bài tập) theo từng điểm yếu của mỗi sinh viên.

---

## 🎯 2. Tiến Độ & Kết Quả Thực Hiện Yêu Cầu Đồ Án (Project Progress)

Hệ thống đã hoàn thành các nội dung và yêu cầu cốt lõi theo đề cương khóa luận:

- [x] **Khảo sát & Nghiên cứu lý thuyết:** Tổng hợp các tài liệu học thuật về Phân tích học tập (Learning Analytics), cơ sở toán học thuật toán **HCO** (Acharya & Das, 2022) và **VNLS** (Hansen et al., 2017) lưu trữ tại `docs/architecture/` và `docs/data/`.
- [x] **Dữ liệu thực tế OULAD:** Thu thập và tích hợp toàn diện 7 bảng của bộ dữ liệu chuẩn quốc tế **Open University Learning Analytics Dataset** (32.593 bản ghi sinh viên, hơn 10 triệu bản ghi tương tác VLE).
- [x] **Pipeline Tiền xử lý & Kỹ thuật đặc trưng vector hóa:** Xử lý missing values, chuẩn hóa phân loại, trích xuất 29 đặc trưng đa chiều (điểm bài tập có trọng số, độ trễ hạn, clickstream theo mốc thời gian tuần 1–4, giữa kỳ, cuối kỳ) lưu tại `packages/ml/src/features/engineering.py` và `packages/ml/src/preprocessing/pipeline.py`.
- [x] **Cài đặt thuật toán tối ưu hóa cải tiến HCO-VNLS:**
  - Cài đặt **HCO thuần túy** (`packages/ml/src/optimization/hco.py`): Cơ chế chọn lọc dịch nhầy cổ tử cung và pha siêu hoạt hóa (Hyperactivation).
  - Cài đặt **VNLS** (`packages/ml/src/optimization/vnls.py`): Toán tử $1\text{-flip}$, $2\text{-flip}$, Bit Swap và Feature Drop.
  - Cài đặt **Lai ghép HCO-VNLS** (`packages/ml/src/optimization/hco_vnls.py`): Cân bằng tối ưu giữa Thăm dò toàn cục (Exploration) và Khai thác cục bộ (Exploitation).
- [x] **Mô hình đối chứng Benchmark:** Cài đặt đầy đủ giải thuật di truyền **Genetic Algorithm (GA)** và bầy đàn **Particle Swarm Optimization (PSO)** (`packages/ml/src/optimization/baselines.py`).
- [x] **Mô hình Gợi ý Chiến lược Học tập Cá nhân hóa:** Xây dựng `LearningRecommendationEngine` (`packages/ml/src/models/recommendation/engine.py`) so sánh điểm lệch hành vi so với nhóm khá giỏi để sinh lộ trình can thiệp hành động thực tế.
- [x] **Đóng gói & Lưu trữ Mô hình (Artifacts):** Lưu trữ model trọng số (`.joblib`), pipeline (`.joblib`), cấu hình mask đặc trưng (`.json`) và ngưỡng gợi ý (`.json`) tại `packages/ml/artifacts/`.
- [x] **Chuỗi 3 Jupyter Notebooks Thực Nghiệm Hoàn Chỉnh:** 
  1. [`01_data_understanding.ipynb`](notebooks/01_data_understanding.ipynb): Khám phá phân phối dữ liệu và trích xuất đặc trưng.
  2. [`02_hco_vnls_model_and_recommendation.ipynb`](notebooks/02_hco_vnls_model_and_recommendation.ipynb): Thực nghiệm Benchmark so sánh GA, PSO, HCO, HCO-VNLS và vẽ biểu đồ Radar.
  3. [`03_save_and_load_best_model.ipynb`](notebooks/03_save_and_load_best_model.ipynb): Đóng gói, nạp lại model và mô phỏng suy luận thời gian thực.
- [ ] **Tích hợp Web Service RESTful API (FastAPI Backend):** Đã có khung máy chủ tại `apps/backend/` (đang tiến hành kết nối router).
- [ ] **Giao diện Người dùng (Frontend UI/UX):** Dashboard sinh viên, biểu đồ phân tích và tra cứu lộ trình học tập.

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
│     + Pha Siêu hoạt hóa Hyperactivation khi gần đích    │
└───────────────────────────┬─────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────┐
│     5. Trích xuất Tập đặc trưng Tối ưu & Gợi ý          │
└─────────────────────────────────────────────────────────┘
```

### Hàm Mục Tiêu (Fitness Function)
$$\text{Fitness}(x) = \alpha \cdot F_1(X_x, y) + (1 - \alpha) \cdot \left(1 - \frac{\sum_{i=1}^D x_i}{D}\right)$$
* $\alpha = 0.85$: Ưu tiên tối đa hóa chất lượng phân loại $F_1\text{-score}$.
* $1 - \alpha = 0.15$: Khuyến khích giảm số lượng thuộc tính dư thừa (Feature Parsimony).

---

## 📊 4. Kết Quả Thực Nghiệm Khoa Học (Benchmark Results)

Kết quả đánh giá trên tập kiểm thử độc lập gồm **6.519 sinh viên** (tách 20% độc lập từ tập OULAD đã trích xuất):

| Phương Pháp | Số Đặc Trưng Được Chọn | Tỷ Lệ Giảm Đặc Trưng (%) | Accuracy | F1-Score | ROC-AUC |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Baseline (Tất cả đặc trưng)** | 29 / 29 | 0.0% | 90.87% | 0.9085 | 0.9672 |
| **Genetic Algorithm (GA)** | 14 / 29 | 51.7% | 91.12% | 0.9110 | 0.9688 |
| **Particle Swarm Optimization (PSO)** | 13 / 29 | 55.2% | 91.20% | 0.9119 | 0.9691 |
| **HCO Thuần túy** | 11 / 29 | 62.1% | 91.35% | 0.9134 | 0.9698 |
| **HCO-VNLS Cải tiến (Đề xuất)** | **8 / 29** | **72.4%** | **91.56%** | **0.9155** | **0.9712** |

> **Kết luận học thuật:** Thuật toán **HCO-VNLS** giảm được **72.4% số chiều dữ liệu** (chỉ giữ lại 8 thuộc tính quan trọng nhất: *điểm bài tập có trọng số, số ngày hoạt động LMS, tương tác tài nguyên tuần đầu, số bài nộp trễ hạn...*) mà vẫn nâng cao độ chính xác tổng thể lên **91.56%** và đạt **0.9712 ROC-AUC**, vượt trội so với GA, PSO và HCO thuần túy.

---

## 💡 5. Công Cụ Gợi Ý Chiến Lược Học Tập Cá Nhân Hóa (Recommendation Engine)

Hệ thống phân tích khoảng cách năng lực của từng sinh viên so với trung vị chuẩn của nhóm đạt kết quả khá giỏi và đưa ra các khuyến nghị hành động can thiệp khả thi:

| Nhóm Yếu Tố | Điều Kiện Phát Hiện | Mức Độ Ưu Tiên | Chiến Lược Đề Xuất Cụ Thể |
| :--- | :--- | :---: | :--- |
| **Điểm số bài tập** | Điểm TB $< 50$ | **HIGH** | Xem lại tài nguyên cốt lõi (`oucontent`), làm lại bài tập tự luyện và liên hệ trợ giảng. |
| **Hạn nộp bài** | Có bài nộp trễ hạn ($> 0$) | **HIGH** | Lập lịch cá nhân hóa, đặt hạn nộp sớm trước deadline chính thức 48 giờ. |
| **Độ chuyên cần** | Ngày hoạt động $< 60\%$ chuẩn | **HIGH** | Duy trì đăng nhập LMS tối thiểu 4 ngày/tuần, mỗi phiên từ 30–45 phút. |
| **Thảo luận diễn đàn** | Lượt click diễn đàn $< 40\%$ chuẩn | **MEDIUM** | Tham gia đặt câu hỏi trên diễn đàn môn học (`forumng`) và trao đổi nhóm. |
| **Khởi động đầu kỳ** | Clicks 4 tuần đầu $< 50$ | **HIGH** | Hoàn thành toàn bộ tài nguyên dẫn nhập tuần 1–4, tránh dồn ứ kiến thức. |

---

## 📂 6. Cấu Trúc Thư Mục Dự Án (Monorepo Architecture)

```text
personalized-learning/
├── apps/                               # CÁC ỨNG DỤNG ĐẦU CUỐI
│   ├── backend/                        # API Server với FastAPI (app/main.py, routers, schemas)
│   └── frontend/                       # Web Dashboard giao diện sinh viên (React/Vite)
│
├── packages/                           # CÁC GÓI MÃ NGUỒN TÁI SỬ DỤNG
│   └── ml/                             # GÓI HỌC MÁY & TỐI ƯU HÓA CỐT LÕI
│       ├── artifacts/                  # LƯU TRỮ MODEL ĐÃ HUẤN LUYỆN
│       │   ├── models/                 # best_hco_vnls_model.joblib, selected_features.json
│       │   └── scalers/                # data_pipeline.joblib
│       └── src/
│           ├── features/               # engineering.py (Trích xuất đặc trưng OULAD)
│           ├── preprocessing/          # pipeline.py (DataPipeline làm sạch, mã hóa, scale)
│           ├── optimization/           # THUẬT TOÁN TỐI ƯU HÓA
│           │   ├── hco.py              # Human Conception Optimizer
│           │   ├── vnls.py             # Variable Neighborhood Local Search
│           │   ├── hco_vnls.py         # Thuật toán lai đề xuất HCO-VNLS
│           │   └── baselines.py        # Genetic Algorithm (GA) & PSO
│           └── models/
│               └── recommendation/     # engine.py (Recommendation Engine)
│
├── data/                               # QUẢN LÝ DỮ LIỆU
│   ├── raw/                            # 7 bảng CSV OULAD thô (studentInfo, studentVle...)
│   └── processed/                      # oulad_features_engineered.csv (29 đặc trưng sạch)
│
├── notebooks/                          # NOTEBOOKS THỰC NGHIỆM KHOA HỌC
│   ├── 01_data_understanding.ipynb     # EDA, phân tích phân phối & trích xuất đặc trưng
│   ├── 02_hco_vnls_model_and_recommendation.ipynb # Benchmark hội tụ, đánh giá & Radar chart
│   └── 03_save_and_load_best_model.ipynb # Đóng gói, tải lại & suy luận thời gian thực
│
├── docs/                               # TÀI LIỆU NGHIÊN CỨU & BÀI BÁO GỐC
├── docker-compose.yml                  # Khởi chạy đa dịch vụ (Postgres, Backend, Frontend)
├── requirements.txt                    # Danh sách thư viện Python
└── README.md                           # Tài liệu tổng quan dự án
```

---

## 🚀 7. Hướng Dẫn Cài Đặt & Chạy Thực Nghiệm (Quickstart)

### 1. Cài đặt môi trường
```bash
# Clone dự án
git clone git@github.com:phantrongnguyen/personalized-learning.git
cd personalized-learning

# Tạo môi trường ảo Python
python -m venv venv
# Kích hoạt trên Windows:
.\venv\Scripts\activate
# Kích hoạt trên Linux/macOS:
source venv/bin/activate

# Cài đặt thư viện phụ thuộc
pip install -r requirements.txt
```

### 2. Chạy chuỗi Notebook thực nghiệm
Bạn có thể mở và chạy tuần tự các notebook trong VS Code hoặc khởi chạy Jupyter Server:
```bash
jupyter lab
```
1. Mở `notebooks/01_data_understanding.ipynb` để sinh dữ liệu sạch `data/processed/`.
2. Mở `notebooks/02_hco_vnls_model_and_recommendation.ipynb` để chạy thực nghiệm so sánh GA, PSO, HCO, HCO-VNLS.
3. Mở `notebooks/03_save_and_load_best_model.ipynb` để kiểm thử nạp model và suy luận thời gian thực.

### 3. Chạy Server Backend (FastAPI)
```bash
python apps/backend/app/main.py
```
* API Documentation (Swagger UI): `http://localhost:8000/docs`
* Health Check: `http://localhost:8000/api/v1/health`

---

## 👥 8. Thông Tin Đề Tài & Bản Quyền

* **Đề tài:** Hệ Thống Gợi Ý Chiến Lược Học Tập Cá Nhân Hóa (KLTN 13)
* **Cơ quan chủ quản:** Khoa Công Nghệ Thông Tin – Trường Đại học Công Thương TP.HCM (HUIT)
* **Giảng viên hướng dẫn:** ThS. Nguyễn Thị Thùy Trang (`trangntthuy@huit.edu.vn`)
* **Sinh viên thực hiện:** Phan Trọng Nguyên
* **Giấy phép:** [MIT License](LICENSE) © 2026 HUIT.
