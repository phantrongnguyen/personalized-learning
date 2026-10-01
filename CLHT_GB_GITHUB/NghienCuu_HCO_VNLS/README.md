# Dự báo nguy cơ học tập và chọn đặc trưng HCO–VNLS

Thư mục này độc lập với `notebooks/`, `ket_qua/`, `hinh/` cũ. Nó dùng lại bảy CSV nguồn trong `../data/` nhưng ghi mọi sản phẩm mới tại đây. **Chưa có cam kết đạt Accuracy 90–93%.**

## Bắt đầu từ đâu?

Mở `notebooks/HUONG_DAN_DOC_NOTEBOOKS.md`, sau đó đọc/chạy các notebook theo số thứ tự 00–05c; đọc `05b` sau `05` để xem thí nghiệm đối chứng LightGBM. Notebook có giải thích bằng tiếng Việt, hiển thị bảng và lưu hình trong `hinh/`. Chạy từ thư mục gốc `CLHT_GB_GITHUB`.

`04_catboost_lightgbm_xgboost.ipynb` đã chạy với CatBoost 240 cây; `04c_thu_them_mo_hinh.ipynb` giữ LogisticRegression cân bằng làm đối chứng Recall. **Năm mô hình theo đuổi:** CatBoost, XGBoost, LightGBM, HGB và LogisticRegression cân bằng; bảng gộp nằm ở `ket_qua/nam_mo_hinh_validation.csv`. `05c_hco_vnls_catboost.ipynb` là thí nghiệm **chọn cột** riêng: CatBoost 80 cây giữ category gốc, so đủ 38 cột với HCO/VNLS/hybrid dưới cùng cấu hình. Hai cấu hình CatBoost 240/80 cây trả lời hai câu hỏi khác nhau, không quy chênh lệch giữa chúng riêng cho feature selection.

Ba notebook này **đã chạy ngày 24/09/2026 và giữ output**. Để hiểu toàn bộ quá trình theo trạng thái mới nhất, đọc `bao_cao/BaoCao_DuBaoNguyCo_HCO_VNLS.md` hoặc bản Word cùng tên trước; bảng năm mô hình cô đọng ở `bao_cao/UNG_VIEN_GIU_LAI_2026_09_24.md`. Kết quả chọn cột bằng CatBoost 80 cây không vượt đối chứng đủ cột trong pilot ngân sách 8.

ExtraTrees và MLP nhỏ không thuộc bảng năm mô hình. Các notebook thử nghiệm MLP/ensemble/test trước đây được lưu cục bộ, không nằm trong bản công bố này. Bảng ứng viên hiện tại chỉ so trong cùng cutoff và cùng split; đây vẫn là lựa chọn theo validation, chưa được xác nhận độc lập trên kỳ học mới.

Lần chạy trên máy này dùng Python 3.12 và kernel `CLHT nghiên cứu 50–75%`. Môi trường riêng đặt tại `.venv/`; để tái tạo:

```powershell
uv venv NghienCuu_HCO_VNLS/.venv --python 3.12 --system-site-packages
uv pip install --python NghienCuu_HCO_VNLS/.venv/Scripts/python.exe catboost==1.2.10 lightgbm
NghienCuu_HCO_VNLS/.venv/Scripts/python.exe -m ipykernel install --user --name clht-mo-rong --display-name "CLHT nghiên cứu 50–75%"
```

Ngoài ra cần các thư viện dự án ở `requirements.txt` cùng XGBoost. Các phiên bản thực tế được ghi trong output notebook. Nếu thiếu gói, **không** xem một notebook chưa chạy là đã có kết quả.

## Nguồn và quyền chia sẻ

 Các CSV gốc là OULAD ẩn danh, cần tự kiểm tra quyền phân phối. CSV cấp enrollment, bảng chia sinh viên, xác suất của từng sinh viên được `.gitignore` loại trừ; chỉ nên chia sẻ thống kê tổng hợp và biểu đồ. Không đưa `.venv/` lên GitHub.

Ngoại lệ theo yêu cầu chia sẻ ngày 01/10/2026: `ket_qua/xuat_30_dac_trung_lightgbm/` có bản xuất 30 cột số sau tiền xử lý của model app, không kèm mã sinh viên trực tiếp, nhãn hoặc split. Xem README trong thư mục đó để hiểu cách đọc và giới hạn chia sẻ. Quy tắc loại trừ các CSV nguồn vẫn giữ nguyên.

## Quy tắc so sánh

Các mốc 50%, 60%, 65%, 70%, 75% đều dùng cùng một phép gán train/validation/test theo `id_student`. HCO, VNLS và hybrid chỉ tìm mask qua GroupKFold trong train. Validation dùng so sánh mô hình; test trong lịch sử dự án đã từng được xem nên không phải holdout hoàn toàn nguyên sơ.

**Các bước chưa chạy hoặc bị lược** phải được ghi rõ trong `bao_cao/`, không suy diễn là đã hoàn thành toàn bộ kế hoạch nghiên cứu dài hạn.
