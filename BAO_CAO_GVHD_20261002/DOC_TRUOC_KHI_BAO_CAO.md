# Nội dung báo cáo với giảng viên hướng dẫn

Chuẩn bị ngày 01/10/2026 cho buổi báo cáo dự kiến ngày 02/10/2026. Đây là bản trích các bằng chứng đã có, không phải một lần huấn luyện hay thí nghiệm mới.

## Mở theo thứ tự nào?

1. Đọc phần “Mạch trình bày trong 10–15 phút” bên dưới.
2. Mở [bảng so sánh HCO, VNLS và HCO–VNLS](ket_qua/hco_vnls_lightgbm_validation.csv).
3. Mở [hình diễn biến tìm mask](hinh/kiem_chung_duong_di_mask.png) và [hình bỏ từng đặc trưng](hinh/ablation_feature_hybrid_75.png).
4. Mở [kết quả các tình huống ứng dụng](ket_qua/ket_qua_demo.csv).
5. Khi cô hỏi chi tiết, mở notebook theo bảng địa chỉ phía dưới. Bản [Word đã chia cấp đề mục](tai_lieu/Bao_5.docx) dùng để đọc sâu phần ứng dụng; không cần trình bày hết bản Word trong buổi báo cáo.

## Mạch trình bày trong 10–15 phút

| Thứ tự | Nội dung nên nói | Bằng chứng trong gói |
|---|---|---|
| 1 | Bài toán: dùng dữ liệu học tập đã quan sát để dự báo nguy cơ Fail/Withdrawn và đưa ra gợi ý có căn cứ. Phần dự báo và phần gợi ý có vai trò khác nhau. | Notebook 12 và bản Word. |
| 2 | Dữ liệu có bảy bảng. Tổng hợp theo sinh viên–môn học–đợt học; chỉ dùng sự kiện xảy ra trước hoặc đúng cutoff. Nhãn cuối kỳ không được làm feature. | Notebook 01, 02; bảng kiểm kê bảy nguồn. |
| 3 | Cutoff 75% là mốc thời gian bằng floor(0,75 × độ dài môn), không phải lấy 75% số dòng. Train/validation/test tách theo sinh viên. Tập còn theo học có thể thay đổi giữa các cutoff, nên không quy toàn bộ chênh lệch chỉ số cho thời gian quan sát. | Notebook 01; notebook 10, cell 4. |
| 4 | HCO, VNLS và HCO–VNLS tìm mask giữ/bỏ đặc trưng. LightGBM học từ các cột đã chọn để dự báo. Fitness có thưởng độ gọn, không đồng nhất với AP validation. | Notebook 05b, 09; bảng so sánh LightGBM. |
| 5 | Đã kiểm chứng mask bằng năm seed, mask ngẫu nhiên cùng số cột và thí nghiệm bỏ từng đặc trưng. Những phép thử này kiểm tra đóng góp dự báo trong cấu hình đang xét, không chứng minh quan hệ nhân quả. | Notebook 09; ba hình kiểm chứng. |
| 6 | Bản model app: HCO–VNLS + LightGBM 80 cây, 17/38 đặc trưng tại cutoff 75%. Khóa mask rồi fit train + validation, không dùng test để fit. | Notebook 10; metadata model. |
| 7 | Ứng dụng có dự báo, bốn quy tắc gợi ý G01–G04, hồ sơ mẫu, nhập liệu và phiếu kết quả. Có bảy tình huống kiểm tra đã lưu; hồ sơ thiếu xác nhận nguồn không bị trả xác suất giả bằng 0. | Notebook 11–13; kết quả demo. |
| 8 | Chưa chứng minh gợi ý giúp tăng điểm; chưa có đánh giá con người; HCO–VNLS chưa tối ưu trực tiếp chiến lược. Xin cô xác nhận phạm vi đề tài và tiêu chí chấm gợi ý. | Phiếu đánh giá còn trống; phần giới hạn trong Word. |

## Bảng so sánh cần đọc đúng

Trích từ cùng bảng LightGBM 80 cây tại cutoff 75%, cùng validation và ngưỡng dự báo 0,5. Đây là kết quả model fit trên train, không phải lần đánh giá mới của artifact đã fit lại train + validation.

| Phương án | Số đặc trưng | Accuracy | Precision nguy cơ | Recall nguy cơ | F1 nguy cơ | Weighted F1 | AP nguy cơ |
|---|---:|---:|---:|---:|---:|---:|---:|
| Đủ đặc trưng | 38 | 87,35% | 92,00% | 68,98% | 78,84% | 86,83% | 0,8970 |
| HCO | 17 | 87,06% | 92,20% | 67,87% | 78,18% | 86,49% | 0,8915 |
| VNLS | 16 | 87,29% | 91,70% | 69,07% | 78,79% | 86,78% | 0,8926 |
| HCO–VNLS | 17 | 87,41% | 92,21% | 68,98% | 78,92% | 86,89% | 0,8968 |

Nhận xét: hybrid dùng ít cột hơn và có Accuracy nhỉnh hơn đủ cột, nhưng AP hơi thấp hơn, Recall bằng nhau. Chênh lệch nhỏ này chưa được chứng minh có ý nghĩa thống kê. Không nói hybrid vượt mọi phương án trên mọi chỉ số; cũng không coi một seed là bảo đảm ổn định. Bảng gốc còn có cutoff 50% để đối chiếu riêng trong mốc đó.

AP là chất lượng xếp hạng, không đọc thành phần trăm dự báo đúng. Recall 68,98% nghĩa là nhận diện được khoảng 69/100 hồ sơ thật sự nguy cơ ở validation, đồng thời còn bỏ sót khoảng 31/100. Weighted F1 tổng hợp F1 theo số lượng từng lớp, không thay thế Recall của lớp nguy cơ.

## Ba tình huống nên trình bày

### Tổng số bài nộp đủ nhưng vẫn thiếu bài đến hạn

Tình huống “Nộp sớm không bù được bài thiếu”: 9 bài đến hạn, 9 bài đã nộp, nhưng chỉ 8 bài nộp khớp danh sách đến hạn. Phải đối chiếu theo mã bài thay vì lấy hai tổng số trừ nhau. Nguy cơ ước lượng khoảng 7,46%; vẫn có G01 và G02. Nguy cơ thấp không ngăn một gợi ý có bằng chứng.

### Một tuần chưa có tương tác

Tình huống “Một tuần chưa có tương tác” có quy tắc G03 và G02; nguy cơ ước lượng khoảng 31,69%. Số liệu hoạt động gần đây làm căn cứ gợi ý, không dùng để kết luận người học lười hoặc xác định nguyên nhân gây trượt môn.

### Thiếu xác nhận nguồn

Tình huống “Thiếu bằng chứng: hệ thống từ chối” không có xác suất và không có quy tắc khớp. Đây là từ chối đánh giá, không phải nguy cơ bằng 0%. Notebook có kết quả lưu để trình bày kể cả khi không mở được giao diện trực tiếp.

Không tính Accuracy/AP từ sáu hồ sơ mẫu; chúng được chọn để minh họa tình huống, không phải tập kiểm tra đại diện. Không dùng thời gian lần đầu nạp model để so trực tiếp với lần gọi đã có cache.

## Địa chỉ cell để trả lời khi cô hỏi

Số cell tính từ trên xuống, gồm cả Markdown và code, không phải execution count trong dấu ngoặc vuông. Số hiệu notebook giữ theo bản gốc; gói này cố ý chỉ chọn một số notebook nên có khoảng trống giữa các số.

| Notebook trong thư mục notebooks | Mở cell nào? | Dùng để giải thích |
|---|---|---|
| [01 – Kiểm tra dữ liệu](notebooks/01_kiem_tra_du_lieu_va_ro_ri.ipynb) | 3; 4–5; 6–7 | Bảy nguồn; cutoff theo độ dài môn; kiểm tra khóa/nhãn/nhóm sinh viên. |
| [02 – Tạo đặc trưng](notebooks/02_tao_dac_trung_theo_thoi_gian.ipynb) | 3–5; 6–7 | Cắt sự kiện rồi tạo feature; ví dụ dòng dữ liệu đã che mã sinh viên. |
| [05b – So sánh LightGBM](notebooks/05b_hco_vnls_lightgbm.ipynb) | 3–5 | Bảng đủ cột/HCO/VNLS/hybrid, cách đọc và nhận xét. |
| [09 – Kiểm chứng mask](notebooks/09_kiem_chung_dac_trung_hco_vnls.ipynb) | 3–5; 6–7; 8–9 | Chấm mask; đối chứng/độ ổn định; bỏ từng cột và đo AP train-CV. |
| [10 – Đóng gói model](notebooks/10_dong_goi_model_hco_vnls_lightgbm_75.ipynb) | 4; 6; 8; 10 | Khóa mask và chia tập; fit; lưu; nạp thử. Nạp thử không phải đánh giá chất lượng mới. |
| [11 – Đối chiếu bằng chứng](notebooks/11_kiem_tra_bang_chung_goi_y.ipynb) | 4; 7; 9 | Đối chiếu bài nộp; ví dụ nộp sớm; tạo tình huống demo. |
| [12 – Dự báo và gợi ý](notebooks/12_goi_y_chien_luoc_co_giai_thich.ipynb) | 4; 7; 9 | Kết quả gọi API thật; giải thích tình huống; biểu đồ xác suất. |
| [13 – Đánh giá kỹ thuật](notebooks/13_danh_gia_ky_thuat_va_phieu_gop_y.ipynb) | 4; 6; 8 | Kiểm thử backend; kiểm tra logic gợi ý; phiếu đánh giá chưa chấm. |

## Những điều cần nói rõ

- G01–G04 là quy tắc gợi ý riêng, không phải chiến lược do HCO–VNLS trực tiếp tối ưu.
- Test lịch sử đã từng được xem; không gọi đó là holdout mới chưa từng sử dụng.
- Kiểm thử kỹ thuật đạt không chứng minh gợi ý giúp tăng điểm. Chưa xác nhận đầy đủ thao tác trình duyệt; còn hai trường hợp đầu vào mâu thuẫn được mô tả trong Word.
- Model app chỉ hỗ trợ cutoff 75%; kết quả nghiên cứu 50% không có nghĩa app đã dùng được model 50%.
- Phiếu đánh giá con người cố ý để trống. Không có điểm trung bình độ phù hợp để báo cáo.

## Hai câu xin ý kiến cô

1. HCO–VNLS chọn đặc trưng cho dự báo và lớp gợi ý có giải thích đã đáp ứng đề cương chưa, hay cần tối ưu trực tiếp chiến lược học tập?
2. Cô có thể góp ý tiêu chí và chấm thử độ phù hợp của các gợi ý để bổ sung đánh giá ngoài chỉ số dự báo không?

## Phạm vi của thư mục này

Chỉ dùng để xem, thuyết trình và đối chiếu bằng chứng. Các notebook giữ nguyên code và output của bản gốc, không chỉnh đường dẫn hoặc chạy lại. Vì không kèm dữ liệu thô, các module dùng chung, app và toàn bộ kết quả trung gian, đây không phải môi trường thực nghiệm độc lập; bấm Run All ở thư mục này có thể lỗi. Khi cần chạy lại, dùng dự án gốc và môi trường đã cài.

Nguồn bản sao:

- Notebook nghiên cứu: CLHT_GB_APP_WORKTREE/CLHT_GB_GITHUB/NghienCuu_HCO_VNLS/notebooks.
- Bảng và hình kiểm chứng nghiên cứu đã lưu: CLHT_GB_GITHUB/NghienCuu_HCO_VNLS/ket_qua và hinh trong bản nghiên cứu cục bộ, nằm ngang cấp repository làm việc. Các bảng và hình cần báo cáo đã được sao chép vào gói này.
- Word, notebook app, kết quả demo và metadata: CLHT_GB_APP_WORKTREE/apps.

Không kèm CSV từng sinh viên, model joblib, node_modules, .venv, log, bản Word cũ hoặc thí nghiệm ngoài phạm vi buổi báo cáo. Không sửa bản gốc. Gói được đặt tại BAO_CAO_GVHD_20261002 trong repository để chia sẻ trên nhánh aBaoN9/clht-gb-github; không kèm ZIP trùng nội dung.
