# HCO–VNLS, LightGBM và hai đối chứng

## Chốt phạm vi

Model triển khai: **HCO–VNLS + LightGBM 80 cây, cutoff 75%**, 17 biến gốc → 30 cột sau tiền xử lý. CatBoost/XGBoost là hai đối chứng đã chạy, chưa thay model app.

Hiện chỉ giữ **bảy notebook**: năm notebook chính và hai notebook đối chứng. Các bản HGB, so nhiều cutoff/ứng viên cũ và CatBoost trung gian đã sao lưu ngoài repository rồi bỏ khỏi nhánh để tránh nhầm phiên bản. Thư mục rỗng giữ bằng `.gitkeep`.

## Thứ tự đọc

| Notebook | Nhiệm vụ |
|---|---|
| `01_kiem_tra_du_lieu_va_ro_ri.ipynb` | Kiểm kê bảy bảng, khóa gộp và rò rỉ thời gian. |
| `02_tao_dac_trung_theo_thoi_gian.ipynb` | Tạo bảng cutoff, tỷ lệ/cửa sổ tương tác và split sinh viên. Output lịch sử có cả mốc trung gian; phần so sánh cuối chỉ dùng 50%/75%. |
| `05b_hco_vnls_lightgbm.ipynb` | Đủ 38 biến/HCO/VNLS/hybrid với LightGBM, chấm mask trong train-CV. |
| `09_kiem_chung_dac_trung_hco_vnls.ipynb` | Nhiều seed, đối chứng mask ngẫu nhiên và ablation để kiểm chứng bộ biến. |
| `10_dong_goi_model_hco_vnls_lightgbm_75.ipynb` | Khóa mask 17 biến, fit train + validation, xuất artifact và nạp thử. |
| `06_so_sanh_catboost_voi_lightgbm_50_75.ipynb` | CatBoost giữ category gốc; đủ biến và ba phương pháp chọn biến ở 50%/75%. |
| `07_so_sanh_xgboost_voi_lightgbm_50_75.ipynb` | XGBoost dùng median/mode/One-Hot; cùng các trường hợp, gộp bảng ba bộ học. |

Thứ tự tái tạo: **01 → 02 → 05b → 09 → 10**, rồi **06 → 07** cho đối chứng. Không cần chạy lại nghiên cứu để mở app đã có model. Đọc [hướng dẫn notebook](notebooks/HUONG_DAN_DOC_NOTEBOOKS.md) để biết địa chỉ cell.

## Giao thức so sánh cuối

Giữ split theo `id_student` ở seed 41 (khoảng 70%/15%/15% số sinh viên), không chia ngẫu nhiên từng lượt học. Mỗi bộ học có đủ 38 biến/HCO/VNLS/hybrid ở hai cutoff, ngưỡng 0,5. Tìm mask: GroupKFold 3 phần bên trong train, alpha 0,85, budget 8 mask mới, population 3. Không chọn mask theo validation hoặc đánh giá test mới.

Hai đối chứng tự tìm mask; LightGBM chỉ fit lại với mask đã chốt. Đây là so pipeline end-to-end, không tách riêng tác động bộ học và bộ biến. CatBoost xử lý category gốc; XGBoost/LightGBM dùng cùng median/mode/One-Hot học từ train. Thời gian tìm mask, fit và dự đoán tách riêng, đo một lần, không coi là benchmark ổn định.

## Bảng hybrid đọc nhanh

Nguồn: `ket_qua/so_sanh_ba_bo_hoc_50_75.csv`. Đây là **validation của các bản fit train-only**, không phải đánh giá mới của artifact fit train + validation.

| Cutoff | Bộ học + HCO–VNLS | Biến | Accuracy | Precision risk | Recall risk | F1 risk | AP |
|---|---|---:|---:|---:|---:|---:|---:|
| 50% | LightGBM | 16 | 80,54% | 84,44% | 60,14% | 70,25% | 0,8452 |
| 50% | CatBoost | 17 | 80,37% | 85,14% | 58,92% | 69,64% | 0,8426 |
| 50% | XGBoost | 17 | 80,87% | 86,07% | 59,57% | 70,41% | 0,8488 |
| 75% | LightGBM | 17 | 87,41% | 92,21% | 68,98% | 78,92% | 0,8968 |
| 75% | CatBoost | 16 | 85,89% | 91,52% | 64,70% | 75,80% | 0,8839 |
| 75% | XGBoost | 17 | 87,32% | 93,08% | 67,95% | 78,55% | 0,8941 |

XGBoost hybrid ở 50% nhỉnh Accuracy/AP nhưng Recall hơi thấp hơn LightGBM. Ở 75%, hybrid LightGBM nhỉnh Accuracy/Recall/F1/AP; XGBoost nhỉnh Precision. CatBoost đủ 38 biến tại 75% có AP 0,8979 nhưng hybrid CatBoost chỉ 0,8839: giảm biến không đảm bảo tăng chất lượng. Chênh nhỏ chưa chứng minh có ý nghĩa thống kê; không tuyên bố mô hình nào thắng mọi chỉ số.

## Những đầu ra được giữ

`ket_qua/` giữ bảng ba bộ học, bảng mask LightGBM, nhật ký/tần suất chọn biến/đối chứng ngẫu nhiên/ablation và giải thích 30 cột số. `hinh/` giữ bảy hình đối chứng/kiểm chứng cùng giải thích nguồn. Không sao chép chúng sang `bao_cao/`; [hướng dẫn trình bày](../../bao_cao/HUONG_DAN_TRINH_BAY.md) dẫn tới nguồn chuẩn và tài liệu Word.

## Tái tạo môi trường nghiên cứu

Python 3.12.6; các phiên bản đã chạy được ghim trong `../requirements.txt` và JSON `giao_thuc_*_50_75.json`. Tạo môi trường riêng, cài thư viện rồi đăng ký kernel:

```powershell
python -m pip install -r CLHT_GB_GITHUB/requirements.txt
python -m ipykernel install --user --name clht-mo-rong --display-name "CLHT nghiên cứu 50–75%"
python -m jupyterlab
```

Chuẩn bị bảy CSV theo `../data/README.md`, chạy 01/02 trước để sinh cache cutoff. Các CSV cấp lượt học và bảng chia sinh viên chỉ lưu cục bộ, bị Git bỏ qua. Không đưa môi trường, cache hoặc snapshot cục bộ lên nhánh.

Chưa có kiểm chứng trên kỳ học/trường khác, đánh giá con người hoàn thành về gợi ý hoặc can thiệp chứng minh tăng điểm. HCO/VNLS hiện tại là phiên bản pilot trong code; cần đối chiếu bài báo gốc để khẳng định tái hiện đầy đủ thuật toán.
