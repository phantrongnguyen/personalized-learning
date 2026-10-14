# Đối chiếu với hồ sơ lịch sử đã vượt qua nguy cơ

## Chức năng trong dashboard

Sau khi phân tích một hồ sơ, mở mục **Hồ sơ tương tự đã vượt qua nguy cơ**:

1. Xác nhận hồ sơ phản ánh **mốc 75% thời lượng học phần**.
2. Nhấn **Tìm trường hợp đối chiếu**.
3. Xem số người gần nhất gồm cả nhóm đạt và nhóm không đạt/rút lui.
4. Mở từng hồ sơ đạt để đối chiếu yếu tố hành vi/SHAP và các mốc 75%, 85%, 100%.
5. Đọc nguồn, cách ghép và giới hạn trước khi dùng làm căn cứ hỗ trợ.

Kết quả luôn dùng bản hồ sơ đã phân tích, không tự lấy giá trị đang sửa trên form.
Phân tích hồ sơ mới hoặc đổi API sẽ xóa đối chiếu cũ và yêu cầu xác nhận lại.
Đổi theme không làm mất kết quả. API đối chiếu lỗi không làm mất dự đoán.

## Dữ liệu thật, không dựng câu chuyện thành công

Thư viện cục bộ được dựng từ bảy CSV OULAD gốc. Không tạo hồ sơ giả khi thiếu dữ liệu.

- Nhóm tham chiếu là **3.447 enrollment** thuộc nhóm test theo người học,
  chia bằng permutation seed 41 như notebook nghiên cứu.
- Những người học này không thuộc nhóm train/validation đã fit artifact hiện tại.
- Bộ dữ liệu hiện tại có **74 enrollment** được model hiện tại xếp nguy cơ ở mốc 75%
  nhưng kết quả thật là Pass/Distinction. Không phải tất cả 74 hồ sơ đều gần người đang xét.
- Chỉ export mã giả danh, không trả id_student, tên hoặc đặc trưng nhân khẩu của
  người tham chiếu qua API. File thư viện vẫn chứa đặc trưng nghiên cứu và phải giữ cục bộ.
- Mã hồ sơ là SHA-256 rút gọn của khóa enrollment; khóa người học dùng để loại đếm trùng.
  Đây là giả danh phục vụ đối chiếu, không phải bảo đảm vô danh cho dữ liệu trường thật.

Model chấm lại lịch sử **hồi cứu**. Không biết người học có từng được cảnh báo hay nhận
can thiệp thực tế hay không. Việc được chấm nguy cơ rồi đạt cũng có thể là dự đoán dương giả;
không đủ để khẳng định đã thay đổi nhờ một hành động cụ thể.

## Cách chọn hồ sơ

Chỉ dùng các đặc trưng đã biết tại mốc 75% để chọn người gần nhau:

- Cùng code_module và đều vượt ngưỡng model; ngưỡng hiện tại là **0,5**.
- Xác suất lệch không quá **20 điểm phần trăm**.
- Có ít nhất một yếu tố hành vi tăng nguy cơ chung trong top 3 SHAP.
- Khoảng cách gồm **70% giá trị hành vi + 20% cấu trúc SHAP tăng + 10% chênh xác suất**.
- Giá trị hành vi số đếm dùng log1p; tỷ lệ giữ thang gốc. Chuẩn hóa bằng khoảng
  percentile 5–95 của thư viện; chặn khoảng cách mỗi biến ở 1.
- Top 3 yếu tố hành vi tăng nguy cơ của hồ sơ hiện tại có trọng số gấp đôi các biến khác.
- Cấu trúc SHAP là phân bố các đóng góp dương trên 11 biến hành vi, không phải % rủi ro.
- Chỉ nhận khoảng cách **≤ 0,25**, chọn tối đa **20 người** gần nhất, mỗi người một enrollment.
- **Sau khi ghép** mới xem kết quả cuối kỳ; hiển thị tối đa **3 hồ sơ đạt gần nhất**,
  đồng thời báo mẫu số và số hồ sơ không đạt/rút lui trong cùng nhóm.

Không trực tiếp đưa tuổi, giới tính, học vấn, ngày đăng ký hoặc kết quả cuối kỳ vào khoảng
cách hành vi. Xác suất và SHAP vẫn xuất phát từ mô hình 17 biến hiện tại; điều này không
phải cam kết công bằng nhân khẩu. Chưa có code_presentation của hồ sơ nhập để ghép cùng
đợt học, nên đợt học của từng trường hợp được hiển thị rõ.

Các trọng số/ngưỡng trên là quy tắc đối chiếu thực nghiệm, **chưa được kiểm chứng cho
một trường cụ thể**. Khoảng cách nhỏ không phải xác suất thành công.

## Diễn biến sau mốc dự báo

Đặc trưng baseline được tạo giống quy tắc nguồn model: chỉ sự kiện đến ngày
floor(0,75 × độ dài học phần); loại người đã rút lui/đăng ký sau mốc.
Đóng góp TreeSHAP và xác suất được kiểm tra tái dựng theo từng dòng trước khi export.

Ở các mốc 75%, 85%, 100%, phần diễn biến hiển thị:

- Số ngày có hoạt động trong **30 ngày** kết thúc ở mốc đó.
- Lượt tương tác trong cùng cửa sổ 30 ngày.
- Số bài có hạn đã biết, đến hạn và được nộp trước hoặc tại mốc / tổng bài đã đến hạn.
- Chênh lệch mốc 75% và cuối học phần, có thể tăng, giảm hoặc không đổi.

Tỷ lệ bài đến hạn này không hoàn toàn đồng nhất với submission_rate đầu vào model:
model có thể đếm cả bài nộp sớm/chưa đến hạn hoặc bài thi chưa có ngày hạn. Diễn biến
chỉ đếm bài đã đến hạn để tỷ lệ quan sát không vượt 100%. Số bài đến hạn thay đổi theo mốc.

**Không chấm lại nguy cơ bằng model 75% ở mốc 85%/100%** và không dùng dữ liệu
sau cutoff hay nhãn cuối kỳ vào khoảng cách ghép. Dữ liệu tương lai chỉ mô tả
những hồ sơ đã được chọn. LMS không phản ánh việc học ngoài hệ thống hoặc chất lượng hiểu bài.

## Tạo và nạp thư viện

Từ thư mục main_app, dùng Python trong môi trường backend đã cài requirements:

~~~powershell
.\.venv\Scripts\python.exe scripts/build_historical_cases.py --data-dir "C:\duong_dan\OULAD"
~~~

Thư mục nguồn cần: studentInfo.csv, studentRegistration.csv, courses.csv,
vle.csv, studentVle.csv, assessments.csv, studentAssessment.csv.

Công cụ ghi mặc định apps/backend/artifacts/historical_cases.json.gz. Có thể đổi
đường dẫn xuất bằng --output; backend đọc đường dẫn cấu hình HISTORICAL_CASES_PATH.
Khởi động lại backend sau khi dựng hoặc thay thư viện để nạp dữ liệu mới.

Công cụ kiểm tra số enrollment và phân tập theo metadata model, hash model,
SHAP tái dựng xác suất, thứ tự hồ sơ khi merge; lưu SHA-256 của từng CSV để truy xuất nguồn.
Hash nguồn được ghi lại để kiểm toán, không tự chứng minh giấy phép hay chất lượng dữ liệu.
Không huấn luyện lại model. Không cần thêm thư viện ngoài dependencies hiện có.
File thư viện mặc định nằm trong .gitignore; **không đưa dữ liệu nguồn/lịch sử lên Git**.
Cần kiểm tra giấy phép và phân quyền trước khi triển khai với dữ liệu trường thật.

## Hợp đồng API

POST /api/v1/historical-cases/ với features (17 biến) và cutoff_fraction: 0.75.
Backend tính lại xác suất/SHAP, không tin xác suất do client gửi.
Mốc khác bị từ chối với HTTP 422. Số không hữu hạn hoặc hành vi âm cũng bị từ chối.

Trạng thái có thể trả:

- available: có trường hợp đạt trong nhóm gần nhất.
- not_at_risk: hồ sơ hiện chưa vượt ngưỡng; không gán nhãn cần ‘lật kèo’.
- no_matches: chưa có hồ sơ đủ gần, không tự nới ngưỡng.
- no_recoveries: có nhóm gần nhưng chưa có trường hợp đạt, không chọn người xa hơn để kể chuyện thành công.
- unavailable: thiếu/hỏng thư viện hoặc không khớp model; dự đoán chính vẫn hoạt động.

Giải thích SHAP vẫn dùng log-odds, không phải điểm phần trăm.

## Kiểm tra cục bộ đã thực hiện

- Build frontend thành công; API dự đoán vẫn trả đủ 17 đóng góp và tái dựng đúng xác suất.
- Mẫu SV Yếu cho nhóm 13 người gần: 5 đạt, 8 không đạt/rút lui; hiển thị 3 hồ sơ đạt.
- Đối soát hồ sơ hiển thị trực tiếp với timestamp CSV gốc tại cả ba mốc.
- Đổi nhãn cuối kỳ và nhật ký tương lai không thay đổi số người đủ điều kiện/nhóm gần.
- Thử thư viện thiếu/hỏng/khác model, không có nhóm gần, không có trường hợp đạt và hồ sơ an toàn.
- Thử API từ chối mốc khác, thiếu mốc, số âm và số không hữu hạn.
- Giao diện: xác nhận mốc, mở/đóng bằng bàn phím, lỗi mạng/thử lại, giữ bản chụp hồ sơ,
  reset và hủy yêu cầu cũ khi phân tích lại, giữ kết quả khi đổi theme.
- Kiểm tra phần mới ở 280–2560 px, màn hình ngang thấp và chữ gốc 200%; không tràn thẻ.
  Một số phần giao diện cũ ngoài thẻ đối chiếu vẫn có thể tràn khi chữ 200% trên màn hình 320 px.

## Phần còn cần hoàn thiện

- Kiểm chứng độ phù hợp của cách ghép và trọng số bằng chuyên gia và dữ liệu trường.
- Đối chiếu đúng học phần/đợt học/thời điểm, loại chính người đang xét khi có mã người học.
  Form hiện tại chưa có định danh để xác định cùng người trong thư viện.
- Thêm dữ liệu về hỗ trợ đã nhận, bối cảnh ngoài LMS và theo dõi can thiệp thực tế.
- Chỉ đánh giá hiệu quả can thiệp khi có thiết kế nghiên cứu phù hợp, không suy ra từ ví dụ đạt.
- Chính sách truy cập/giữ dữ liệu và bảo vệ thông tin người học trước khi triển khai chính thức.
