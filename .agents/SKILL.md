---
name: ignore-pdf-files
description: Bỏ qua và không đọc/phân tích bất kỳ file PDF nào trong dự án để tránh tốn dung lượng context và bộ nhớ.
rules:
  - Do not read, parse, or process PDF files.
---

# Quy tắc xử lý File PDF

Agent **tuyệt đối không đọc, mở, quét (scan) hoặc phân tích nội dung các file PDF** (`.pdf`) nằm trong dự án dưới mọi hình thức.

### Hướng dẫn dành cho Agent:
1. **Phát hiện file PDF:** Nếu trong câu lệnh của người dùng hoặc trong kết quả tìm kiếm file có đề cập tới các file có đuôi `.pdf`, hãy bỏ qua việc đọc file đó.
2. **Khi được yêu cầu đọc PDF:** Nếu người dùng yêu cầu phân tích một file PDF cụ thể, hãy thông báo ngắn gọn:
   > *"Tôi được cấu hình để không đọc các file PDF trong dự án. Bạn vui lòng chuyển đổi nội dung file PDF sang định dạng văn bản (như `.txt` hoặc `.md`) nếu muốn tôi xử lý."*
3. **Các công cụ tìm kiếm / liệt kê file:** Không dùng các công cụ (tools) đọc file hoặc lấy text từ file PDF trong dự án.