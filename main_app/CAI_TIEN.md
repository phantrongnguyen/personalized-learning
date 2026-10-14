# Các cải tiến hiện tại của main_app

Ngày ghi nhận: **11/10/2026**. Đây là bản cập nhật tạm thời; ứng dụng vẫn
cần được hoàn thiện trước khi dùng chính thức tại trường.

## Bổ sung: hồ sơ tương tự đã vượt qua nguy cơ

- Thêm mục đối chiếu lịch sử trên dashboard, dùng hồ sơ đã phân tích tại mốc 75%.
- Ghép cùng học phần, hành vi và lý do SHAP; chọn nhóm gần trước khi xét kết quả cuối kỳ.
- Báo cả số người đạt và không đạt/rút lui trong nhóm, hiển thị tối đa 3 hồ sơ đạt gần nhất.
- Mở từng hồ sơ để xem giá trị đối chiếu và diễn biến thật ở mốc 75%, 85%, 100%.
- Thư viện cục bộ dựng từ 3.447 enrollment test độc lập; không dựng ví dụ giả khi thiếu dữ liệu.
- Thư viện được giữ ngoài Git; công cụ dựng dữ liệu và hướng dẫn nằm trong source.
- Không diễn giải tương tự thành xác suất thành công hoặc thay đổi thành nguyên nhân nhân quả.

Chi tiết phương pháp, nguồn dữ liệu và cách chạy: [docs/DOI_CHIEU_LICH_SU.md](docs/DOI_CHIEU_LICH_SU.md).

## Bổ sung: Mục tiêu can thiệp khả thi (Actionable Counterfactual Recourse) và Kế hoạch tự điều chỉnh (SRL)

- Thêm khối **Kế Hoạch Đảo Ngược Nguy Cơ & Mục Tiêu Khả Thi** trên Dashboard ngay sau phần giải thích SHAP.
- **Thuật toán Phản thực nghiệm khả thi (Actionable Counterfactual Recourse - DiCE / Wachter et al.):**
  - Khóa hoàn toàn các biến nhân khẩu học và bối cảnh (tuổi, giới tính, học vấn, tín chỉ đăng ký, ngày đăng ký).
  - Tối ưu hóa đơn điệu các biến hành vi học tập (xóa ngày gián đoạn học tập, nâng số bài đánh giá nộp, tăng tương tác học liệu resource và liên kết url).
  - Cung cấp 2 kịch bản có căn cứ:
    1. **⚡ Can thiệp Cấp bách (Quick-Win Re-engagement):** Xóa chuỗi ngày gián đoạn và hoàn thành 1 bài đánh giá nợ để đưa xác suất về mức an toàn cơ bản.
    2. **🌱 Lộ trình Bền vững (Sustainable Mastery):** Duy trì nhịp học 3-4 ngày/tuần, tăng sâu lượt học liệu và hoàn thành 100% bài nộp để đưa nguy cơ xuống sâu dưới 30%.
- **Lý thuyết Học tập Tự điều chỉnh (Self-Regulated Learning - SRL, Pardo et al. 2019 / Zimmerman):**
  - Chuyển đổi các con số mục tiêu thành lộ trình 3 giai đoạn: Chuẩn bị & Kích hoạt lại (Forethought / 48h), Thực thi & Bù đắp nhiệm vụ (Performance / Tuần tiếp theo), Phản tỉnh & Rà soát cùng Cố vấn (Reflection).
- **Chế độ Thử nghiệm Kịch bản (What-if Simulation):**
  - Người dùng có thể nhấn **"Áp dụng vào Form (Thử nghiệm What-if)"** để tự động tải các giá trị mục tiêu vào form và kích hoạt mô hình LightGBM tính lại xác suất trực tiếp trong thời gian thực.
  - Cung cấp nút **"Khôi phục ban đầu"** để quay lại hồ sơ gốc bất kỳ lúc nào.
- **Minh bạch cơ sở khoa học:** Nêu rõ trích dẫn 4 bài báo quốc tế (Wachter 2017, Mothilal DiCE 2020, Pardo 2019, Karimi 2021) và các giới hạn học thuật (đo lường độ nhạy dự đoán, không thay thế nỗ lực học tập thực chất).

## Bổ sung: Giao diện Sinh viên Tối giản chạy song song (Student-Centric View)

- **Triết lý thiết kế phân quyền (Role-based UI):** Chạy song song 2 góc nhìn trong cùng 1 ứng dụng mà không làm mất công sức kỹ thuật trước đó:
  1. **🎓 Góc nhìn Sinh viên (Tối giản - Thân thiện):** Truy cập tại menu hoặc hash #student.
     - Loại bỏ hoàn toàn các thuật ngữ máy học kỹ thuật (log-odds, TreeSHAP, ma trận 17 biến).
     - **Thẻ trạng thái học tập:** Điểm độ sẵn sàng qua môn (Progress Gauge) và thông điệp động viên nhẹ nhàng.
     - **Checklist hành động tuần này (SRL Tasks):** Các nhiệm vụ cụ thể để sinh viên tick hoàn thành, kèm thanh tiến độ tiến độ hoàn thành tuần.
     - **Mục tiêu ngắn hạn khả thi (tính toán từ DiCE):** Con số cụ thể về số buổi học và bài tập cần hoàn thành.
     - **Kết nối Cố vấn:** Cung cấp modal gửi tin nhắn mẫu đến Cố vấn học tập của trường.
     - **Bộ chuyển đổi kịch bản (Scenario Selector):** 4 tình huống người học mẫu (Nợ bài tập, Gián đoạn học tập, Ít tương tác, Học lực vững) để kiểm chứng trực quan.
  2. **📊 Dashboard Cố vấn & Phân tích (Bản kỹ thuật đầy đủ):** Truy cập tại #dashboard.
     - Giữ nguyên 100% các công cụ đo lường chuyên sâu: 17 đặc trưng, TreeSHAP, DiCE What-if simulator, đối chiếu 3.447 ca lịch sử, biểu đồ radar năng lực.
- **Thanh chuyển đổi nhanh (Role Switcher):** Đặt ngay trên thanh Header/Navbar và Menu bên để chuyển đổi tức thời giữa 2 vai trò với 1 cú click.

## 1. Phạm vi và nguồn ứng dụng

- Lấy app từ nhánh `phantrongnguyen`, commit nguồn `de1970b`, tách vào `main_app`.
- Gồm React/Vite, FastAPI, kiểu dữ liệu dùng chung và artifact LightGBM.
- Không cần notebook, dữ liệu nghiên cứu hoặc báo cáo luận văn để chạy app.
- Không huấn luyện lại hoặc thay mô hình trong đợt cải tiến này.

## 2. Giải thích dự đoán cho từng hồ sơ

- Backend trả thêm ngưỡng phân loại và giải thích bằng LightGBM TreeSHAP.
- Cộng đóng góp sau mã hóa về **17 biến đầu vào gốc**, kèm giá trị và chiều tăng/giảm/trung tính.
- Kiểm tra mức nền cộng tổng đóng góp trên thang log-odds tái dựng đúng xác suất.
- Dashboard hiển thị mức nền, xác suất cuối cùng, chênh lệch tổng so với mức nền,
  ba yếu tố tăng và ba yếu tố giảm nổi bật; có thể mở bảng đầy đủ.
- Gợi ý hỗ trợ ưu tiên các yếu tố hành vi đóng góp tăng thực tế trong hồ sơ,
  thay vì chỉ dùng chiến lược cố định cho cùng mức xác suất.
- Tuổi, giới tính, học vấn và thông tin học phần/đăng ký được xem là bối cảnh,
  không phải mục tiêu thay đổi cá nhân để giảm dự đoán.
- Backend thiếu giải thích thì giao diện báo thiếu dữ liệu, không tự dựng nguyên nhân.

**Giới hạn:** SHAP giải thích cách mô hình tạo ra dự đoán nguy cơ trượt/bỏ học,
không chứng minh quan hệ nhân quả hoặc đánh giá toàn diện năng lực.
Đóng góp từng biến có đơn vị **log-odds**, không phải điểm phần trăm.
Các hành động hỗ trợ là mẫu do con người thiết kế, chưa chứng minh hiệu quả can thiệp.

## 3. Đồng bộ hồ sơ và kết quả

- Dự đoán, giải thích, radar và gợi ý dùng cùng bản chụp hồ sơ đã gửi.
- Sửa form không tự đổi kết quả cũ; dashboard nhắc phân tích lại.
- Khóa form trong lúc gửi yêu cầu để tránh lệch hồ sơ và kết quả.
- Ô số hỗ trợ nhập số thập phân.

## 4. Hạn chế tràn và che chữ

- Điều chỉnh vùng vẽ radar, giữ nhãn trong SVG và rút gọn/xuống dòng nhãn.
- Vùng hẹp dùng trục đánh số và danh sách tên đầy đủ bên dưới.
- Radar và bảng chỉ nằm song song khi thẻ chứa đủ rộng, sử dụng container query.
- Tách rõ giá trị hiện tại và chuẩn đối sánh; giá trị dài được xuống dòng.
- Chú giải, tiêu đề và thanh tìm kiếm/xuất lịch sử có thể xuống hàng.
- Menu bên có vùng cuộn để truy cập phần hệ thống trên màn hình thấp.

## 5. Xem chỉ số khi tương tác radar

- Rê chuột, chạm hoặc dùng bàn phím vào một trong sáu trục để xem chi tiết.
- Hiển thị tên đầy đủ, giá trị hồ sơ và chuẩn đối sánh; làm nổi bật điểm/hàng tương ứng.
- Chi tiết nằm dưới biểu đồ, không dùng hộp nổi đè lên nhãn.
- Hỗ trợ Tab, Enter/Space và Escape; chạm ra ngoài để đóng.
- Ghi rõ vị trí chuẩn hóa trên radar không phải xác suất rủi ro.

## 6. Lựa chọn giao diện trong Hệ thống

- Thêm **Hệ thống → Giao diện** trên menu bên và mục tương ứng ở trang hồ sơ.
- Ba lựa chọn: **Tối**, **Sáng — xanh dương & trắng**, **Theo thiết bị**.
- Giữ giao diện tối làm mặc định, không thay thế hoàn toàn màu sắc cũ.
- Lưu localStorage bằng khóa `edurisk_theme`, giữ qua tải lại và đồng bộ giữa các tab.
- Chế độ theo thiết bị cập nhật khi hệ điều hành đổi sáng/tối.
- Áp dụng lựa chọn trước khi React tải để hạn chế nháy màu khi mở trang.
- Đổi giao diện không làm mất dữ liệu nhập hoặc kết quả dự đoán đang xem.
- Giữ ý nghĩa xanh lá/đỏ/vàng cho tăng/giảm/cảnh báo.

## 7. Kiểm tra đã thực hiện

- Frontend: `npm run build` thành công sau các thay đổi giao diện.
- Backend đã khởi động, kiểm tra health và gọi dự đoán với model hiện tại.
- Đã thử radar ở các kích thước 280–2560 px, dọc/ngang, thu gọn menu,
  chữ gốc 200% và giá trị dài.
- Đã thử cả sáu trục bằng chuột, chạm và bàn phím.
- Đã thử sáng/tối/theo thiết bị, tải lại, đồng bộ tab và cấu hình không hợp lệ.
- Đã xem năm trang frontend ở giao diện sáng và kiểm tra vùng chọn giao diện
  trên màn hình nhỏ/màn hình ngang thấp.

Đây là kiểm tra cục bộ trên các trường hợp đã thử, không phải cam kết
mọi thiết bị đều tương thích hoặc chứng nhận sẵn sàng triển khai chính thức.

## 8. Chưa thực hiện — hướng cải tiến tiếp theo

- Dữ liệu học sinh/lớp/học kỳ thật, nguồn dữ liệu và thời điểm cập nhật.
- Quy trình hỗ trợ có người phụ trách, thời hạn, trạng thái và theo dõi kết quả.
- Đăng nhập, phân quyền, lưu trữ phía máy chủ và nhật ký thao tác thực sự.
- Kiểm chứng mô hình trên dữ liệu phù hợp với trường và đánh giá hiệu quả can thiệp.
- Chuẩn hóa nhận diện trường và màn hình phục vụ công việc hằng ngày.
- Bổ sung kiểm thử tự động, khả năng tiếp cận và tương thích trình duyệt.

Các nội dung này mới là định hướng, **không phải tính năng đã hoàn thành**.

## 9. Chạy app

Xem `README.md` để tạo môi trường backend và cài dependencies frontend.

- Backend: chạy từ `apps/backend` bằng Python của môi trường `.venv`:
  `python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload`.
- Frontend: từ `apps/frontend`, chạy `npm ci`, sau đó
  `node node_modules/vite/bin/vite.js --host 127.0.0.1 --strictPort`.
- Mở `http://127.0.0.1:5173/#dashboard`.
- Kiểm tra build: từ `apps/frontend`, chạy `npm run build`.
- CORS hiện dùng `allow_private_network=True`; cần Starlette hỗ trợ tham số này.
  Môi trường đã thử dùng Starlette 1.7.0.
- Không đưa `.venv`, `node_modules`, `dist`, `.env` hoặc ảnh kiểm tra cục bộ lên Git.


