# Định nghĩa dữ liệu, radar và quy tắc gợi ý — 21/10/2026

## 1. Phạm vi kiến trúc

- HCO-VNLS chọn đặc trưng; artifact LightGBM đang phục vụ dự báo nhãn nguy cơ từ 17 đầu vào tại cutoff 75%. Quy tắc gợi ý không phải đầu ra được học của LightGBM.
- Dashboard nhập tay: `apps/frontend/src/utils/recommendations.ts` tạo gợi ý minh họa từ dữ liệu nhập và nhãn/xác suất model. Không tự tạo plan/task, không kiểm toán log gốc; các ngưỡng và mức ưu tiên là giả định sản phẩm chưa được đánh giá sư phạm.
- Luồng giảng viên: `apps/backend/services/support_suggestions.py` áp dụng G02_AGGREGATE/G03/G04 có kiểm tra metadata bằng chứng; giảng viên xem căn cứ, sửa nháp và quyết định giao nhiệm vụ theo plan ACTIVE hợp lệ. GET không ghi plan/task.
- Radar chỉ mô tả chỉ số hành vi theo mốc tham khảo. Không phải phân vị, phép đo năng lực, mức nguy cơ mới hoặc bằng chứng hiệu quả can thiệp.

## 2. Kiểm tra nguồn benchmark và quyết định áp dụng

Rà soát mã ứng dụng, `packages/shared`, mã nghiên cứu trong `experiments` và tài liệu model chưa tìm thấy tập tham chiếu hoặc script tái tạo chứng minh benchmark là “Top 25%” hay nhóm Pass/Distinction. Trước thay đổi, hai bộ số còn khác nhau:

| Chỉ số | Backend cũ | Frontend cũ | Mốc dùng chung hiện tại |
| --- | ---: | ---: | ---: |
| Tổng click | 350 | 2.400 | 350 |
| Ngày có hoạt động | 40 | 85 | 40 |
| Tỷ lệ ngày hoạt động | 0,45 | 0,65 | 0,45 |
| Click 7 ngày | 30 | 120 | 30 |
| Tỷ lệ nộp bài | 0,95 | 0,85 | 0,95 |

Giữ các mốc backend trước đây để thống nhất hiển thị; **đây là lựa chọn tương thích, không xác nhận các số này đúng về mặt thống kê**. Xóa bộ frontend riêng và các tuyên bố nguồn chưa được chứng minh. Cấu hình chung: `packages/shared/constants/radar-reference.json`, version `illustrative-cutoff75-v1`, status `illustrative_unvalidated`. Python và TypeScript cùng đọc tệp này; Dockerfile hiện có đã COPY `packages` cho cả hai ứng dụng.

Muốn công bố một benchmark thống kê sau này cần xác định tập tham chiếu, tiêu chí chọn nhóm, cutoff, đơn vị, xử lý dữ liệu thiếu và mã tính tái lập; ghi version/checksum nguồn và đánh giá khả năng áp dụng HUIT. Việc tính benchmark thống kê mới chưa thuộc kết quả đã thực hiện này.

## 3. Hợp đồng radar

- Năm chiều đầu: `reference_score = round(min(100, max(0, value / reference * 100)), 1)`. 100% nghĩa là đạt hoặc vượt mốc hiển thị, không phải hơn 100% sinh viên hay xác suất đạt môn.
- Chiều nộp trễ: `student_value = max(0, 1 - late_submissions_to_t * 0.25) * 100`; mốc là 100. Hệ số 0,25 là quy ước hiển thị kế thừa, chưa kiểm chứng sư phạm. Không gọi đây là tỷ lệ bài nộp đúng hạn.
- Khi số bài đã nộp bằng 0, thiếu số bài, hoặc số bài trễ lớn hơn tổng đã nộp: chiều nộp trễ là `null`. Không suy ra 100% từ việc chưa có bài nộp.
- Giá trị thiếu, âm, không hữu hạn hoặc tỷ lệ ngoài [0, 1] là `null`, không thay bằng 0. Không có snapshot thì API trả 404. Giao diện hiển thị “—”/“Chưa đủ dữ liệu”, không nối đa giác tổng hợp khi thiếu chiều.
- Loại bỏ ngưỡng tô màu radar 50%/70% ngụ ý mức tốt/xấu khi chưa có căn cứ; giữ màu trung tính và giá trị tham khảo.
- API sinh viên và cố vấn dùng cùng hàm tạo payload, trả `reference_score`, `unit`, `reference_version`, `reference_status`, `snapshot_id`, `cutoff_stage`, `recorded_at` và `data_source` nếu có. `recorded_at` là thời điểm ghi DB, không phải ngày cutoff.
- **Thay đổi API:** bỏ `percentile`; client phải đọc `reference_score` và xử lý `null`. Backend/frontend cần được triển khai cùng phiên bản. Không có migration DB vì không đổi dữ liệu lưu trữ.
- Radar của form nhập tay phản ánh dữ liệu người dùng đang xem hoặc provenance lần dự báo; không tự xác nhận nguồn LMS. Radar sinh viên phản ánh snapshot được chọn bởi API, không phải dữ liệu thời gian thực.

## 4. Ý nghĩa dữ liệu OULAD và giới hạn chuyển sang HUIT

Nguồn định nghĩa gốc: [Kuzilek và cộng sự, Open University Learning Analytics dataset (2017)](https://doi.org/10.1038/sdata.2017.171). `studied_credits` là tổng tín chỉ các học phần sinh viên đang học trong bối cảnh Open University. Mã học phần và dữ liệu sinh viên đã được ẩn danh. Các ngày đăng ký là ngày tương đối với mốc bắt đầu học phần. Đây không phải bảng quy đổi tín chỉ/bằng cấp sang HUIT.

| Trường/nhóm | Cách dùng trong dự án | Quy tắc khi đưa vào bối cảnh HUIT |
| --- | --- | --- |
| `studied_credits` | Giữ đơn vị đầu vào OULAD của artifact | Không nhập số tín chỉ HUIT rồi mặc định tương đương; chưa có hệ số quy đổi được xác minh. Bỏ quy tắc `>=90` suy ra quá tải HUIT. |
| `code_module` | Artifact nhận AAA–GGG | Không tự gán mã môn HUIT vào nhóm OULAD. Tên môn demo không chứng minh tương đương nội dung/độ khó. Mã ngoài hợp đồng vẫn bị API dự báo từ chối. |
| `highest_education`, `gender`, `age_band` | Giữ nhóm đầu vào và cách mã hóa của artifact | Không tự quy đổi bằng cấp hoặc suy luận năng lực từ nhóm nhân khẩu học; không ép nhóm ngoài hợp đồng vào nhóm có sẵn. |
| `region`, `imd_band`, `disability` | Có trong hồ sơ/nguồn OULAD, không phải toàn bộ đều thuộc 17 đầu vào model hiện tại | Không đổi nhãn khu vực/chỉ số bất lợi thành dữ liệu HUIT nếu chưa có định nghĩa tương ứng; không dùng làm căn cứ riêng để giao can thiệp. |
| `date_registration` | Ngày tương đối với khai giảng; có thể âm | Không diễn giải thành ngày lịch hoặc số tín chỉ. |
| Click, ngày hoạt động, `days_since_last_activity` | Đặc trưng được tổng hợp đến cutoff | Click không đồng nghĩa đăng nhập, học hiểu hay chuyên cần trên lớp. Không có click chưa chứng minh ngừng học. |
| `clicks_recent_7/30` | Hai cửa sổ kết thúc cùng tại cutoff; 7 ngày nằm trong 30 ngày | Không gọi là so sánh hai tháng độc lập hoặc dữ liệu hiện tại. |
| `submission_rate`, số bài nộp/trễ | Chỉ số tổng hợp theo quy trình tạo đặc trưng | Cần biết bài đến hạn, miễn/gia hạn và độ đầy đủ nguồn trước khi diễn giải; không xác định bài cụ thể từ số tổng hợp. |
| Nhãn model | Nguy cơ Fail/Withdrawn trong giao thức OULAD | Không coi là kết luận sinh viên HUIT chắc chắn trượt/bỏ học; không đổi Distinction thành xếp loại HUIT. |

`DEFAULT_FEATURES`/`PRESETS` là dữ liệu tổng hợp minh họa, không phải hồ sơ sinh viên thật. Form có nhãn rõ; preset mẫu có số bài trễ không vượt tổng bài đã nộp. Snapshot mang `data_source=synthetic_demo` được hiển thị là minh họa; thiếu nguồn thì hiển thị chưa xác nhận. Không tự sửa tín chỉ/mã môn/dữ liệu cá nhân trong database, không đổi artifact hoặc threshold để phù hợp dữ liệu demo.

## 5. Bảng quy tắc Dashboard nhập tay

Các ngưỡng bên dưới là **giả định minh họa hiện có**, chưa có nghiên cứu hoặc tập hiệu chỉnh được xác minh trong repository. Giữ điều kiện để không tự ý hiệu chỉnh hành vi, nhưng bỏ các kết luận về nguyên nhân, bỏ học, sức khỏe và năng lực. Các mức HIGH/MEDIUM/LOW chỉ là thứ tự xem xét của quy tắc, không phải mức nguy cơ mới của model.

| ID | Điều kiện | Mục tiêu/cách xử lý | Ngoại lệ và cách cố vấn điều chỉnh |
| --- | --- | --- | --- |
| `watch-moderate` | Nhãn dưới ngưỡng model, xác suất ≥0,30 | Đề nghị trao đổi/theo dõi thêm | 0,30 không phải ngưỡng can thiệp đã kiểm chứng; không giả định ngưỡng model luôn 0,50. Thống nhất lịch và mục tiêu theo học phần. |
| `maintain-performance` | Nhãn dưới ngưỡng model, xác suất <0,30 | Tiếp tục theo dõi | Không suy ra tương tác tốt, đạt môn hoặc đủ điều kiện trợ giảng; xác minh nhu cầu trước khi thêm thử thách. |
| `high-inactivity` | Nhãn cần theo dõi, số ngày không có click ≥14 | Xác minh gián đoạn tại cutoff | Kiểm tra học ngoài LMS, thời khóa biểu và log thiếu; không yêu cầu đăng nhập trong 24 giờ chỉ từ snapshot cũ. |
| `low-active-ratio` | Nhãn cần theo dõi, tỷ lệ ngày hoạt động <0,35 | Trao đổi lịch học phù hợp | Không suy ra học dồn từ tỷ lệ; cố vấn chọn lịch theo thực tế. |
| `no-submission` | Nhãn cần theo dõi, số bài đã nộp =0 | Xác minh bài đến hạn và nguồn dữ liệu | Có thể chưa có bài đến hạn/được miễn/log thiếu; không tự kết luận lỗi kỹ thuật hoặc yêu cầu nộp bù. |
| `late-submission` | Nhãn cần theo dõi, đã nộp >0 và tỷ lệ <0,60 hoặc số bài trễ ≥2 | Đối chiếu lịch, hạn cá nhân và trao đổi hỗ trợ | Tỷ lệ đúng 0,60 không kích hoạt nếu chưa đủ 2 bài trễ. Mục tiêu do cố vấn/sinh viên thống nhất. |
| `drop-recent` | Nhãn cần theo dõi, click 30 ngày >0 và click 7 ngày < click 30 ngày /10 | Xác minh hai cửa sổ hoạt động tại cutoff | Đây là cửa sổ chồng lấn, không chứng minh suy giảm đột biến hay vấn đề tâm lý; nhóm quy tắc được đổi sang chuyên cần. |
| `general-consult` | Nhãn cần theo dõi nhưng không khớp quy tắc trên | Đề nghị trao đổi để làm rõ nhu cầu | Không suy ra điểm nghẽn kiến thức từ xác suất. |
| `credit-overload` — đã bỏ | Trước đây dùng `studied_credits >=90` | Không còn phát gợi ý này | Chưa có ánh xạ đơn vị OULAD/HUIT hoặc ngưỡng quá tải đã kiểm chứng. |

Thiếu/không hợp lệ các đầu vào dùng bởi quy tắc, xác suất ngoài [0,1], bài trễ > bài nộp hoặc click 7 ngày > click 30 ngày thì không sinh gợi ý. Lớp này vẫn không xác minh được sự đầy đủ của log nguồn; không dùng nó thay cho luồng giảng viên có metadata. Trên Dashboard, cố vấn xem xét và điều chỉnh khi lập kế hoạch ở luồng nghiệp vụ phù hợp; sao chép gợi ý không tạo nhiệm vụ.

## 6. Bảng quy tắc giảng viên có bằng chứng

Ở mốc ưu tiên 1 dùng `lecturer-support-1.0`. Ưu tiên 2 nâng lên `lecturer-support-1.1` để yêu cầu xác nhận có người phụ trách và hash gắn với đúng snapshot; xem [quy trình rà soát database](../database/database-snapshot-review.md). Các điều kiện tín hiệu trong bảng dưới vẫn giữ nguyên.

Điều kiện chung: snapshot `CUTOFF_75`; thời lượng học phần dương; `snapshot_day=floor(length*0.75)`; ngày bắt đầu; nguồn không rỗng; `confirmed_at` hợp lệ có múi giờ, không tương lai; bản ghi/xác nhận không trước cutoff. Cutoff tương lai trả `abstained`; metadata thiếu trả `insufficient_data`. API không tự kiểm toán log gốc.

| ID | Điều kiện riêng | Mục tiêu/căn cứ | Ngoại lệ và điều chỉnh |
| --- | --- | --- | --- |
| G02_AGGREGATE | `assessments_complete=true`; `0 < late <= submitted`; số đếm hợp lệ; tỷ lệ trong [0,1] | Mời kiểm tra vì có ít nhất một lần nộp trễ được xác nhận trong số liệu tổng hợp; không xác định bài nào | Kiểm tra lịch bài, hạn cá nhân và lý do trước khi giao nhiệm vụ. |
| G03 | `activity_complete=true`; total >0; click 7 ngày =0; click 30 ngày >0; số ngày không có click ≥7 | Xác minh cửa sổ 7 ngày không có click; mốc 7 theo định nghĩa cửa sổ dữ liệu, không phải ngưỡng nguy cơ được học | Kiểm tra cách học ngoài LMS và tính đầy đủ log. |
| G04 | `activity_complete=true`; total >0; click 30 ngày =0; số ngày không có click ≥30 | Xác minh cửa sổ 30 ngày; được xét trước G03 để không lặp tín hiệu | Không suy ra bỏ học. Tổng/cửa sổ/ngày hoạt động mâu thuẫn thì từ chối diễn giải. |

Giảng viên có thể không dùng gợi ý, sửa tiêu đề/nội dung/mục tiêu/ưu tiên trước khi giao; không sửa dữ liệu nguồn chỉ để gợi ý xuất hiện. Không có gợi ý không có nghĩa không cần hỗ trợ. Không triển khai G01 hoặc quy tắc theo bài khi chưa có dữ liệu chi tiết. Đánh giá chuyên gia và hiệu quả can thiệp thuộc ưu tiên 3, chưa được xác nhận bởi thay đổi này.
