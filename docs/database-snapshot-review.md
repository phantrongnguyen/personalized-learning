# Rà soát nguồn snapshot từ database — 21/10/2026

## Phạm vi và dữ liệu hiện có

Theo yêu cầu sử dụng database hiện tại, công cụ kiểm kê đọc `student_feature_snapshots`, enrollment và thời lượng/ngày bắt đầu học phần bằng transaction read-only. Không xuất tên, mã sinh viên, email, mật khẩu hoặc URL kết nối.

Kết quả local ngày 21/10: **2 snapshot, 0 bản có `support_evidence`**, trong đó 1 `synthetic_demo`, 1 chưa xác nhận nguồn; cả hai trả `insufficient_data`. Metadata hiện có gồm `note`, `cutoff_day`, `data_source`, `assessments_due`, `assessment_score`. Không có bảng log hoạt động hoặc lịch/bài/hạn nộp chi tiết trong 20 bảng public hiện tại.

Các số trong DB có thể nhất quán nhưng chưa chứng minh nguồn đầy đủ. Một trường `cutoff_day` hoặc số bài đến hạn trong JSON không tự thay thế người xác minh, thời điểm quan sát và phạm vi log/assessment được đối chiếu. Không nâng hai snapshot này thành dữ liệu LMS đã xác minh.

Chạy lại kiểm kê:

```powershell
.venv/Scripts/python.exe scripts/inspect_support_evidence.py --output reports/test-results/priority2-inventory.json
```

## Trách nhiệm và ba phạm vi rà soát

Người xác nhận là **tài khoản giảng viên được phân công đúng lớp học phần**. Server lấy danh tính từ JWT và ghi vào audit, không nhận tên/người xác nhận hoặc thời gian xác nhận do client tự khai. Quyền ADMIN không tự bỏ qua phân công học phần.

| Phạm vi | Khi sử dụng | Cách xử lý |
| --- | --- | --- |
| `aggregate_only` | Chỉ đối chiếu các số đang có trong database | Hai cờ đầy đủ phải false. Vẫn `insufficient_data`, không mở G02/G03/G04. |
| `source_verified` | Giảng viên đã kiểm tra nguồn và độ đầy đủ của ít nhất một phạm vi | Ghi tham chiếu, nội dung đã kiểm tra và xác nhận riêng log hoạt động/bài đánh giá. Không cho dùng với snapshot mang nhãn `synthetic_demo`. |
| `demonstration` | Kiểm chứng quy trình trên dữ liệu minh họa | Bản mới bắt buộc mang `synthetic_demo`, gợi ý/UI cảnh báo minh họa. Không dùng kết quả làm bằng chứng LMS thực. |

Các checkbox mặc định false. Kiểm tra nội bộ không tự bật chúng. `source_verified` là **xác nhận có trách nhiệm của người được phân quyền**, không phải hệ thống tự kiểm toán nguồn hoặc bảo đảm lời khai là đúng. Chỉ chọn nếu có nguồn để đối chiếu; khi chỉ có database tổng hợp như hiện tại, dùng `aggregate_only` hoặc minh họa.

## Quy trình sử dụng trên giao diện giảng viên

1. Chọn học phần và sinh viên, mở **Xem gợi ý**.
2. Mở **Rà soát và xác nhận nguồn snapshot**, bấm **Đọc snapshot từ database**. Kiểm tra nguồn, cutoff, từng chỉ số và lỗi nhất quán; đây là thao tác chỉ đọc.
3. Chọn phạm vi phù hợp; nhập tham chiếu và nội dung đã đối chiếu (ít nhất 20 ký tự). Nếu thực sự đã kiểm tra nguồn, xác nhận riêng từng loại dữ liệu đầy đủ đến cutoff. Đọc giới hạn và xác nhận trách nhiệm trước khi lưu.
4. Server kiểm tra quyền, enrollment, snapshot mới nhất, hash nội dung, cutoff và số liệu; từ chối dữ liệu thay đổi hoặc mâu thuẫn. Server **tạo snapshot mới**, sao chép chỉ số, thêm metadata/audit trong cùng transaction; không sửa bản cũ, không tự dự báo, tạo plan hoặc task.
5. UI tải lại gợi ý và xóa lựa chọn/nháp cũ. Bản mới chưa có PredictionRun thì hiển thị chưa dự báo. Cần chạy luồng dự báo hiện có, rồi cố vấn/admin lập plan ACTIVE đúng enrollment nếu chưa có kế hoạch phù hợp.
6. Giảng viên xem căn cứ, chọn gợi ý để điền nháp, sửa nội dung/mục tiêu/ưu tiên rồi chủ động giao. Request kèm snapshot và rule đã chọn; server kiểm tra lại gợi ý trước khi lưu task và audit. Snapshot đổi hoặc rule không còn đủ căn cứ trả 409, không dùng lựa chọn cũ.
7. Giao thủ công vẫn là quyết định riêng của giảng viên: UI yêu cầu căn cứ tự xác minh và ghi vào mô tả nhiệm vụ; không coi thao tác này là gợi ý tự động đã được chứng minh. Các trường mới của task là tùy chọn để giữ tương thích client cũ; backend chưa bắt buộc `verified_basis` cho mọi request giao thủ công.

## API và tính toàn vẹn

- `GET /api/v1/lecturer/courses/{presentation_id}/students/{student_id}/suggestions`: bổ sung `snapshot_id`, `data_source` để mở đúng snapshot cần rà soát.
- `GET /api/v1/lecturer/courses/{presentation_id}/students/{student_id}/snapshots/{snapshot_id}/review`: trả chỉ số, hash, nguồn, cutoff, lỗi và giới hạn. Không ghi dữ liệu.
- `POST` cùng URL: xác nhận phạm vi và lưu bản mới. Body gồm `snapshot_sha256`, `review_scope`, `source_reference`, `review_note`, `activity_complete`, `assessments_complete`, `acknowledged_limitations=true`. Các trường không khai báo bị từ chối.
- `POST /api/v1/lecturer/courses/{presentation_id}/tasks`: thêm cặp tùy chọn `suggestion_snapshot_id`/`suggestion_rule_id` và `verified_basis`; phải có cả hai tham chiếu khi giao từ gợi ý. Có audit `ASSIGN_COURSE_TASK` lưu enrollment, plan, snapshot/rule được chọn và người giao.

Metadata `support_evidence` mới có version `database-snapshot-review-1`, phạm vi, người/thời điểm xác nhận, tham chiếu, ghi chú, liên kết/hash bản cũ, hash bản mới và hai cờ riêng. Hash ràng buộc ID snapshot/enrollment, chỉ số, cutoff và mốc học phần; giúp phát hiện nội dung thay đổi, **không phải chữ ký xác thực hoặc bằng chứng nguồn đầy đủ**. Quyền DB đặc quyền vẫn có thể sửa/giả metadata; audit và quản lý quyền DB cần được duy trì.

Rule version tăng thành `lecturer-support-1.1` để yêu cầu xác nhận gắn với đúng snapshot/người phụ trách. Metadata kiểu cũ thiếu version/hash không tự được tin cậy. Các điều kiện tín hiệu G02_AGGREGATE/G03/G04 vẫn giữ nguyên; chỉ mở theo phạm vi đã xác nhận. Thay đổi số liệu đánh giá tạo snapshot mới và xóa `support_evidence` kế thừa, bắt buộc rà soát lại.

Khóa enrollment khi xác nhận hoặc giao từ snapshot để tránh dùng bản cũ trong các luồng sửa đang có; khóa plan khi giao task. Không thêm bảng/cột hoặc migration, không thay artifact/ngưỡng model.

## Giới hạn và điều kiện xác nhận hoàn tất

- Không có dữ liệu từng bài/hạn/gia hạn thì không xác định bài nào thiếu/trễ. G02 chỉ mời đối chiếu số tổng hợp, G03/G04 chỉ mô tả cửa sổ tại cutoff; dữ liệu cũ không phản ánh hiện tại.
- Kiểm thử tích hợp sử dụng database riêng và fixture minh họa, có chạy artifact thật để tạo PredictionRun trước khi tạo plan/task. Dữ liệu/test được rollback và database tạm được dọn. Không tạo gợi ý hoặc task demo trong database ứng dụng để báo hoàn thành.
- Điều kiện **nguồn LMS thực được người phụ trách xác minh** chưa được đáp ứng bởi hai snapshot hiện tại. Phần công cụ, phân quyền, kiểm tra và luồng tích hợp có thể được xác minh riêng; không gọi đó là hoàn tất kiểm chứng dữ liệu HUIT thực.
- Kiểm thử HTTP/DB và component không thay thế bộ E2E trình duyệt đầy đủ thuộc ưu tiên 4. Đánh giá chất lượng/hiệu quả gợi ý vẫn thuộc ưu tiên 3.
