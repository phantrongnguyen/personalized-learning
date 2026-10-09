# Phần nghiên cứu dùng để trình bày

Nội dung hiện tại tập trung vào **HCO–VNLS + LightGBM** và hai đối chứng **CatBoost/XGBoost** tại cutoff 50%/75%. Không dùng các kết quả HGB cũ làm bằng chứng cho model hiện tại.

## Đường đọc gọn

1. [Hướng dẫn trình bày](../bao_cao/HUONG_DAN_TRINH_BAY.md): lý thuyết, công thức, hai đối chứng, chỉ số và bố cục slide.
2. [Nghiên cứu chính](NghienCuu_HCO_VNLS/README.md): bảy notebook, bảng và hình được giữ.
3. [Lý thuyết LightGBM trong Word](../apps/docs/Co_so_ly_thuyet_LightGBM_va_ung_dung_trong_du_bao_nguy_co_hoc_tap.docx): có ví dụ xuyên suốt và công thức Word; không chỉ mô tả thư mục.
4. [Thông tin model app](../apps/backend/model_store/THONG_TIN_MODEL_HCO_VNLS_LIGHTGBM_75.json): schema, bộ biến, tham số và hash.

`clht_code/` chứa thao tác dữ liệu, tiền xử lý, chỉ số và bộ tìm mask dùng chung. Huấn luyện và nghiệm thu kết quả nằm trong các notebook. Bảy CSV nguồn tự chuẩn bị theo `data/README.md`; không đẩy dữ liệu cấp sinh viên lên GitHub.

## Vì sao có thư mục trống?

Các thư mục `notebooks/`, `ket_qua/`, `hinh/`, `docs/` và `mo_hinh/` cũ được giữ lại bằng `.gitkeep` theo yêu cầu. **Bằng chứng hiện tại chỉ đọc trong `NghienCuu_HCO_VNLS/`**, còn model/giao diện ở `../streamlit-web/`. Các đầu ra cũ đã sao lưu ngoài repository trước khi tinh gọn.

Không có model đối chứng nào tự thay thế model đang triển khai. Chỉ số validation không phải đánh giá mới của artifact đã fit train + validation.
