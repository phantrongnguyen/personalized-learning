# Đọc ba notebook bổ sung

Các notebook ở đây chỉ dành cho phần app/gợi ý mới. Không ghi đè notebook nghiên cứu trước đó và không huấn luyện lại model.

Để theo dõi **nguồn gốc model app**, xem chuỗi nghiên cứu tại `../../CLHT_GB_GITHUB/NghienCuu_HCO_VNLS/notebooks/`: notebook `05b` so sánh HCO/VNLS với LightGBM, `09` kiểm chứng mask chọn đặc trưng, và `10` đóng gói model 17 đặc trưng ở cutoff 75%. Ba notebook `11`–`13` dưới đây kiểm chứng riêng phần gợi ý và tích hợp app. Notebook nghiên cứu cần dữ liệu gốc và đầu ra trung gian nếu muốn chạy lại; chỉ xem kết quả đã lưu hoặc chạy demo thì không cần.

| Thứ tự | File | Câu hỏi trả lời | Kết quả đã có |
|---|---|---|---|
| 11 | 11_kiem_tra_bang_chung_goi_y.ipynb | Làm sao đếm đúng bài đến hạn chưa có bản ghi? | Đối chiếu train ở 50/75%, ví dụ nộp sớm có đáp án, xuất 7 tình huống demo |
| 12 | 12_goi_y_chien_luoc_co_giai_thich.ipynb | Một hồ sơ đi qua model và gợi ý như thế nào? | Gọi API thật cho 7 tình huống, bảng kết quả, giải thích G01–G04 và hình xác suất |
| 13 | 13_danh_gia_ky_thuat_va_phieu_gop_y.ipynb | Điều gì đã kiểm tra, điều gì chưa được đánh giá? | Kiểm thử backend; kiểm tra nguy cơ thấp vẫn có G01; phiếu đánh giá con người còn trống |

## Đọc nhanh

Mỗi notebook có phần câu hỏi, code từng bước, kết quả và cách hiểu. Số cell tính từ trên xuống, gồm cả Markdown:

- Notebook 11: cell 4 đối chiếu train; cell 7 ví dụ nộp sớm; cell 9 chuẩn bị dữ liệu demo; cell 11 bài tập có đáp án.
- Notebook 12: cell 4 chạy các hồ sơ qua API; cell 7 giải thích trường hợp nộp sớm; cell 9 vẽ biểu đồ.
- Notebook 13: cell 4 chạy kiểm thử; cell 6 kiểm tra nguy cơ thấp không chặn gợi ý; cell 8 tạo phiếu chấm trống.

Notebook 12 không mock model trong bảng kết quả. Notebook 13 có một kiểm thử mock xác suất 1% được ghi rõ, chỉ để thử logic; không dùng số mock làm kết quả model.

## Chạy lại

Từ gốc checkout, dùng Python trong apps/backend/.venv và kernel clht-demo đã cài theo README app. Lệnh: apps/backend/.venv/Scripts/python.exe apps/scripts/run_notebooks.py.

Mặc định dữ liệu được đọc từ thư mục CLHT_GB_GITHUB ngang cấp checkout CLHT_GB_APP_WORKTREE. Nếu ở máy khác, đặt biến môi trường CLHT_RESEARCH_DATA trỏ đến thư mục chứa data và NghienCuu_HCO_VNLS. Không yêu cầu copy cả CSV vào app.

Đầu ra nằm ở apps/research_outputs; bộ hồ sơ app nằm ở apps/backend/app/core/support_cases.json. Chạy lại notebook 11 sẽ tái tạo bộ hồ sơ này; khởi động lại backend nếu đang chạy để bỏ cache cũ. Nếu hash hoặc dữ liệu thay đổi, xem lại số kiểm tra thay vì sửa assertion cho qua.

## Giới hạn khi nghiệm thu

Kiểm thử đạt không đồng nghĩa lời khuyên giúp tăng điểm. Tác dụng thực tế và điểm chấm độ phù hợp chưa có. Model vẫn là bản cutoff 75% đã đóng gói, các gợi ý là quy tắc riêng, chưa được HCO–VNLS tối ưu trực tiếp.
