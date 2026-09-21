# Dữ liệu đầu vào

Folder GitHub không kèm 7 file CSV gốc vì `studentVle.csv` có dung lượng lớn và cần kiểm tra quyền phân phối trước khi công khai.

Để chạy lại notebook, đặt đúng 7 file CSV trực tiếp vào folder `data/`:

- `studentInfo.csv`
- `studentRegistration.csv`
- `assessments.csv`
- `studentAssessment.csv`
- `studentVle.csv`
- `vle.csv`
- `courses.csv`

Các notebook dùng `data/` làm thư mục dữ liệu. Các notebook đã chạy sẵn và lưu output. Dữ liệu trung gian tại cutoff 50% không được đóng gói để tránh đưa bản ghi sinh viên lên GitHub; notebook sẽ tự tạo bảng này trong `ket_qua/` khi chạy lại với đủ dữ liệu đầu vào.

Dữ liệu được dùng là bộ OULAD đã được ẩn danh. Người dùng cần tự kiểm tra giấy phép và nguồn tải trước khi đưa dữ liệu gốc lên GitHub. Không đưa thông tin cá nhân, token hoặc file dữ liệu chưa được phép công khai.