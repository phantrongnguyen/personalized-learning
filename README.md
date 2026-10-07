# Dự báo nguy cơ học tập và gợi ý hỗ trợ

Nhánh nghiên cứu tập trung vào **HCO–VNLS + LightGBM**, với **CatBoost và XGBoost** làm hai đối chứng. Dữ liệu là các lượt học trong OULAD; cutoff 50%/75% là thời điểm quan sát, không phải tỷ lệ lấy mẫu dòng.

## Mở phần nào trước?

| Mục đích | Địa chỉ |
|---|---|
| Chuẩn bị báo cáo lý thuyết và kết quả | [Hướng dẫn trình bày](bao_cao/HUONG_DAN_TRINH_BAY.md) |
| Dữ liệu, chọn biến, kiểm chứng và hai đối chứng | [Nghiên cứu chính](CLHT_GB_GITHUB/NghienCuu_HCO_VNLS/README.md) |
| Hiểu thứ tự bảy notebook | [Hướng dẫn notebook](CLHT_GB_GITHUB/NghienCuu_HCO_VNLS/notebooks/HUONG_DAN_DOC_NOTEBOOKS.md) |
| Lý thuyết LightGBM, ví dụ và công thức Word | [Cơ sở lý thuyết LightGBM](apps/docs/Co_so_ly_thuyet_LightGBM_va_ung_dung_trong_du_bao_nguy_co_hoc_tap.docx) |
| Model và giao diện Streamlit | `streamlit-web/app.py` và model cùng thư mục |
| Schema, tham số và SHA-256 model | [Thông tin model](apps/backend/model_store/THONG_TIN_MODEL_HCO_VNLS_LIGHTGBM_75.json) |

## Phần nghiên cứu được giữ lại

- **Năm notebook chính:** kiểm tra dữ liệu → đặc trưng theo thời gian → HCO/VNLS với LightGBM → kiểm chứng biến → đóng gói model.
- **Hai notebook đối chứng đã chạy:** CatBoost và XGBoost; cùng cutoff, split theo sinh viên, seed 41, GroupKFold trong train và budget 8 mask.
- Bảng validation của 24 trường hợp, tên biến được chọn, hình và các bảng kiểm chứng ở nguồn nghiên cứu; không sao chép vào nhiều gói báo cáo.
- Model app vẫn là hybrid LightGBM 75%, 17 biến gốc → 30 cột sau tiền xử lý. Model cuối fit train + validation; bảng so sánh đánh giá các bản fit train-only.

Notebook/kết quả/Word HGB cũ, các thử nghiệm trung gian không còn dùng và gói báo cáo theo ngày được bỏ khỏi đầu nhánh sau khi sao lưu ngoài repository. Thư mục rỗng được giữ bằng `.gitkeep`. Các thư mục hạ tầng và web React/FastAPI trong `apps/` vẫn giữ; không nhầm nghiệm thu của web đó với Streamlit.

## Mở Streamlit

Dùng Python 3.12 và môi trường riêng. Cài phiên bản đã dùng cho artifact:

```powershell
python -m pip install streamlit==1.64.0 numpy==2.2.6 pandas==2.2.2 scikit-learn==1.6.0 lightgbm==4.7.0 joblib==1.4.2
python -m streamlit run streamlit-web/app.py
```

GitHub lưu mã nguồn, không tự chạy giao diện Streamlit. Bảy CSV nguồn và các bảng cấp lượt học không được kèm trong bản chia sẻ; xem [hướng dẫn dữ liệu](CLHT_GB_GITHUB/data/README.md) khi chạy lại nghiên cứu.

## Giới hạn cần nói rõ

Đây là thí nghiệm validation trong dataset hiện tại, không cam kết Accuracy 90–93%, tối ưu toàn cục hoặc áp dụng ngay cho sinh viên trường khác. Test lịch sử từng được xem; không coi đó là holdout mới. Gợi ý hỗ trợ là quy tắc dựa trên bằng chứng, chưa có đánh giá con người hoàn thành hoặc can thiệp chứng minh làm tăng điểm. Triển khai HCO/VNLS phải được đối chiếu thêm với công thức bài báo gốc trước khi tuyên bố tái hiện đầy đủ lý thuyết.
