# Trình diễn hệ thống và giải thích với GVHD

Bản chuẩn bị ngày 30/09/2026. Mục tiêu: trình diễn hệ thống hoạt động, không tuyên bố đã chứng minh gợi ý làm tăng điểm.

## 1. Chuẩn bị trước buổi báo cáo

1. Chạy apps/Start-Demo.ps1 từ gốc checkout. Mở http://127.0.0.1:5187/#goi-y hoặc tải lại tab đang mở.
2. Chờ backend nạp model. Chỉ chạy một bộ backend/frontend, không chạy chồng lên port của app khác.
3. Mở sẵn ba notebook trong apps/notebooks; đã có output nên không cần chạy lại lúc trình bày.
4. Dùng hồ sơ minh họa có sẵn, tránh gõ thông tin người học thật khi đang chia sẻ màn hình.

## 2. Mở đầu: bài toán của nhóm

“Nhóm muốn hỗ trợ người học từ dữ liệu đã biết ở một thời điểm trong học phần. Hệ thống có nhánh dự báo nguy cơ và nhánh gợi ý có giải thích. HCO–VNLS chọn đặc trưng cho LightGBM; phần gợi ý hiện dùng quy tắc minh bạch dựa vào bằng chứng.”

Giải thích cutoff 75% là 75% thời lượng học phần. Với AAA · 2013J dài 268 ngày, mốc quan sát là ngày 201. Không phải lấy 75% số sinh viên; ngưỡng cảnh báo 50% là khái niệm khác với cutoff 50%.

## 3. Trình diễn theo thứ tự này

### Tình huống 1 — Nộp sớm không bù được bài thiếu

Trong “Hồ sơ & gợi ý”, chọn “Nộp sớm không bù được bài thiếu”. Mở “Xem từng bài đánh giá”, rồi bấm “Phân tích hồ sơ”.

Điểm cần nói:

- Đây là một bản trích rút train, đã bỏ mã sinh viên và nhãn cuối kỳ, đổi mã bài thành mã minh họa.
- T = 180. Có 9 bài đến hạn và 9 bài đã nộp, nhưng một bài hạn ngày 187 đã nộp sớm ngày 176.
- Chỉ 8 bài trong tập đến hạn có bản ghi; còn 1 bài cần kiểm tra. Không được lấy 9 trừ 9 rồi nói hoàn thành hết.
- Xác suất model trên đầu vào này khoảng 7,5%, vẫn có G01. Đây không phải mâu thuẫn: nguy cơ tổng thể thấp không xóa bằng chứng thiếu bài.
- G01 đề nghị kiểm tra và trao đổi, không hứa vẫn được nộp muộn, không khẳng định sinh viên lười.

Các số xác suất là đầu ra lần chạy demo, không phải Accuracy hoặc kết quả đánh giá tổng quát. Notebook 11 giải thích phép đối chiếu; notebook 12 chạy API/model thật.

### Tình huống 2 — Một tuần chưa có tương tác

Chọn “Một tuần chưa có tương tác”, bấm phân tích và mở phần căn cứ của G03.

Nói: “Ở cutoff ngày 201, cửa sổ 7 ngày là từ 195 đến 201. Không có click trong cửa sổ này, nhưng có 72 click trong 30 ngày. Hệ thống hỏi về việc học ngoài hệ thống hoặc khó khăn truy cập, không kết luận người học không học.”

Hồ sơ này còn G02 do từng nộp trễ. Hai lời khuyên xử lý hai tín hiệu khác nhau. Chưa có dữ liệu nội dung để khuyên học lại một chương cụ thể.

### Tình huống 3 — Thiếu bằng chứng: hệ thống từ chối

Chọn tình huống này rồi phân tích. Phải thấy “Chưa chạy”, không phải “nguy cơ 0%”, và không có lời khuyên cụ thể.

Nói: “Đây là tình huống tổng hợp để kiểm thử việc thiếu xác nhận nguồn, không phải hồ sơ sinh viên thật. Hệ thống không bịa dữ liệu hoặc lấp chỗ thiếu bằng một lời khuyên chung.”

### Tình huống 4 — Nhập dữ liệu thủ công nếu cần

Vào “Đánh giá”. Có ba bước nhập số tổng hợp. Bước ba bổ sung xác nhận dữ liệu và chi tiết từng bài nếu muốn gợi ý bài nộp. Không có danh sách chi tiết đầy đủ thì hệ thống không lấy tổng bài để đoán thiếu bài.

Để thử nhanh, dùng “Điền ví dụ tổng hợp”; đây không phải hồ sơ thực và không có đủ chi tiết để gợi ý về bài nộp. API chặn sự kiện sau cutoff, số liệu tổng hợp mâu thuẫn và mã bài trùng.

### Kết thúc demo

Bấm “Tải phiếu kết quả”. Phiếu có kết quả vừa tính, lời khuyên, bằng chứng và giới hạn; không phải báo cáo thành tích hoặc quyết định học vụ.

## 4. Những câu dễ được hỏi

| Câu hỏi | Trả lời đúng phạm vi đã làm |
|---|---|
| HCO–VNLS ở đâu? | Chọn mask 17/38 đặc trưng cho LightGBM tại 75%. Chưa trực tiếp tối ưu bốn chiến lược G01–G04. |
| Sao không dùng điểm bài để khuyên ôn kiến thức yếu? | Bảng nguồn thiếu thời điểm công bố điểm, không đủ bản đồ kiến thức. Nộp trước cutoff không chứng minh đã nhận điểm. |
| Đặc trưng được chọn có phải nguyên nhân? | Không. Nó có thể hữu ích cho dự báo, không chứng minh thay đổi nó sẽ làm điểm tăng. |
| Tại sao nguy cơ thấp vẫn có lời khuyên? | Vì hành động kiểm tra bài dựa trên bản ghi cụ thể, không bị khóa bởi ngưỡng dự báo. |
| Cá nhân hóa ở đâu? | Hồ sơ có tín hiệu khác nhau nhận gợi ý khác nhau và có căn cứ riêng; chưa khẳng định tối ưu tác động cho từng cá nhân. |
| App đã được đánh giá chưa? | Đã kiểm thử kỹ thuật và chạy notebook; chưa có điểm chấm độ phù hợp của giảng viên/người học và chưa theo dõi tác động. |
| Có chạy cutoff 50% không? | Notebook kiểm tra bằng chứng ở 50% và 75%, nhưng app dự báo chỉ dùng model 75%. Không dùng sai model cho mốc khác. |
| Dữ liệu được bảo mật thế nào? | Demo chỉ chạy localhost, không lưu đầu vào vào DB, không dùng tên/mã sinh viên. Ví dụ rút gọn vẫn không được gọi là ẩn danh tuyệt đối; cần kiểm tra quyền phân phối trước khi công khai. |

## 5. Đề nghị cô góp ý

- Hướng HCO–VNLS chọn đặc trưng rồi tích hợp gợi ý có đáp ứng phạm vi đề tài không, hay cần trực tiếp tối ưu chiến lược?
- Bốn tình huống và cách diễn đạt đã phù hợp chưa? Xử lý gia hạn, miễn bài, bảo lưu thế nào?
- Có thể đánh giá lời khuyên bằng hồ sơ ẩn phương pháp với tiêu chí phù hợp, có căn cứ, khả thi, dễ hiểu không?

Không nói “hệ thống tăng điểm” hoặc “toàn bộ đề tài đã hoàn tất”. Có thể nói “đã có bản demo tích hợp, có kiểm thử và bằng chứng tái lập; đang chuẩn bị đánh giá độ phù hợp”.
