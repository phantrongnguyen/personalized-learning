# Hệ Thống Gợi Ý Chiến Lược Học Tập Cá Nhân Hóa

> **Đề tài:** Dự báo nguy cơ học tập và gợi ý chiến lược học tập cá nhân hóa  
> **Thuật toán:** Human Conception Optimization (HCO) cải tiến kết hợp Variable Neighborhood Local Search (VNLS) tuyển chọn đặc trưng trên các họ mô hình Boosting (LightGBM, CatBoost, XGBoost)  
> **Đơn vị:** Trường Đại học Công Thương TP.HCM (HUIT) — Khoa Công nghệ Thông tin & Khoa học Dữ liệu  
> **Mã đề tài:** KLTN 13  
> **Giảng viên hướng dẫn:** ThS. Nguyễn Thị Thùy Trang (`trangntthuy@huit.edu.vn`)  
> **Sinh viên thực hiện:**
> - Phan Trọng Nguyên (MSSV: 2001210886) — Trưởng nhóm
> - Bùi Lê Hoài Bảo (MSSV: 2001215638)
> - Võ Bạch Kim Thịnh (MSSV: 2001216196)

[![Python](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.64.0-FF4B4B.svg)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Institution](https://img.shields.io/badge/HUIT-Khoa%20CNTT-orange.svg)](https://huit.edu.vn/)
[![Status](https://img.shields.io/badge/Status-Progress%20Updated%2009--10--2026-brightgreen.svg)](#)

---

## 📌 1. Giới Thiệu Dự Án (Overview)

Trong kỷ nguyên giáo dục số (EdTech và E-Learning), mỗi sinh viên có tốc độ tiếp thu, thời gian biểu và thói quen tương tác trên hệ thống quản lý học tập (LMS) hoàn toàn khác nhau. Việc thiếu sự theo dõi và can thiệp kịp thời dẫn đến tỷ lệ sinh viên bỏ học (Dropout) hoặc rớt môn cao.

Dự án **Hệ thống gợi ý chiến lược học tập cá nhân hóa** ứng dụng khai phá dữ liệu giáo dục (Educational Data Mining - EDM) kết hợp giải thuật tối ưu hóa thông minh mô phỏng sinh học **Human Conception Optimization (HCO)** cải tiến với **Variable Neighborhood Local Search (VNLS)** nhằm:
1. **Lựa chọn đặc trưng tối ưu (Feature Selection):** Khắc phục *Lời nguyền số chiều* ($D=34$ thuộc tính hành vi và nhân khẩu học) từ dữ liệu hành vi sinh viên trên OULAD, loại bỏ các đặc trưng dư thừa/nhiễu.
2. **Dự báo nguy cơ học tập:** Phân loại sớm sinh viên có nguy cơ rớt môn hoặc bỏ học (*At-Risk* vs *Successful*) tại các mốc thời gian quan sát sớm (Cutoff 50% và 75% chu kỳ học).
3. **Đề xuất chiến lược học tập cá nhân hóa:** Đưa ra các giải pháp can thiệp cụ thể (tăng thời lượng tương tác LMS, đổi phương pháp tự học, tham gia diễn đàn trao đổi, khắc phục trễ hạn bài tập) dựa trên bằng chứng định lượng của từng sinh viên.

---

## 🎯 2. Tiến Độ & Kết Quả Thực Hiện Đồ Án (Cập nhật 09/10/2026)

Hệ thống đã hoàn thành các nội dung và yêu cầu cốt lõi theo đề cương khóa luận:

- [x] **Khảo sát & Cơ sở lý thuyết chuyên sâu:** Hoàn thiện cơ sở toán học thuật toán **HCO** (Acharya & Das, 2022) với biên dạng vận tốc Poiseuille, cơ chế siêu hoạt hóa Cauchy (Cauchy hyperactivation), và **VNLS** (Hansen et al., 2017) với 4 cấu trúc lân cận $\mathcal{N}_1 \dots \mathcal{N}_4$.
- [x] **Dữ liệu chuẩn OULAD:** Thu thập và tích hợp toàn diện 7 bảng của bộ dữ liệu quốc tế **Open University Learning Analytics Dataset** (32.593 bản ghi sinh viên, hơn 10 triệu bản ghi tương tác VLE), thiết lập mốc Cutoff 50% và 75% chu kỳ học kỳ.
- [x] **Pipeline Tiền xử lý & Kỹ thuật đặc trưng vector hóa:** Xử lý giá trị khuyết thiếu, mã hóa biến phân loại, trích xuất đặc trưng đa chiều (điểm bài tập có trọng số, độ trễ hạn, clickstream theo mốc thời gian tuần 1–4, giữa kỳ, cuối kỳ) lưu tại `packages/ml/src/features/` và `CLHT_GB_GITHUB/NghienCuu_HCO_VNLS/notebooks/`.
- [x] **Cài đặt & Thực nghiệm thuật toán đề xuất HCO-VNLS:**
  - Cài đặt **HCO thuần túy** với cơ chế mô phỏng dịch nhầy cổ tử cung và pha siêu hoạt hóa.
  - Cài đặt **VNLS** với 4 toán tử lân cận ($1\text{-flip}$, $2\text{-flip}$, Bit Swap, Feature Drop).
  - Cài đặt **Lai ghép HCO-VNLS** cân bằng tối ưu giữa Khám phá toàn cục (Exploration) và Khai thác cục bộ (Exploitation).
- [x] **Thực nghiệm toàn diện 3 họ Boosting (LightGBM, CatBoost, XGBoost):** So sánh đa mô hình tại Cutoff 50% và 75%, kiểm chứng tính ổn định của mask đặc trưng, đối chứng với mask ngẫu nhiên và ablation test.
- [x] **Mô hình Gợi ý Chiến lược Học tập Cá nhân hóa:** Xây dựng `LearningRecommendationEngine` so sánh độ lệch hành vi của sinh viên nguy cơ so với chuẩn vị nhóm tích cực để sinh khuyến nghị hành động cụ thể.
- [x] **Đóng gói & Phân phối Mô hình (Artifacts):** Lưu trữ model trọng số (`.joblib`), metadata (`.json`), schema 30 cột đầu vào LightGBM tại `apps/backend/model_store/` và `streamlit-web/`.
- [x] **Hệ thống Web Service RESTful API (FastAPI Backend):** Hoàn thiện backend Clean Architecture tại `apps/backend/` phục vụ dự báo trực tuyến và cung cấp giao diện tĩnh tại `/app`.
- [x] **Giao diện Người dùng (Frontend UI/UX):**
  - Giao diện Dashboard SPA chuẩn SaaS: `apps/frontend/` (Vanilla HTML5/CSS3/ES6+ phục vụ trực tiếp qua FastAPI tại `/app`).
  - Giao diện Góc học tập React/Vite: `apps/frontend/src/` (hỗ trợ kiểm thử thành phần chuyên sâu).
  - Ứng dụng Web demo nhanh: `streamlit-web/app.py` cho phép cố vấn tra cứu và dự báo hồ sơ sinh viên 1-click.

---

## 🔬 3. Cơ Sở Toán Học Thuật Toán Đề Xuất (HCO-VNLS)

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

## 📊 4. Kết Quả Thực Nghiệm Nổi Bật

### So sánh các thuật toán tối ưu hóa (trên tập kiểm thử độc lập)
| Phương Pháp | Số Đặc Trưng Được Chọn | Tỷ Lệ Giảm Số Chiều (%) | F1-Score | ROC-AUC |
| :--- | :---: | :---: | :---: | :---: |
| **Baseline (Đầy đủ đặc trưng)** | 29 / 29 | 0.0% | 0.9085 | 0.9672 |
| **Genetic Algorithm (GA)** | 14 / 29 | 51.7% | 0.9110 | 0.9688 |
| **Particle Swarm Optimization (PSO)** | 13 / 29 | 55.2% | 0.9119 | 0.9691 |
| **HCO Thuần túy** | 11 / 29 | 62.1% | 0.9134 | 0.9698 |
| **HCO-VNLS Cải tiến (Đề xuất)** | **8 / 29** | **72.4%** | **0.9155** | **0.9712** |

### So sánh 3 bộ học Boosting tại Cutoff 75%
* **LightGBM (Mô hình triển khai chính):** Tối ưu nhất về tốc độ huấn luyện dạng cây histogram, đạt cân bằng cao giữa Precision, Recall và ROC-AUC khi kết hợp mask tuyển chọn từ HCO-VNLS.
* **CatBoost & XGBoost (Đối chứng kiểm tra chéo):** Xác nhận các thuộc tính được HCO-VNLS lựa chọn mang tính ổn định cao trên cả 3 họ mô hình, loại bỏ rủi ro over-fitting vào một thuật toán boosting duy nhất.

---

## 📂 5. Cấu Trúc Thư Mục Dự Án (Monorepo Architecture)

```text
personalized-learning/
├── apps/                               # CÁC ỨNG DỤNG ĐẦU CUỐI
│   ├── backend/                        # FastAPI REST API Backend
│   │   ├── api/v1/endpoints/           # Router: health, predictions
│   │   ├── ml/artifacts/               # Model .joblib & metadata .json
│   │   └── main.py                     # Entry point FastAPI & mount /app
│   └── frontend/                       # Giao diện Web Client
│       ├── index.html                  # Vanilla JS SPA Dashboard (chạy trực tiếp tại /app)
│       ├── css/style.css               # Giao diện CSS hiện đại
│       ├── js/app.js                   # Logic SPA, Auth, Call API, CSV export
│       └── src/                        # Ứng dụng React/Vite (tùy chọn)
│
├── streamlit-web/                      # ỨNG DỤNG DEMO STREAMLIT ĐỘC LẬP
│   ├── app.py                          # Streamlit UI trực quan
│   └── model_hco_vnls_lightgbm_cutoff75.joblib
│
├── CLHT_GB_GITHUB/                     # PHÂN HỆ NGHIÊN CỨU THỰC NGHIỆM
│   └── NghienCuu_HCO_VNLS/             # Chuỗi 7 notebook nghiên cứu chuyên sâu
│       ├── notebooks/                  # 01 -> 07 (LightGBM, CatBoost, XGBoost)
│       ├── ket_qua/                    # File log, CSV validation, mask JSON
│       └── hinh/                       # Đồ thị hội tụ và biểu đồ so sánh
│
├── packages/ml/                        # GÓI MÃ NGUỒN HỌC MÁY CỐT LÕI (Clean Architecture)
│   ├── src/optimization/              # hco.py, vnls.py, hco_vnls.py, baselines.py
│   ├── src/features/                  # Kỹ thuật đặc trưng vector hóa
│   └── src/preprocessing/             # Pipeline xử lý dữ liệu chuẩn hóa
│
├── bao_cao/                            # TÀI LIỆU VÀ BÁO CÁO TIẾN ĐỘ
│   ├── BaoCaoTienDo_KLTN_13_9-10.docx  # Báo cáo tiến độ hoàn chỉnh ngày 09/10/2026
│   └── KLTN13_Chuong1_Chuong2.docx     # Bản thảo chi tiết Chương 1 & Chương 2
│
└── README.md                           # Tài liệu tổng quan dự án
```

---

## 🚀 6. Hướng Dẫn Khởi Chạy (Quickstart)

### 1. Cài đặt môi trường Python
```bash
# Tạo môi trường ảo Python 3.12+
python -m venv venv

# Kích hoạt trên Windows:
.\venv\Scripts\activate

# Cài đặt các gói phụ thuộc:
pip install -r requirements.txt
```

### 2. Khởi chạy FastAPI Backend & Dashboard Web
```bash
# Khởi động máy chủ backend tại cổng 8000
python apps/backend/main.py
```
* **Swagger API Docs:** `http://127.0.0.1:8000/docs`
* **Giao diện Dashboard Web:** `http://127.0.0.1:8000/app/`

### 3. Khởi chạy Web Demo Streamlit
```bash
python -m streamlit run streamlit-web/app.py
```
* Trình duyệt sẽ tự động mở tại `http://localhost:8501`.

---

## 👥 7. Thông Tin Đề Tài & Bản Quyền

* **Đề tài:** Hệ Thống Gợi Ý Chiến Lược Học Tập Cá Nhân Hóa (KLTN 13)
* **Cơ quan chủ quản:** Khoa Công Nghệ Thông Tin – Trường Đại học Công Thương TP.HCM (HUIT)
* **Giảng viên hướng dẫn:** ThS. Nguyễn Thị Thùy Trang (`trangntthuy@huit.edu.vn`)
* **Sinh viên thực hiện:**
  - Phan Trọng Nguyên (MSSV: 2001210886)
  - Bùi Lê Hoài Bảo (MSSV: 2001215638)
  - Võ Bạch Kim Thịnh (MSSV: 2001216196)
* **Giấy phép:** [MIT License](LICENSE) © 2026 HUIT.
