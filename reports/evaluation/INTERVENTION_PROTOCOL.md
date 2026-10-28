# Giao thức theo dõi can thiệp — đề xuất, chưa thu thập

## Đơn vị, mốc thời gian và nguồn

- Đơn vị phân tích là enrollment (sinh viên × đợt mở học phần), không gộp mọi môn của một sinh viên thành một kết quả. Nếu một sinh viên có nhiều enrollment, ghi nhận sự phụ thuộc khi phân tích.
- `t0`: thời điểm giảng viên/cố vấn quyết định giao kế hoạch sau khi xem căn cứ. Khóa danh sách nhiệm vụ và mục tiêu tại t0 để xác định mẫu số; nhiệm vụ thêm sau đó được ghi riêng.
- Baseline: 7 ngày lịch kết thúc ngay trước t0; follow-up chính: 7 ngày ngay sau t0; theo dõi hoàn thành nhiệm vụ tại t0+14 ngày. Thu kết quả học phần ở thời điểm kết thúc học phần nếu được phép và có ánh xạ hợp lệ.
- Ghi rõ `observed_from`/`observed_to`, timezone, nguồn và người xác nhận. Snapshot cutoff 75% cũ và `created_at` không thay thế quan sát baseline/follow-up mới. Không lấy hai cửa sổ chồng lấn 7/30 ngày làm hai giai đoạn độc lập.
- Phân biệt synthetic_demo, nguồn chưa xác nhận và dữ liệu thực đã đối chiếu. Thiếu nguồn/tính đầy đủ thì để thiếu, không thay bằng 0.

## Thước đo định trước

| Thước đo | Công thức và điều kiện |
| --- | --- |
| Hoàn thành nhiệm vụ sau 14 ngày | Số task trong danh sách khóa tại t0 có `completed_at <= t0+14 ngày` / tổng task trong danh sách. Mẫu số 0 trả NA. Ghi riêng hủy/đổi nhiệm vụ. |
| Hoàn thành đúng hạn | Chỉ tính khi có hạn được thống nhất. Hiện task không có hạn riêng, chỉ có hạn kế hoạch: không tự suy ra mọi task đã trễ. |
| Tỷ lệ nộp bài từng giai đoạn | Bài đến hạn trong giai đoạn đã nộp theo quy định / bài đến hạn phải nộp trong giai đoạn; đối chiếu miễn/gia hạn và phạm vi nguồn. Mẫu số 0 trả NA, không gán 100%. |
| Ngày có hoạt động | Ngày có log trong giai đoạn / số ngày quan sát có nguồn đầy đủ; hai giai đoạn cùng định nghĩa. Hoạt động ngoài LMS là giới hạn cần ghi nhận. |
| Thay đổi hành vi | Follow-up trừ baseline của các tỷ lệ cùng đơn vị. Không so tổng click hai cửa sổ dài khác nhau. Báo n có đủ cặp dữ liệu và n thiếu. |
| Kết quả học tập | Chỉ so sánh khi định nghĩa điểm/xếp loại và thời điểm đánh giá tương thích trong cùng học phần. Không tự đổi Distinction OULAD sang xếp loại HUIT. |

## Nhóm so sánh và diễn giải

Nếu triển khai được, xác định trước nhóm so sánh có cùng học phần, mốc quan sát và điều kiện nguồn; ghi cách phân nhóm, tình trạng ban đầu, mức tiếp xúc với hỗ trợ, thay đổi giảng viên/lịch bài và can thiệp khác. Đề xuất này chưa phân nhóm hoặc giao nhiệm vụ cho sinh viên thật.

Nếu chỉ có trước/sau một nhóm, báo thay đổi mô tả và các giải thích thay thế (hạn bài, lịch thi, lựa chọn người tham gia, hồi quy về trung bình, thay đổi nguồn log); **không kết luận hiệu quả nhân quả**. Có nhóm so sánh cũng chưa tự bảo đảm nhân quả nếu chọn nhóm không tương đương. Không tối ưu nhóm hoặc mốc thời gian sau khi xem kết quả.

Đánh giá chuyên gia, thước đo model và hoàn thành task là ba loại bằng chứng khác nhau. Với dữ liệu hiện tại, kết quả quan sát can thiệp là **chưa có**, không phải “không có tác động”.

## Thu thập và quản lý

Giữ dữ liệu có định danh ngoài Git; dùng mã nghiên cứu, ghi mẫu số, cặp quan sát thiếu, lý do loại và lịch sử chỉnh sửa. Thống nhất người phụ trách nguồn và quyền sử dụng trước thu thập. Chưa liên hệ chuyên gia/sinh viên hoặc tự tạo dữ liệu thực địa trong công việc này.
