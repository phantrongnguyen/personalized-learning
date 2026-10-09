# BÁO CÁO PHÂN TÍCH KIẾN TRÚC VÀ ĐÁNH GIÁ HỆ THỐNG GỢI Ý CHIẾN LƯỢC HỌC TẬP CÁ NHÂN HÓA (KLTN 13)

> **Cơ quan chủ quản:** Trường Đại học Công Thương TP.HCM (HUIT) — Khoa Công Nghệ Thông Tin  
> **Mã đề tài:** KLTN 13  
> **Giảng viên hướng dẫn:** ThS. Nguyễn Thị Thùy Trang (`trangntthuy@huit.edu.vn`)  
> **Sinh viên thực hiện:** Phan Trọng Nguyên  
> **Thuật toán đề xuất:** Human Conception Optimization (HCO) cải tiến kết hợp Variable Neighborhood Local Search (VNLS)  
> **Tập dữ liệu thực nghiệm:** Open University Learning Analytics Dataset (OULAD)  

---

## 📌 MỤC LỤC
1. [Tổng Quan & Tính Cấp Thiết Của Đề Tài](#1-tổng-quan--tính-cấp-thiết-của-đề-tài)
2. [Định Nghĩa Bài Toán Tổng Thể & Input / Output Hệ Thống](#2-định-nghĩa-bài-toán-tổng-thể--input--output-hệ-thống)
3. [Vai Trò & Cơ Chế Của Thuật Toán HCO-VNLS Trong Chọn Lọc Đặc Trưng](#3-vai-trò--cơ-chế-của-thuật-toán-hco-vnls-trong-chọn-lọc-đặc-trưng)
4. [Kiến Trúc Hệ Thống & Luồng Xử Lý Dữ Liệu (End-to-End Pipeline)](#4-kiến-trúc-hệ-thống--luồng-xử-lý-dữ-liệu-end-to-end-pipeline)
5. [Phân Tích Chi Tiết Chuỗi Thực Nghiệm Khoa Học (`notebooks/`)](#5-phân-tích-chi-tiết-chuỗi-thực-nghiệm-khoa-học-notebooks)
6. [Phân Tích Chi Tiết Gói Mã Nguồn Cốt Lõi (`packages/`)](#6-phân-tích-chi-tiết-gói-mã-nguồn-cốt-lõi-packages)
7. [Bản Chất Cơ Chế Gợi Ý & Cảnh Báo Sư Phạm](#7-bản-chất-cơ-chế-gợi-ý--cảnh-báo-sư-phạm)
8. [Đánh Giá Toàn Diện Ưu Điểm, Hạn Chế & Lộ Trình Phát Triển](#8-đánh-giá-toàn-diện-ưu-điểm-hạn-chế--lộ-trình-phát-triển)

---

## 1. Tổng Quan & Tính Cấp Thiết Của Đề Tài

Trong môi trường giáo dục trực tuyến (E-Learning / LMS), người học đối mặt với nhiều rào cản: thiếu kỷ luật tự giác, bắt nhịp chậm ở giai đoạn đầu, quản lý thời gian kém dẫn đến nộp trễ bài tập, và thiếu sự tương tác với giảng viên/cộng đồng. Hệ quả là tỷ lệ sinh viên bỏ học (*Dropout*) hoặc thi trượt (*Fail*) luôn ở mức cao.

Đề tài **"Hệ Thống Gợi Ý Chiến Lược Học Tập Cá Nhân Hóa"** giải quyết bài toán trên bằng cách chuyển dịch từ **Phân tích dự đoán (Predictive Analytics)** sang **Phân tích kê đơn (Prescriptive Analytics)**:
* Không chỉ dừng lại ở việc dự đoán sinh viên *đậu/rớt*.
* Đi sâu vào tìm ra **nguyên nhân gốc rễ (Root Causes)** của sự suy giảm phong độ.
* Kê đơn **kế hoạch hành động cụ thể, cá nhân hóa (Actionable Intervention Strategies)** với các chỉ số mục tiêu đo lường được nhằm giúp sinh viên chủ động cải thiện kết quả học tập.

---

## 2. Định Nghĩa Bài Toán Tổng Thể & Input / Output Hệ Thống

Hệ thống được cấu thành từ **1 bài toán tổng thể** và **3 bài toán con liên kết chặt chẽ**:

```
                       ┌─────────────────────────────────────────────────────────────┐
                       │                     INPUT HỆ THỐNG                          │
                       │ Hồ sơ sinh viên: Nhân khẩu học, Điểm số, Hành vi LMS/VLE    │
                       └──────────────────────────────┬──────────────────────────────┘
                                                      │
                                                      ▼
                       ┌─────────────────────────────────────────────────────────────┐
                       │ BÀI TOÁN 1: LỰA CHỌN ĐẶC TRƯNG TỐI ƯU (HCO-VNLS)            │
                       │ • Input: 30 đặc trưng thô/phái sinh                         │
                       │ • Output: Mask nhị phân chọn 4-8 đặc trưng cốt lõi          │
                       └──────────────────────────────┬──────────────────────────────┘
                                                      │
                       ┌──────────────────────────────┴──────────────────────────────┐
                       ▼                                                             ▼
        ┌───────────────────────────────────────────┐ ┌───────────────────────────────────────────┐
        │ BÀI TOÁN 2: DỰ BÁO NGUY CƠ HỌC TẬP        │ │ BÀI TOÁN 3: GỢI Ý CHIẾN LƯỢC HỌC TẬP      │
        │ • Input: Vector đặc trưng tối ưu          │ │ • Input: Hành vi SV + Chuẩn Benchmark     │
        │ • Output: Nhãn nguy cơ & Điểm rủi ro (%)  │ │ • Output: Điểm yếu & Lộ trình hành động   │
        └───────────────────────────────────────────┘ └───────────────────────────────────────────┘
                                                      │
                                                      ▼
                       ┌─────────────────────────────────────────────────────────────┐
                       │                     OUTPUT HỆ THỐNG                         │
                       │ Báo cáo tư vấn, xác suất rớt môn, chiến lược can thiệp,     │
                       │ checklist hành động và dữ liệu vẽ Radar Chart so sánh       │
                       └─────────────────────────────────────────────────────────────┘
```

---

### 2.1. Input & Output Của Toàn Bộ Hệ Thống Đầu Cuối

#### 📥 INPUT HỆ THỐNG
* **Nhân khẩu học & Đăng ký:** Mã môn học (`code_module`), học kỳ (`code_presentation`), giới tính, khu vực địa lý, trình độ học vấn cao nhất, phân vị kinh tế xã hội (`imd_band`), nhóm tuổi, số tín chỉ đăng ký, số lần học lại, ngày đăng ký học phần.
* **Kết quả đánh giá định kỳ:** Điểm trung bình bài kiểm tra (`avg_score`), điểm nhỏ nhất/lớn nhất (`min_score`, `max_score`), độ lệch chuẩn điểm (`std_score`), số lượng bài nộp (`total_assessments_taken`), số bài nộp trễ hạn (`late_submissions`), điểm trung bình có trọng số (`weighted_avg_score`).
* **Nhật ký tương tác VLE Clickstream:**
  * Theo mốc thời gian: Lượt click 4 tuần đầu (`clicks_early`), giữa kỳ (`clicks_mid`), ôn thi cuối kỳ (`clicks_late`), tổng số ngày hoạt động (`active_days`).
  * Theo phân loại tài nguyên: Lượt click bài giảng (`clicks_oucontent`), diễn đàn (`clicks_forumng`), bài kiểm tra trắc nghiệm (`clicks_quiz`), tài nguyên phụ trợ (`clicks_resource`), trang con (`clicks_subpage`), liên kết ngoài (`clicks_url`), trang chủ (`clicks_homepage`).

#### 📤 OUTPUT HỆ THỐNG
Bản kế hoạch hành động cá nhân hóa định dạng JSON / Dashboard:
1. **Trạng thái cảnh báo & Điểm rủi ro:** Phân loại `HIGH RISK` (Nguy cơ rớt môn/bỏ học) hoặc `SAFE` kèm xác suất rủi ro cụ thể (ví dụ: `82.0%`).
2. **Điểm yếu phát hiện (`weaknesses`):** Danh sách các tiêu chí bị tụt hậu so với ngưỡng chuẩn.
3. **Chiến lược can thiệp (`strategies`):** Danh sách hành động được ưu tiên hóa (`HIGH`, `MEDIUM`, `LOW`), kèm danh mục sư phạm và mục tiêu định lượng (`target_metric`).
4. **Dữ liệu đối sánh năng lực (Radar Chart Data):** Bộ dữ liệu đa chiều so sánh trực quan giữa sinh viên với nhóm khá giỏi (Pass/Distinction).

---

### 2.2. Chi Tiết Input / Output Của 3 Bài Toán Con

| Bài toán con | Bản chất học thuật | Input | Output |
| :--- | :--- | :--- | :--- |
| **1. Lựa chọn đặc trưng tối ưu (Feature Selection)** | Tối ưu hóa tổ hợp đa mục tiêu nhị phân (Binary Multi-objective Optimization) | - Ma trận đặc trưng $X \in \mathbb{R}^{N \times D}$ ($N = 32.593, D = 30$).<br>- Vector nhãn học tập $y \in \{0, 1\}^N$. | Vector mask nhị phân $x^* \in \{0, 1\}^D$ chỉ giữ lại $d = 4 \dots 8$ đặc trưng quan trọng nhất, giảm $> 72\%$ số chiều dữ liệu. |
| **2. Dự báo nguy cơ học tập (Risk Prediction)** | Học máy có giám sát – Phân loại nhị phân (Binary Classification) | Vector $d$ đặc trưng tối ưu của sinh viên sau khi qua chuẩn hóa `StandardScaler`. | - Nhãn phân loại $\hat{y} \in \{0, 1\}$ ($1$: Thành công, $0$: Nguy cơ).<br>- Xác suất rủi ro $P(\text{Risk}) \in [0.0, 1.0]$. |
| **3. Gợi ý chiến lược học tập (Prescriptive Engine)** | Phân tích khoảng cách năng lực kết hợp hệ luật sư phạm (Gap Analysis & Rule-based) | - Hồ sơ hành vi sinh viên $S$.<br>- Xác suất rủi ro $P_{\text{risk}}$.<br>- Vector trung vị chuẩn $M_{\text{benchmark}}$ của nhóm SV giỏi. | Báo cáo chẩn đoán, danh sách điểm yếu, các khuyến nghị hành động can thiệp và mục tiêu cần đạt. |

---

## 3. Vai Trò & Cơ Chế Của Thuật Toán HCO-VNLS Trong Chọn Lọc Đặc Trưng

### 3.1. Khẳng Định Mục Đích Cốt Lõi
Mục đích duy nhất và cốt lõi của thuật toán **HCO-VNLS** trong đồ án là giải quyết bài toán **Lựa chọn đặc trưng tối ưu (Optimal Feature Selection / Subset Selection)** theo phương pháp bọc (**Wrapper-based Method**).

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. Không gian tìm kiếm nhị phân (Binary Search Space):                      │
│    Mỗi cá thể là một mask nhị phân: X = [x₁, x₂, ..., x₃₀] ∈ {0, 1}³⁰       │
│    • xᵢ = 1: Thuộc tính thứ i ĐƯỢC CHỌN                                     │
│    • xᵢ = 0: Thuộc tính thứ i BỊ LOẠI BỎ (dư thừa / nhiễu)                 │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 2. Đánh giá chất lượng bằng Hàm Thích Nghi Đa Mục Tiêu (Fitness Function):  │
│                                                                             │
│    Fitness(X) = 0.85 × F1_Score(X) + 0.15 × (1 - |X| / 30)                  │
│                                                                             │
│    • Mục tiêu 1 (Trọng số 85%): Tối đa hóa chất lượng phân loại (F1-Score). │
│    • Mục tiêu 2 (Trọng số 15%): Tối đa hóa tỷ lệ loại bỏ thuộc tính dư thừa.│
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 3. Kết quả đầu ra của HCO-VNLS:                                             │
│    Bộ mask tối ưu chọn ra 4 – 8 đặc trưng cốt lõi nhất (giảm 72.4% - 86.7%) │
│    mà vẫn giữ nguyên (thậm chí tăng) độ chính xác phân loại.                │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2. Vì Sao Cần Chọn Đặc Trưng Mà Không Dùng Toàn Bộ 30 Biến?
1. **Loại bỏ nhiễu và đa cộng tuyến (Multicollinearity):** Trong dữ liệu LMS, nhiều thuộc tính có sự trùng lặp thông tin lớn (ví dụ: `total_clicks` là tổng của `clicks_early + clicks_mid + clicks_late` và các biến click tài nguyên). Giữ lại toàn bộ sẽ làm mô hình bị quá khớp (*Overfitting*).
2. **Tìm ra các chỉ số then chốt (Key Performance Indicators):** Lọc ra chính xác các yếu tố quyết định kết quả học tập (`weighted_avg_score`, `total_assessments_taken`, `late_submissions`, `clicks_late`).
3. **Tối ưu hóa tài nguyên tính toán:** Giúp hệ thống suy luận thời gian thực trên API nhanh và nhẹ hơn.

### 3.3. Phân Định Rõ Ràng Vai Trò Của Các Thuật Toán Trong Đề Tài

| Thành phần trong Đồ án | Thuật toán / Mô hình sử dụng | Mục đích cụ thể |
| :--- | :--- | :--- |
| **1. Tối ưu hóa chọn đặc trưng** | **HCO-VNLS** *(Lai ghép HCO + VNLS)* | Tìm ra tập con các đặc trưng tốt nhất và tinh gọn nhất từ 30 biến ban đầu. |
| **2. Dự báo nguy cơ học tập** | **Random Forest / Decision Tree** | Dùng các đặc trưng đã được HCO-VNLS chọn để phân loại sinh viên (*Pass/Distinction* vs *Fail/Withdrawn*). |
| **3. Gợi ý chiến lược học tập** | **Prescriptive Gap Engine** | So sánh hành vi sinh viên với trung vị chuẩn của nhóm giỏi để kê đơn lộ trình cải thiện. |

---

## 4. Kiến Trúc Hệ Thống & Luồng Xử Lý Dữ Liệu (End-to-End Pipeline)

Hệ thống được tổ chức theo kiến trúc **Monorepo** với 3 tầng phân tách độc lập:

```text
personalized-learning/
├── apps/                               # TẦNG ỨNG DỤNG ĐẦU CUỐI
│   ├── backend/                        # API Server với FastAPI (app/main.py, routers, schemas)
│   └── frontend/                       # Dashboard giao diện sinh viên / giảng viên (React)
│
├── packages/                           # TẦNG MÃ NGUỒN TÁI SỬ DỤNG
│   ├── ml/                             # GÓI MACHINE LEARNING & TỐI ƯU HÓA CỐT LÕI
│   │   ├── artifacts/                  # Model & Pipeline đã serialize (.joblib, .json)
│   │   └── src/
│   │       ├── features/               # engineering.py (Trích xuất 30 đặc trưng OULAD)
│   │       ├── preprocessing/          # pipeline.py (Làm sạch, mã hóa, chuẩn hóa)
│   │       ├── optimization/           # Thuật toán HCO, VNLS, HCO-VNLS, GA, PSO
│   │       └── models/recommendation/  # engine.py (Recommendation Engine)
│   └── shared/                         # Schemas và Constants dùng chung
│
├── data/                               # TẦNG QUẢN TRỊ DỮ LIỆU
│   ├── raw/                            # 7 bảng CSV OULAD thô
│   └── processed/                      # oulad_features_engineered.csv (Dữ liệu sạch 33 cột)
│
├── notebooks/                          # CHUỖI 3 NOTEBOOKS THỰC NGHIỆM KHOA HỌC
└── docs/                               # TÀI LIỆU HỌC THUẬT & BÀI BÁO GỐC
```

---

## 5. Phân Tích Chi Tiết Chuỗi Thực Nghiệm Khoa Học (`notebooks/`)

### 5.1. Notebook 01: Khám Phá Dữ Liệu & Kỹ Thuật Trích Xuất Đặc Trưng
* **File:** `notebooks/01_data_understanding.ipynb`
* **Quy trình:**
  1. Tải và phân tích tương quan 7 bảng OULAD (`studentInfo`, `studentRegistration`, `assessments`, `studentAssessment`, `vle`, `courses`, `studentVle`).
  2. Phân bố nhãn: `Pass` (38.0%), `Withdrawn` (31.2%), `Fail` (21.6%), `Distinction` (9.2%). Khi gom bài toán nhị phân: Nhóm Thành công (47.20%) vs Nhóm Nguy cơ (52.80%) $\rightarrow$ Tỷ lệ dữ liệu cân bằng lý tưởng.
  3. Trích xuất đặc trưng đa chiều theo trục thời gian và nhóm tài nguyên.
  4. Lưu trữ dữ liệu chuẩn hóa vào `data/processed/oulad_features_engineered.csv` (32.593 bản ghi $\times$ 33 thuộc tính).

---

### 5.2. Notebook 02: Huấn Luyện, Benchmark Hội Tụ & Đề Xuất Chiến Lược
* **File:** `notebooks/02_hco_vnls_model_and_recommendation.ipynb`
* **Thiết kế thực nghiệm:** 26.074 mẫu huấn luyện (Train 80%) và 6.519 mẫu kiểm thử độc lập (Test 20%), phân tầng theo nhãn (`stratify=y`).
* **Hàm thích nghi đa mục tiêu (Fitness Function):**
  $$\text{Fitness}(x) = 0.85 \cdot F_1\text{-score}(X_x, y) + 0.15 \cdot \left(1 - \frac{\sum_{i=1}^D x_i}{D}\right)$$
* **Bảng kết quả so sánh đối chứng trên tập kiểm thử:**

| Phương pháp tối ưu | Số đặc trưng chọn | Tỷ lệ giảm thuộc tính | Accuracy | Precision | Recall | F1-Score | ROC-AUC |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Baseline (Toàn bộ)** | 30 / 30 | 0.0% | 93.04% | 0.9331 | 0.9304 | 0.9304 | 0.9799 |
| **Genetic Algorithm (GA)** | 12 / 30 | 60.0% | 91.84% | 0.9219 | 0.9184 | 0.9184 | 0.9727 |
| **Particle Swarm (PSO)** | 5 / 30 | 83.3% | 93.02% | 0.9328 | 0.9302 | 0.9303 | 0.9783 |
| **HCO Thuần túy** | 12 / 30 | 60.0% | 93.39% | 0.9362 | 0.9339 | 0.9339 | 0.9810 |
| **HCO-VNLS Đề xuất** | **4 / 30** | **86.7%** | **93.04%** | **0.9329** | **0.9304** | **0.9304** | **0.9785** |

* **Đóng góp khoa học:** Thuật toán lai **HCO-VNLS** giảm được **86.7% số chiều dữ liệu** (chỉ giữ lại 4 thuộc tính cốt lõi) mà hiệu năng phân loại vẫn tương đương với mô hình sử dụng toàn bộ 30 thuộc tính.

---

### 5.3. Notebook 03: Đóng Gói Artifacts & Mô Phỏng API Thời Gian Thực
* **File:** `notebooks/03_save_and_load_best_model.ipynb`
* **Nội dung:**
  1. Serialize toàn bộ mô hình và pipeline sang `packages/ml/artifacts/`.
  2. Nạp lại độc lập (*Deserialization*): Sanity Check đạt độ tương thích **100%**.
  3. Đánh giá kiểm thử độc lập: **Accuracy 92.39%**, **ROC-AUC 0.9735**, **F1-Score 92.40%**.
  4. Thực hiện mô phỏng suy luận sinh khuyến nghị cho hồ sơ sinh viên mới.

---

## 6. Phân Tích Chi Tiết Gói Mã Nguồn Cốt Lõi (`packages/`)

### 6.1. Module Tiền Xử Lý Dữ Liệu
* `packages/ml/src/features/engineering.py`: Tổng hợp và trích xuất dữ liệu đa nguồn từ 7 bảng OULAD.
* `packages/ml/src/preprocessing/pipeline.py`: Class `DataPipeline` xử lý missing values, mã hóa nhãn nhị phân, `LabelEncoder` cho biến định tính và `StandardScaler` cho biến định lượng.

---

### 6.2. Module Thuật Toán Tối Ưu Hóa (`packages/ml/src/optimization/`)

1. **Human Conception Optimizer (`hco.py`):**
   * Hàm truyền Sigmoid nhị phân: $S(v) = \frac{1}{1 + e^{-v}}$.
   * Vận tốc cập nhật theo hướng dẫn dịch nhầy tử cung với trọng số quán tính $w$ giảm tuyến tính từ $0.9 \rightarrow 0.4$.
   * Pha siêu hoạt hóa (*Hyperactivation Phase*): Sử dụng nhiễu phân phối Cauchy $C(0, 1)$ khi tiến độ $\ge 70\%$ để thoát cực trị cục bộ.
2. **Variable Neighborhood Local Search (`vnls.py`):**
   * Sử dụng 4 cấu trúc lân cận: $k=1$ (1-bit flip), $k=2$ (2-bit flip), $k=3$ (Bit swap giữa 1 và 0), $k=4$ (Feature drop $1 \rightarrow 0$).
   * Chiến lược tìm kiếm cải tiến: Khởi động lại $k=1$ ngay khi tìm thấy nghiệm tốt hơn.
3. **Lai Ghép HCO-VNLS (`hco_vnls.py`):**
   * Cân bằng hoàn hảo giữa Thăm dò toàn cục (*Exploration* từ HCO) và Khai thác sâu cục bộ (*Exploitation* từ VNLS).
4. **Mô Hình Đối Chứng (`baselines.py`):**
   * Cài đặt chuẩn xác Genetic Algorithm (GA) và Binary Particle Swarm Optimization (BPSO).

---

### 6.3. Module Gợi Ý Chiến Lược Học Tập (`engine.py`)

* **Class `LearningRecommendationEngine`:**
  * `fit_benchmarks()`: Tính toán vector trung vị chuẩn ($M_{\text{benchmark}}$) từ toàn bộ sinh viên đạt Pass / Distinction.
  * Phân tích khoảng cách hành vi trên 5 nhóm sư phạm:
    1. **Điểm số kiểm tra (`avg_score`):** Nhận diện lỗ hổng kiến thức nền tảng.
    2. **Kỷ luật nộp bài (`late_submissions`):** Cảnh báo thói quen trì hoãn deadline.
    3. **Độ chuyên cần LMS (`active_days`):** Cảnh báo tần suất đăng nhập ngắt quãng.
    4. **Tương tác diễn đàn (`clicks_forumng`):** Thúc đẩy học tập cộng đồng và hỏi đáp.
    5. **Khởi động đầu kỳ (`clicks_early`):** Khắc phục tình trạng bắt nhịp chậm ở 4 tuần đầu.

---

### 6.4. Kho Lưu Trữ Artifacts (`packages/ml/artifacts/`)
* `models/best_hco_vnls_model.joblib`: Trọng số mô hình Random Forest tối ưu.
* `scalers/data_pipeline.joblib`: Pipeline tiền xử lý và scaler đã fit.
* `models/selected_features.json`: Mask nhị phân và danh sách 30 thuộc tính.
* `models/recommendation_benchmarks.json`: Bảng trung vị chuẩn của nhóm giỏi.

---

## 7. Bản Chất Cơ Chế Gợi Ý & Cảnh Báo Sư Phạm

### 7.1. Cơ Chế Hoạt Động Cốt Lõi
Nội dung gợi ý và cảnh báo trong hệ thống được xây dựng theo mô hình **Phân tích kê đơn lai ghép (Hybrid Prescriptive Analytics)** kết hợp giữa **Dữ liệu thực tế (Data-Driven)** và **Hệ chuyên gia dựa trên luật (Expert Rule-Based)**:

1. **Thành phần Tự động từ Dữ liệu (Data-Driven):**
   * Xác suất nguy cơ rớt môn ($P_{\text{risk}}$) được dự đoán bởi mô hình Machine Learning.
   * Ngưỡng so sánh mục tiêu (Benchmark Medians) được tính toán tự động từ hàng chục nghìn sinh viên thật trong bộ dữ liệu OULAD.
2. **Thành phần Chuyên gia Sư phạm (Expert Knowledge Templates):**
   * Các câu chữ hành động can thiệp và phân cấp ưu tiên (`HIGH`, `MEDIUM`, `LOW`) được định nghĩa theo chuẩn phương pháp sư phạm nhằm đảm bảo tính khả thi.

### 7.2. Tính Hợp Lệ & Khoa Học Trong Nghiên Cứu Giáo Dục Số
Cách tiếp cận này **hoàn toàn đúng đắn, chuẩn mực và được khuyến nghị** trong lĩnh vực Learning Analytics (tương tự các hệ thống nổi tiếng thế giới như *Purdue Course Signals* hay *OU Analyse*):
* **Tính sư phạm & Khả thi:** Tránh tình trạng AI sinh ra lời khuyên "ảo giác" (hallucination) hoặc chung chung vô nghĩa.
* **Tính giải thích được (Explainable AI - XAI):** Sinh viên và giảng viên hiểu rõ *tại sao* nhận được cảnh báo này (dựa trên sự chênh lệch chỉ số định lượng so với mức chuẩn).

---

## 8. Đánh Giá Toàn Diện Ưu Điểm, Hạn Chế & Lộ Trình Phát Triển

### 🌟 Ưu Điểm Nổi Bật
1. **Tính mới về mặt học thuật:** Ứng dụng thành công giải thuật mô phỏng sinh học mới HCO (2022) kết hợp VNLS cho bài toán Feature Selection trong Giáo dục số.
2. **Chuyển dịch thành công sang Phân tích kê đơn:** Đưa ra giải pháp can thiệp hành động thực tế chứ không chỉ dừng ở dự đoán đậu/rớt.
3. **Thực nghiệm bài bản, đối chứng thuyết phục:** So sánh chi tiết với GA, PSO, HCO thuần túy.
4. **Kiến trúc mã nguồn chuẩn mực:** Tổ chức Monorepo tách bạch, có pipeline và artifacts sẵn sàng triển khai.

---

### ⚠️ Hạn Chế & Điểm Cần Cải Thiện
1. **Đồng bộ hóa số lượng đặc trưng:** Cần chạy huấn luyện chính thức một lần trên toàn bộ tập dữ liệu để cố định danh sách đặc trưng tối ưu đồng nhất giữa báo cáo và artifact.
2. **Hoàn thiện tầng Ứng dụng (Application Layer):** Cần kết nối router API FastAPI tại `apps/backend/` và hoàn thiện giao diện Web Dashboard tại `apps/frontend/`.
3. **Phân hóa Benchmark theo môn học:** Có thể nâng cấp tính trung vị chuẩn riêng theo từng `code_module` để phản ánh đúng đặc thù từng môn (STEM vs Xã hội).

---

### 🚀 Lộ Trình Triển Khai Tiếp Theo (Action Roadmap)
* **Giai đoạn 1:** Xây dựng router `POST /api/v1/recommend` trên FastAPI nạp trực tiếp các file từ `packages/ml/artifacts/`.
* **Giai đoạn 2:** Xây dựng Dashboard React/Vite hiển thị Thẻ cảnh báo rủi ro, Biểu đồ Radar năng lực và Kế hoạch can thiệp tuần.
* **Giai đoạn 3:** Hoàn thiện văn bản toàn văn Khóa luận tốt nghiệp theo quy cách chuẩn của trường Đại học Công Thương TP.HCM (HUIT).
