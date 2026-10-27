# DÀN Ý CHƯƠNG 5. PHÂN TÍCH VÀ THIẾT KẾ HỆ THỐNG

**Đề tài:** Hệ thống gợi ý chiến lược học tập cá nhân hóa sử dụng thuật toán Human Conception Optimization cải tiến với Variable Neighborhood Local Search.

**Căn cứ:** [Đề cương khóa luận cử nhân](../../docs/product/thesis-proposal.md), [use case hiện có](../../database/use_case_diagram.md), [thiết kế cơ sở dữ liệu](../../database/database_design_plan.md) và các quy tắc nghiệp vụ của ứng dụng.

**Mục tiêu chương:** xác định hệ thống cần giải quyết những nghiệp vụ nào, ai sử dụng, dữ liệu và các thành phần tương tác ra sao; từ đó thiết kế kiến trúc, cơ sở dữ liệu, giao tiếp và giao diện làm cơ sở cài đặt ở Chương 6.

**Định hướng trình bày:** tập trung vào yêu cầu và quyết định thiết kế. Cấu hình thư viện, đoạn mã, ảnh giao diện thực tế, lệnh triển khai và kết quả kiểm thử trình bày ở Chương 6. Các sơ đồ/bảng dưới đây là sản phẩm cần chuẩn bị khi viết chương hoàn chỉnh, không mặc nhiên đã được tạo hoặc nghiệm thu.

## 5.1. Phân tích bài toán và phạm vi hệ thống

### 5.1.1. Bối cảnh và vấn đề cần giải quyết

- Dữ liệu học tập phân tán giữa thông tin học phần, hoạt động trên LMS và tình hình nộp bài.
- Người học cần biết tình hình của bản thân và các hành động có thể thực hiện; giảng viên/cố vấn cần thông tin để ưu tiên xem xét hỗ trợ.
- Hệ thống cần kết nối nhận diện nguy cơ với gợi ý có căn cứ và quy trình giao, theo dõi nhiệm vụ.
- Mô tả nhu cầu bằng tình huống minh họa; không coi đây là kết quả khảo sát người dùng thực tế nếu chưa thu thập khảo sát.

### 5.1.2. Mục tiêu và phạm vi chức năng

- Tiếp nhận thông tin sinh viên, học phần và hành vi học tập theo hợp đồng dữ liệu.
- Dự báo nguy cơ từ mô hình LightGBM với tập đặc trưng được HCO–VNLS lựa chọn.
- Cung cấp gợi ý minh họa hoặc gợi ý dựa trên căn cứ theo từng luồng nghiệp vụ.
- Hỗ trợ giảng viên/cố vấn xem xét, điều chỉnh và giao nhiệm vụ; sinh viên theo dõi và cập nhật hoàn thành.
- Quản lý tài khoản, phân công, dữ liệu và lịch sử liên quan trong phạm vi ứng dụng.

### 5.1.3. Ranh giới và giả định thiết kế

- Phân biệt dữ liệu OULAD lịch sử, dữ liệu tổng hợp minh họa và dữ liệu thực được xác nhận.
- Phân biệt huấn luyện/chọn đặc trưng ngoại tuyến với suy luận trong ứng dụng; không chạy HCO–VNLS lại cho mỗi sinh viên.
- Hệ thống hỗ trợ quyết định, không tự kết luận nguyên nhân học yếu hoặc thay giảng viên quyết định hỗ trợ.
- Chưa giả định có kết nối LMS thời gian thực, ánh xạ OULAD sang HUIT hoặc kiểm chứng hiệu quả can thiệp khi chưa có bằng chứng.

**Minh chứng đề xuất:** Hình 5.1 — Sơ đồ ngữ cảnh; Bảng 5.1 — Mục tiêu, phạm vi và giả định.

## 5.2. Phân tích tác nhân và yêu cầu hệ thống

### 5.2.1. Các tác nhân

| Tác nhân | Nhu cầu chính | Phạm vi dữ liệu |
| --- | --- | --- |
| Quản trị viên | Quản lý tài khoản, đào tạo, phân công và model theo nghiệp vụ được hỗ trợ | Các thao tác quản trị được cấp quyền |
| Cố vấn học tập | Theo dõi nguy cơ, lập và theo dõi kế hoạch hỗ trợ | Lớp và sinh viên được phân công |
| Giảng viên | Xem lớp học phần, căn cứ, gợi ý và giao nhiệm vụ | Học phần/lớp học phần được phân công |
| Sinh viên | Xem thông tin, dự báo, nhiệm vụ và gửi yêu cầu trợ giúp | Hồ sơ và enrollment của bản thân |

- Giới thiệu “người dùng hệ thống” như actor tổng quát cho các chức năng chung.
- Database, LightGBM và service nội bộ là thành phần bên trong, không vẽ thành actor nghiệp vụ bên ngoài.
- Nếu thể hiện bên gọi API công khai, giới hạn ở chức năng thực được mở; không suy ra có dự báo ẩn danh.

### 5.2.2. Yêu cầu chức năng

Đề xuất mã yêu cầu để truy vết trong báo cáo; đây không phải tên endpoint hoặc mã use case có sẵn.

| Mã đề xuất | Nhóm yêu cầu | Nội dung |
| --- | --- | --- |
| FR-01 | Tài khoản | Đăng nhập, quản lý phiên, hồ sơ và quyền truy cập |
| FR-02 | Quản lý đào tạo | Quản lý/tra cứu lớp, học phần, enrollment và phân công theo quyền |
| FR-03 | Dữ liệu học tập | Tiếp nhận, kiểm tra, lưu snapshot và nguồn dữ liệu |
| FR-04 | Dự báo | Kiểm tra đầu vào, tính nguy cơ và truy vết kết quả |
| FR-05 | Gợi ý | Phân tích tín hiệu, kiểm tra căn cứ và phát gợi ý hoặc từ chối |
| FR-06 | Kế hoạch và nhiệm vụ | Xem xét, điều chỉnh, giao và theo dõi hỗ trợ |
| FR-07 | Tương tác hỗ trợ | Ghi chú, yêu cầu trợ giúp và nhắc nhở theo chức năng hiện có |
| FR-08 | Tra cứu và quản trị | Lịch sử, báo cáo, audit và phiên bản model theo quyền |

Với từng yêu cầu, ghi tác nhân, đầu vào/đầu ra, điều kiện chấp nhận và trạng thái đã có/dự kiến sau khi đối chiếu cài đặt. API đã có không đồng nghĩa có giao diện hoàn chỉnh.

### 5.2.3. Yêu cầu phi chức năng

- Bảo mật: xác thực, kiểm tra quyền theo bản ghi và bảo vệ thông tin cá nhân.
- Toàn vẹn: ràng buộc dữ liệu, chống nhầm enrollment và giữ nguồn gốc dự báo.
- Khả dụng khi dữ liệu thiếu: thông báo trạng thái rõ ràng, không mặc định an toàn.
- Dễ sử dụng: bố cục theo vai trò, phản hồi lỗi và dữ liệu đầu vào dễ hiểu.
- Khả năng bảo trì/tái lập: tách trách nhiệm, quản lý cấu hình và phiên bản artifact.
- Hiệu năng: xác định thao tác, quy mô dữ liệu, môi trường và ngưỡng mong muốn để kiểm tra; không ghi thời gian đáp ứng cụ thể như kết quả đã đo nếu chưa có benchmark.

**Minh chứng đề xuất:** Bảng 5.2 — Tác nhân; Bảng 5.3 — Yêu cầu chức năng; Bảng 5.4 — Yêu cầu phi chức năng và cách kiểm chứng.

## 5.3. Mô hình hóa use case và phân quyền

### 5.3.1. Biểu đồ use case tổng quát

- Vẽ ranh giới hệ thống và bốn vai trò nghiệp vụ.
- Nhóm use case chung, quản trị, dự báo, giảng viên, cố vấn và sinh viên.
- Đăng nhập là điều kiện trước của thao tác được bảo vệ; không bắt buộc vẽ `include` đăng nhập ở mọi use case.
- Chỉ dùng `include`/`extend` khi có ý nghĩa nghiệp vụ UML; không dùng để biểu diễn thao tác xảy ra trước/sau.
- Tham khảo danh mục hiện có nhưng không ép một endpoint phải tương ứng một mục tiêu người dùng độc lập.

### 5.3.2. Biểu đồ use case theo vai trò

- Quản trị: quản lý tài khoản, phân công và các chức năng quản trị liên quan.
- Cố vấn: theo dõi sinh viên, xem nguy cơ, lập/theo dõi kế hoạch hỗ trợ.
- Giảng viên: xem học phần, kiểm tra căn cứ, điều chỉnh và giao nhiệm vụ.
- Sinh viên: xem dự báo, nhiệm vụ, cập nhật hoàn thành và yêu cầu trợ giúp.

### 5.3.3. Đặc tả use case trọng tâm

Chuẩn bị bảng đặc tả cho: đăng nhập; dự báo nguy cơ; rà soát căn cứ và xem gợi ý; giao nhiệm vụ; sinh viên hoàn thành nhiệm vụ; cố vấn theo dõi hỗ trợ.

Mỗi đặc tả gồm mã/tên, mục tiêu, tác nhân, kích hoạt, điều kiện trước, luồng chính, luồng thay thế, lỗi và hậu điều kiện.

- **Dự báo nguy cơ:** người dùng có quyền cung cấp đầu vào hợp lệ hoặc chọn snapshot phù hợp; hệ thống xác minh model, suy luận và trả kết quả theo hợp đồng. Ngoại lệ gồm dữ liệu không hợp lệ, thiếu snapshot hoặc artifact lỗi. Hậu điều kiện ghi rõ trường hợp nào được lưu lịch sử, tránh mặc định mọi lượt nhập tay đều tạo bản ghi nghiệp vụ.
- **Giao nhiệm vụ từ gợi ý:** giảng viên được phân công xem căn cứ hợp lệ, chọn/điều chỉnh gợi ý rồi xác nhận giao. Ngoại lệ gồm căn cứ thiếu, snapshot/rule thay đổi hoặc ngoài phạm vi. Hậu điều kiện là nhiệm vụ gắn đúng enrollment/kế hoạch và có thông tin truy vết theo cài đặt.

### 5.3.4. Ma trận phân quyền

- Lập bảng vai trò × chức năng × phạm vi dữ liệu.
- Phân biệt quyền thực hiện thao tác với quyền xem/sửa một bản ghi cụ thể.
- Không mặc định admin kế thừa toàn bộ portal của các vai trò; đối chiếu kiểm tra hồ sơ và phân công ở backend.

**Minh chứng đề xuất:** Hình 5.2 — Use case tổng quát; các hình 5.3a–5.3d theo vai trò; Bảng 5.5 — Đặc tả use case; Bảng 5.6 — Ma trận quyền.

## 5.4. Phân tích quy trình nghiệp vụ và quy tắc xử lý

### 5.4.1. Quy trình nhận diện nguy cơ

- Chọn enrollment/thời điểm quan sát hoặc nhập dữ liệu minh họa.
- Kiểm tra nguồn, schema, dữ liệu thiếu và các quan hệ nhất quán.
- Lấy model phù hợp, tính xác suất và xác định nhãn theo threshold.
- Trả kết quả và ghi nhận nguồn gốc theo luồng được thiết kế.

### 5.4.2. Quy trình đề xuất và thực hiện hỗ trợ

- Giảng viên/cố vấn xem dữ liệu, đối chiếu căn cứ và nhu cầu hỗ trợ.
- Hệ thống kiểm tra điều kiện quy tắc và quyết định phát gợi ý hoặc từ chối.
- Người có trách nhiệm điều chỉnh nội dung, xác định nhiệm vụ và giao hỗ trợ.
- Sinh viên xem nhiệm vụ, thực hiện và cập nhật trạng thái; giảng viên/cố vấn theo dõi.
- Hoàn thành nhiệm vụ là trạng thái phần mềm, không tự chứng minh cải thiện kết quả học tập.

### 5.4.3. Quy tắc và trạng thái cần mô hình hóa

- Thiếu dự báo khác với nguy cơ thấp; thiếu dữ liệu khác với giá trị bằng 0.
- Số bài trễ không vượt số bài đã nộp; các cửa sổ click và thời điểm quan sát phải nhất quán theo hợp đồng.
- Dữ liệu minh họa không được tự xác nhận là nguồn thực.
- Snapshot hoặc căn cứ thay đổi cần xử lý xác nhận theo hợp đồng; nêu rõ phạm vi toàn vẹn đã thiết kế và phần còn hạn chế.
- Gợi ý nhập tay và gợi ý giảng viên có căn cứ là hai luồng riêng; sao chép gợi ý không tự tạo nhiệm vụ.
- Giải thích các trạng thái `NOT_PREDICTED`, `insufficient_data`, `abstained` ở đúng thành phần sử dụng; không gộp thành một trạng thái duy nhất.
- Không xem radar tham chiếu là phân vị/năng lực hoặc suy ra nguyên nhân từ xác suất nguy cơ.

**Minh chứng đề xuất:** Hình 5.4 — Activity dự báo; Hình 5.5 — Activity hỗ trợ; Bảng 5.7 — Quy tắc nghiệp vụ và ngoại lệ.

## 5.5. Thiết kế kiến trúc hệ thống

### 5.5.1. Kiến trúc tổng thể

- Lớp trình bày: web frontend theo vai trò.
- Lớp API và nghiệp vụ: xác thực, kiểm tra dữ liệu, dự báo và hỗ trợ.
- Lớp dữ liệu: repository/ORM và PostgreSQL.
- Thành phần ML: pipeline tiền xử lý, LightGBM, metadata và registry.
- Quy trình thực nghiệm ngoại tuyến: HCO–VNLS chọn đặc trưng, đánh giá và xuất artifact.

### 5.5.2. Thiết kế mô-đun và trách nhiệm

- Tách quản lý người dùng, đào tạo, đặc trưng học tập, dự báo, quy tắc gợi ý, kế hoạch/nhiệm vụ và audit.
- Xác định dữ liệu vào/ra và phụ thuộc giữa các mô-đun.
- Giải thích lựa chọn tách dịch vụ nghiệp vụ với truy cập dữ liệu và mã suy luận.
- Phân biệt dữ liệu ứng dụng với dữ liệu/kết quả phục vụ nghiên cứu; xác định một nguồn mã ML chuẩn.

### 5.5.3. Luồng dữ liệu và tích hợp mô hình

- Nguồn học tập → đặc trưng theo cutoff → snapshot/đầu vào → dự báo → xem xét căn cứ → gợi ý → nhiệm vụ → theo dõi.
- Chỉ rõ phần nào dùng kết quả model, phần nào dùng quy tắc và phần nào cần con người quyết định.
- Định nghĩa giao tiếp qua schema, phiên bản model, cutoff, threshold và mã định danh nguồn.

**Minh chứng đề xuất:** Hình 5.6 — Kiến trúc tổng thể; Hình 5.7 — Sơ đồ thành phần và luồng dữ liệu.

## 5.6. Thiết kế dữ liệu và cơ sở dữ liệu

### 5.6.1. Mô hình dữ liệu khái niệm

- Xác định thực thể: tài khoản/hồ sơ, lớp, học phần, đợt mở học phần, enrollment, phân công, snapshot, model, dự báo, kế hoạch, nhiệm vụ và các thực thể hỗ trợ theo schema.
- Phân tích quan hệ, lực lượng và vai trò enrollment làm điểm nối dữ liệu học tập của một sinh viên trong một học phần cụ thể.
- Phân biệt hồ sơ sinh viên với một lượt đăng ký học; một sinh viên có thể có nhiều enrollment.

### 5.6.2. Mô hình quan hệ và từ điển dữ liệu

- Chuyển thực thể thành bảng với khóa chính/ngoại, kiểu dữ liệu, tính bắt buộc và giá trị mặc định.
- Mô tả ràng buộc duy nhất, CHECK, chỉ mục và chính sách cập nhật/xóa theo từng quan hệ.
- Chỉ đưa các bảng cốt lõi vào thân chương; từ điển đầy đủ đưa phụ lục hoặc dẫn chiếu tài liệu thiết kế.
- Đối chiếu số bảng với schema cuối trước khi nộp, không lấy số từ mô tả cũ.

### 5.6.3. Thiết kế snapshot, dự báo và căn cứ hỗ trợ

- Lưu dấu thời điểm quan sát, thời điểm ghi và nguồn dữ liệu; không dùng thời điểm ghi thay thời điểm quan sát.
- Dự báo gắn với đầu vào/snapshot và phiên bản artifact, cutoff, threshold theo hợp đồng hiện hành.
- Quản lý căn cứ, phạm vi rà soát, người xác nhận và liên kết đến quyết định giao nhiệm vụ.
- Giữ lịch sử phù hợp khi dữ liệu thay đổi; không ghi đè làm mất khả năng truy vết.
- Phân loại dữ liệu cá nhân, dữ liệu nghiên cứu và dữ liệu minh họa để xác định quyền truy cập.

**Minh chứng đề xuất:** Hình 5.8 — ERD; Bảng 5.8 — Thực thể cốt lõi; Bảng 5.9 — Từ điển dữ liệu rút gọn và ràng buộc.

## 5.7. Thiết kế tương tác và giao tiếp API

### 5.7.1. Sequence cho các luồng chính

- Đăng nhập: giao diện → API xác thực → dịch vụ → database → kết quả phiên.
- Dự báo: giao diện → kiểm tra quyền/schema → snapshot/model registry → suy luận → lưu/trả kết quả.
- Xem gợi ý và giao nhiệm vụ: giao diện giảng viên → kiểm tra phạm vi/căn cứ → quy tắc → xác nhận giao → database/audit.
- Hoàn thành nhiệm vụ: giao diện sinh viên → kiểm tra sở hữu/trạng thái → cập nhật → phản hồi để các bên theo dõi.
- Mỗi sequence có nhánh lỗi tiêu biểu; không vẽ mọi thao tác đọc dữ liệu như đều phát sinh ghi database.

### 5.7.2. Hợp đồng API đại diện

- Chia nhóm xác thực, quản trị, sinh viên, cố vấn, giảng viên và dự báo.
- Lập bảng method/path, tác nhân, request/response, điều kiện quyền, lỗi và tác động dữ liệu cho các API cốt lõi.
- Định nghĩa rõ xác suất, nhãn, dữ liệu thiếu, nguồn gợi ý và các định danh dùng để liên kết nghiệp vụ.
- Đối chiếu endpoint với OpenAPI/mã backend; chức năng dự kiến phải được đánh dấu riêng.

### 5.7.3. Thiết kế trạng thái và nhất quán

- Mô hình hóa vòng đời kế hoạch/nhiệm vụ bằng đúng tập trạng thái trong schema hiện hành.
- Nêu xử lý thao tác lặp, dữ liệu cũ và thay đổi snapshot; chỉ khẳng định chống lặp hoặc khóa đồng thời khi có cơ chế tương ứng.
- Phản hồi UI cần gắn đúng lớp/học phần đang chọn; đề xuất kiểm tra phản hồi về sai thứ tự.

**Minh chứng đề xuất:** Hình 5.9–5.12 — Sequence bốn luồng; Hình 5.13 — Trạng thái kế hoạch/nhiệm vụ; Bảng 5.10 — Hợp đồng API đại diện.

## 5.8. Thiết kế giao diện và trải nghiệm người dùng

### 5.8.1. Cấu trúc điều hướng

- Màn hình đăng nhập, điều hướng chung, hồ sơ và các trang theo vai trò.
- Xác định điểm vào, dữ liệu cần tải và hành động chính của từng màn hình.
- Chức năng chỉ xuất hiện phù hợp vai trò; backend vẫn phải kiểm tra quyền độc lập.

### 5.8.2. Thiết kế các màn hình trọng tâm

- Nhập thông tin/dự báo minh họa: nhóm trường, kiểm tra dữ liệu, xác suất và gợi ý.
- Cố vấn: danh sách lớp/sinh viên, tổng quan nguy cơ, kế hoạch và tiến độ.
- Giảng viên: học phần, sinh viên, thông tin/căn cứ, gợi ý và giao nhiệm vụ.
- Sinh viên: học phần, tình hình nguy cơ, kế hoạch/nhiệm vụ và yêu cầu trợ giúp.
- Quản trị: tài khoản, vai trò và các nghiệp vụ đã có màn hình; tránh giả định mọi API có giao diện.

### 5.8.3. Nguyên tắc hiển thị

- Phân biệt dữ liệu minh họa, dữ liệu chưa xác nhận và nguồn đã đối chiếu.
- Hiển thị tải/rỗng/lỗi/thiếu dữ liệu bằng thông báo và hành động phù hợp.
- Không chỉ dựa vào màu để truyền đạt nguy cơ; ghi nhãn, đơn vị, thời điểm và phạm vi.
- Mỗi gợi ý thể hiện căn cứ, nội dung hành động và bước xem xét của người phụ trách.
- Thể hiện bố cục thích ứng ở mức thiết kế, không khẳng định đã kiểm thử mọi thiết bị.

**Minh chứng đề xuất:** Hình 5.14 — Sơ đồ điều hướng; Hình 5.15a–5.15e — Wireframe các màn hình chính. Ảnh chụp ứng dụng đã cài đặt đưa ở Chương 6.

## 5.9. Thiết kế bảo mật, triển khai và tiêu chí nghiệm thu

### 5.9.1. Bảo mật và toàn vẹn

- Xác thực, phân quyền theo vai trò và kiểm tra phạm vi dữ liệu.
- Bảo vệ mật khẩu/token, quản lý biến môi trường và hạn chế lộ định danh trong báo cáo/log.
- Xác định phạm vi checksum artifact/căn cứ; checksum hỗ trợ kiểm tra thay đổi, không tự là chữ ký xác thực hoặc bằng chứng nguồn đầy đủ.
- Xác định yêu cầu lưu lịch sử, audit, backup/restore và chính sách phiên; phần chưa hiện thực phải nêu rõ.

### 5.9.2. Mô hình triển khai dự kiến

- Trình bày quan hệ browser, frontend, backend, PostgreSQL và nơi lưu artifact.
- Phân biệt cấu trúc triển khai local/Docker và yêu cầu bổ sung nếu mở rộng môi trường thực tế.
- Các cổng, lệnh chạy và cấu hình cụ thể trình bày ở Chương 6.

### 5.9.3. Truy vết và nghiệm thu yêu cầu

| Nhóm yêu cầu | Thành phần thiết kế | Minh chứng cần kiểm tra ở Chương 6 |
| --- | --- | --- |
| FR-01, FR-02 | Actor, quyền, dữ liệu tài khoản/đào tạo | Đăng nhập và truy cập đúng phạm vi |
| FR-03, FR-04 | Snapshot, model, hợp đồng dự báo | Dữ liệu hợp lệ, dự báo và truy vết đúng |
| FR-05, FR-06 | Quy tắc, căn cứ, kế hoạch/nhiệm vụ | Phát/từ chối gợi ý và giao nhiệm vụ đúng |
| FR-07, FR-08 | Tương tác hỗ trợ, lịch sử và audit | Cập nhật trạng thái và tra cứu theo quyền |
| Phi chức năng | Kiến trúc, bảo mật và xử lý ngoại lệ | Các ca kiểm thử/đo đạc có bằng chứng phù hợp |

Các tiêu chí là cơ sở thiết kế kiểm thử, không phải kết quả nghiệm thu đã đạt.

**Minh chứng đề xuất:** Hình 5.16 — Mô hình triển khai; Bảng 5.11 — Ma trận yêu cầu–thiết kế–kiểm thử.

## 5.10. Tổng kết chương

- Tóm tắt tác nhân, yêu cầu, quy trình và ranh giới nghiệp vụ đã phân tích.
- Chốt kiến trúc, mô hình dữ liệu, giao tiếp và thiết kế giao diện được chọn.
- Nêu các quyết định quan trọng: tách huấn luyện/suy luận, phân biệt dự báo/gợi ý, gắn dữ liệu với enrollment/snapshot và giữ con người quyết định hỗ trợ.
- Chuyển tiếp sang Chương 6 để trình bày hiện thực, màn hình, triển khai và kiểm thử; phần thiết kế còn dự kiến không được mô tả như đã cài đặt.

**Đoạn mở đầu tham khảo:**

> Chương này trình bày quá trình phân tích và thiết kế hệ thống gợi ý chiến lược học tập cá nhân hóa. Xuất phát từ yêu cầu của đề tài và nhu cầu sử dụng theo vai trò, chương xác định phạm vi chức năng, mô hình hóa các quy trình nghiệp vụ, đề xuất kiến trúc và thiết kế cơ sở dữ liệu, giao tiếp, giao diện. Thiết kế làm rõ mối liên hệ giữa dự báo nguy cơ bằng LightGBM với tập đặc trưng được HCO–VNLS lựa chọn và quy trình gợi ý, giao nhiệm vụ dựa trên căn cứ học tập.

## Nguồn đối chiếu và checklist hoàn thiện Chương 5

- [Yêu cầu đề tài](../../docs/product/thesis-proposal.md); [use case và tác nhân](../../database/use_case_diagram.md).
- [Schema chi tiết](../../database/database_design_plan.md); [sơ đồ database](../../docs/database/database_design.drawio).
- [Quy tắc nghiệp vụ](../../docs/product/business-rules.md); [quy trình rà soát snapshot](../../docs/database/database-snapshot-review.md).
- [Phân quyền backend](../../apps/backend/core/permissions.py); [router API](../../apps/backend/api/router.py); [mô hình dữ liệu](../../apps/backend/models/).
- [Giao diện và điều hướng](../../apps/frontend/src/App.tsx); [kiến trúc frontend](../../docs/frontend/architecture.md).

- [ ] Thống nhất thuật ngữ, mã yêu cầu và phạm vi với đề cương.
- [ ] Hoàn thiện UML/use case/activity/sequence theo đúng nghiệp vụ và quyền hiện hành.
- [ ] Đối chiếu ERD, trạng thái, khóa và ràng buộc với schema cuối.
- [ ] Đánh dấu rõ yêu cầu đã cài đặt, yêu cầu dự kiến và giới hạn.
- [ ] Tạo wireframe, hợp đồng API và ma trận truy vết; không dùng số endpoint làm số mục tiêu nghiệp vụ một cách máy móc.
- [ ] Đồng bộ với Chương 6: Chương 5 giải thích thiết kế, Chương 6 trình bày cách hiện thực và bằng chứng kiểm thử.
- [ ] Đánh số hình/bảng theo chương và kiểm tra các dẫn chiếu trong toàn quyển báo cáo.

---

# DÀN Ý CHƯƠNG 6. CÀI ĐẶT HỆ THỐNG

**Đề tài:** Hệ thống gợi ý chiến lược học tập cá nhân hóa sử dụng thuật toán Human Conception Optimization cải tiến với Variable Neighborhood Local Search.

**Căn cứ:** [Đề cương khóa luận cử nhân](../../docs/product/thesis-proposal.md), mã nguồn ứng dụng và quy trình thực nghiệm đang được duy trì trong repository.

**Mục tiêu chương:** trình bày cách chuyển kết quả nghiên cứu thành website minh họa, từ tổ chức mã nguồn, lưu trữ dữ liệu, tích hợp mô hình đến giao diện sử dụng và kiểm thử. Nội dung đáp ứng yêu cầu xây dựng website cho phép nhập thông tin sinh viên, dự báo nguy cơ, hiển thị gợi ý học tập và kiểm thử chương trình minh họa.

**Định hướng trình bày:** mỗi mục làm rõ thành phần được cài đặt, cách hoạt động, kết quả hiện thực và hình/bảng minh chứng. Phương pháp HCO–VNLS và phân tích so sánh mô hình được dẫn chiếu tới chương phương pháp/thực nghiệm, tránh lặp lại toàn bộ nội dung nghiên cứu. Các hình dưới đây là danh mục đề xuất, chưa phải ảnh đã chụp hoặc kết quả kiểm thử mới.

## 6.1. Môi trường và công nghệ cài đặt

### 6.1.1. Môi trường phát triển và chạy thử

- Trình bày môi trường phát triển trên Windows, công cụ quản lý mã nguồn Git và cấu trúc repository.
- Nêu cấu hình máy thực tế sử dụng: CPU, RAM, hệ điều hành và dung lượng lưu trữ; lấy thông tin từ máy chạy, không tự điền cấu hình giả định.
- Phân biệt môi trường Python phục vụ backend và môi trường tái thực nghiệm ML để tránh xung đột thư viện.
- Trình bày hai cách chạy: phát triển local và triển khai minh họa bằng Docker Compose.

### 6.1.2. Công nghệ sử dụng

| Thành phần | Công nghệ | Vai trò cần trình bày |
| --- | --- | --- |
| Backend | Python 3.12, FastAPI, Pydantic, Uvicorn | Xử lý API, kiểm tra dữ liệu và phục vụ yêu cầu ứng dụng |
| Truy cập dữ liệu | SQLAlchemy Async, asyncpg, Alembic | ORM, truy cập PostgreSQL và quản lý migration |
| Cơ sở dữ liệu | PostgreSQL 15 | Lưu tài khoản, học phần, snapshot, dự báo và kế hoạch hỗ trợ |
| Frontend | React 18, TypeScript, Vite 6, Tailwind CSS 3 | Xây dựng giao diện và tương tác với backend |
| Mô hình | scikit-learn, LightGBM, joblib | Pipeline tiền xử lý, suy luận và lưu/nạp artifact |
| Thực nghiệm | NumPy, pandas, LightGBM, CatBoost, XGBoost, Jupyter | Tạo dữ liệu, chọn đặc trưng và so sánh mô hình |
| Triển khai | Docker Compose, nginx | Đóng gói và kết nối các dịch vụ |
| Kiểm thử | pytest, Node test runner, Playwright | Kiểm tra backend, logic frontend và luồng trình duyệt |

Khi hoàn thiện quyển báo cáo, ghi phiên bản đã khóa từ file dependency/lockfile của đúng môi trường bàn giao; các ràng buộc phiên bản trong `package.json` không mặc nhiên là phiên bản thực tế đã cài.

**Minh chứng đề xuất:** Bảng 6.1 — Cấu hình môi trường; Bảng 6.2 — Công nghệ và thư viện sử dụng.

## 6.2. Tổ chức mã nguồn và các thành phần cài đặt

### 6.2.1. Tổ chức mã nguồn toàn hệ thống

- `apps/backend/`: API, nghiệp vụ, truy cập dữ liệu và suy luận mô hình.
- `apps/frontend/`: ứng dụng giao diện React.
- `packages/ml/`: quy trình thực nghiệm, chọn đặc trưng và đóng gói artifact nghiên cứu.
- `packages/shared/`: kiểu dữ liệu, hằng số và định nghĩa dùng chung cho các phần liên quan.
- `database/`, `docker/`, `docs/`, `reports/`, `tests/`: thiết kế dữ liệu, cấu hình triển khai, tài liệu, bằng chứng và kiểm thử.
- Phân biệt mã nguồn đang duy trì với dữ liệu sinh ra, kết quả lịch sử và artifact của từng lần chạy.

### 6.2.2. Tổ chức backend

- `api/`: khai báo router và endpoint.
- `schemas/`: cấu trúc request/response và kiểm tra miền dữ liệu.
- `services/`: nghiệp vụ xác thực, dự báo, quản lý model, radar và gợi ý hỗ trợ.
- `repositories/`, `models/`: truy cập dữ liệu và ánh xạ bảng.
- `core/`: cấu hình, kết nối database, bảo mật và kiểm tra quyền.
- `ml/`, `artifacts/`, `migrations/`: suy luận, artifact triển khai và cập nhật schema.

### 6.2.3. Tổ chức frontend

- `pages/`: các màn hình chức năng theo vai trò.
- `components/`: thành phần giao diện dùng lại.
- `services/`: gọi API, quản lý phiên và các thao tác dịch vụ.
- `state/`: trạng thái ứng dụng; `utils/`: các hàm hỗ trợ.
- Giải thích mối liên hệ giữa `App.tsx`, trạng thái phiên đăng nhập và màn hình được hiển thị.

**Minh chứng đề xuất:** Hình 6.1 — Sơ đồ thành phần cài đặt; Hình 6.2 — Cây thư mục rút gọn. Chỉ đưa thư mục có ý nghĩa, không liệt kê môi trường ảo hoặc dependency.

## 6.3. Cài đặt cơ sở dữ liệu

### 6.3.1. Khởi tạo và kết nối PostgreSQL

- Trình bày cấu hình kết nối bằng biến môi trường và cơ chế tạo phiên truy cập dữ liệu.
- Nêu cách khởi tạo database mới bằng script và cách nâng cấp database đã có bằng Alembic.
- Phân biệt script khởi tạo với migration; không mô tả thao tác xóa volume như bước nâng cấp dữ liệu thông thường.

### 6.3.2. Hiện thực các nhóm bảng nghiệp vụ

- Nhóm tài khoản, vai trò và hồ sơ người dùng.
- Nhóm lớp, học phần, đợt mở học phần, phân công và đăng ký học.
- Nhóm snapshot đặc trưng, phiên bản mô hình và lịch sử dự báo.
- Nhóm kế hoạch hỗ trợ, nhiệm vụ, yêu cầu trợ giúp, ghi chú và nhật ký thao tác theo schema hiện hành.
- Trình bày khóa chính, khóa ngoại, ràng buộc miền dữ liệu và chính sách giữ lịch sử ở các quan hệ tiêu biểu.

### 6.3.3. Lưu dữ liệu phục vụ dự báo và hỗ trợ

- Dùng enrollment làm đơn vị gắn sinh viên với một học phần/đợt mở cụ thể.
- Phân biệt thời điểm quan sát, thời điểm ghi snapshot và thời điểm dự báo.
- Giải thích việc tạo snapshot mới khi cập nhật dữ liệu thay vì làm mất đầu vào của dự báo cũ.
- Trình bày cách lưu đầu vào và danh tính artifact để hỗ trợ truy vết, replay và audit.

**Minh chứng đề xuất:** Hình 6.3 — Các nhóm bảng đã hiện thực; Bảng 6.3 — Dữ liệu lưu trong một lượt dự báo. Chi tiết schema dẫn chiếu phần thiết kế database.

## 6.4. Tích hợp mô hình HCO–VNLS và LightGBM

### 6.4.1. Chuyển kết quả nghiên cứu thành artifact

- Tóm tắt pipeline trong `packages/ml`: tạo đặc trưng theo cutoff, chia nhóm sinh viên, tìm mask, đánh giá và đóng gói.
- Làm rõ HCO–VNLS thực hiện lựa chọn đặc trưng; LightGBM thực hiện phân loại nguy cơ học tập.
- Giới thiệu cấu hình artifact đang triển khai: cutoff 75%, 17 đặc trưng gốc được chọn từ 38 đặc trưng, ngưỡng phân loại 0,50.
- Phân biệt 17 biến gốc với 30 chiều sau mã hóa của pipeline được báo cáo; không gọi cả hai là số đặc trưng đầu vào thô.
- Phân biệt artifact nghiên cứu tái chạy với artifact ứng dụng đang phục vụ. Việc tái thực nghiệm không tự thay model backend.

### 6.4.2. Nạp, kiểm tra và quản lý phiên bản mô hình

- Trình bày artifact joblib, metadata, danh sách/thứ tự feature, cutoff, threshold và checksum.
- Mô tả cơ chế lựa chọn model đang hoạt động dựa trên bản ghi database và kiểm tra artifact của `model_registry`.
- Nêu xử lý khi thiếu file, sai schema, không tương thích hoặc không xác minh được model.
- Giải thích lý do đóng gói cả tiền xử lý và bộ phân loại để đầu vào khi suy luận nhất quán với huấn luyện.

### 6.4.3. Quy trình suy luận

1. Tiếp nhận dữ liệu nhập hoặc lấy snapshot của enrollment được phép truy cập.
2. Kiểm tra trường bắt buộc, kiểu dữ liệu, miền giá trị và tính nhất quán.
3. Tạo đầu vào đúng schema, sử dụng pipeline đã fit; không fit lại tiền xử lý trên yêu cầu dự báo.
4. Tính xác suất lớp nguy cơ Fail/Withdrawn, áp dụng threshold của artifact.
5. Trả kết quả, lưu lịch sử theo luồng nghiệp vụ và hiển thị lên giao diện.

- Giải thích xác suất nguy cơ khác với kết luận chắc chắn trượt học phần.
- Phân biệt chưa dự báo/thiếu snapshot với kết quả an toàn; mô tả trạng thái `NOT_PREDICTED` khi phù hợp.
- Nếu trình bày giải thích dự báo, ghi đúng loại giải thích hiện có và giới hạn; không suy ra quan hệ nhân quả từ feature.

**Minh chứng đề xuất:** Hình 6.4 — Luồng tích hợp artifact vào API; Bảng 6.4 — Đầu vào/đầu ra dự báo; một đoạn mã ngắn minh họa bước kiểm tra và suy luận.

## 6.5. Cài đặt backend và nghiệp vụ gợi ý

### 6.5.1. Tổ chức API và hợp đồng dữ liệu

- Giới thiệu các nhóm router dưới `/api/v1`: xác thực, quản trị, sinh viên, cố vấn, giảng viên, dự báo và kiểm tra sức khỏe.
- Trình bày một số API đại diện cho luồng chính, gồm method/path thực tế, request, response, quyền và lỗi thường gặp.
- Giới thiệu OpenAPI/Swagger để tra cứu và thử API; không đưa toàn bộ danh sách endpoint vào thân chương.

### 6.5.2. Xác thực và phân quyền

- Đăng nhập, kiểm tra Bearer access token, tài khoản và trạng thái hoạt động.
- Phân quyền bốn vai trò: quản trị viên, cố vấn học tập, giảng viên và sinh viên.
- Kết hợp vai trò với phạm vi bản ghi: sinh viên của lớp phụ trách, enrollment hoặc học phần được phân công.
- Mô tả xử lý truy cập trái phép và phiên không hợp lệ theo mã hiện hành; chỉ khẳng định thu hồi phiên khi có cài đặt và kiểm thử xác nhận.

### 6.5.3. Cài đặt quy tắc gợi ý chiến lược học tập

- Trình bày quy tắc dựa trên dữ liệu hành vi/bài nộp và căn cứ học phần; phân biệt với model dự báo.
- Với mỗi nhóm gợi ý: nêu điều kiện, dữ liệu cần có, hành động đề xuất và trường hợp không đủ căn cứ.
- Giải thích cơ chế rà soát nguồn, dữ liệu minh họa và các trạng thái thiếu dữ liệu/từ chối.
- Mô tả quy trình giảng viên xem căn cứ, chọn gợi ý, điều chỉnh nội dung và chủ động giao nhiệm vụ.
- Nêu vai trò cố vấn trong kế hoạch hỗ trợ và theo dõi; sinh viên tiếp nhận, hoàn thành và gửi yêu cầu trợ giúp.
- Trình bày giới hạn: HCO–VNLS không trực tiếp tối ưu từng kế hoạch; hệ thống không tự chứng minh gợi ý làm tăng kết quả học tập.

### 6.5.4. Truy vết và xử lý ngoại lệ

- Lịch sử dự báo, nhật ký thao tác và quan hệ giữa snapshot, gợi ý, kế hoạch, nhiệm vụ.
- Xử lý dữ liệu mâu thuẫn, snapshot thay đổi, thiếu model và lỗi API.
- Trình bày đúng phạm vi checksum căn cứ đã cài đặt; các trường hợp chưa được bao phủ phải ghi là giới hạn.

**Minh chứng đề xuất:** Bảng 6.5 — API đại diện; Hình 6.5 — Luồng rà soát và giao nhiệm vụ; Bảng 6.6 — Một số quy tắc gợi ý kèm căn cứ.

## 6.6. Cài đặt giao diện người dùng

### 6.6.1. Giao diện chung và quản lý phiên

- Màn hình đăng nhập, thanh điều hướng, menu chức năng và hồ sơ cá nhân.
- Bố cục thích ứng, trạng thái tải, thông báo lỗi và phản hồi khi lưu thành công.
- Gọi API qua lớp dịch vụ và điều hướng màn hình theo phiên/nhóm quyền.
- Trình bày các chức năng phụ như avatar hoặc giao diện sáng/tối ở mức ngắn gọn, ưu tiên chức năng gắn với đề tài.

### 6.6.2. Giao diện nhập thông tin và dự báo minh họa

- Nhóm trường thông tin học phần, đặc điểm sinh viên và hành vi học tập theo schema model.
- Kiểm tra đầu vào, ví dụ dữ liệu hợp lệ và thông báo khi dữ liệu không nhất quán.
- Hiển thị xác suất, nhãn nguy cơ, radar và gợi ý minh họa theo chức năng thực có.
- Ghi rõ nguồn dữ liệu nhập tay/preset; radar dùng mốc tham chiếu minh họa, không tự gọi là phân vị hoặc phép đo năng lực.

### 6.6.3. Giao diện quản trị viên

- Quản lý tài khoản, tạo tài khoản, gán vai trò, khóa và đặt lại mật khẩu theo chức năng đã tích hợp.
- Phân biệt API quản trị đã có với chức năng có giao diện hoàn chỉnh; không mô tả mọi API như đã có màn hình.

### 6.6.4. Giao diện cố vấn học tập

- Danh sách lớp/sinh viên phụ trách và tổng quan nguy cơ.
- Xem tình hình theo học phần, radar, kế hoạch hỗ trợ và nhiệm vụ.
- Theo dõi tiến độ, ghi chú và báo cáo theo mức tích hợp thực tế.

### 6.6.5. Giao diện giảng viên

- Chọn lớp học phần, xem sinh viên và thông tin nguy cơ.
- Xem dữ liệu/căn cứ, rà soát nguồn và đọc gợi ý.
- Chọn gợi ý, sửa nháp, giao bài tập hoặc nhiệm vụ hỗ trợ.
- Minh họa tình huống hệ thống không phát gợi ý vì chưa đủ dữ liệu.

### 6.6.6. Giao diện sinh viên

- Xem học phần, thông tin dự báo, kế hoạch hỗ trợ và nhiệm vụ.
- Đánh dấu hoàn thành, xem nhắc nhở và gửi yêu cầu trợ giúp theo chức năng hiện hành.
- Phân biệt xác suất nguy cơ và hướng dẫn hành động; giải thích dữ liệu thiếu thay vì hiển thị như an toàn.

**Cách trình bày ảnh:** mỗi ảnh ghi vai trò, chức năng, dữ liệu sử dụng và thao tác chính. Ưu tiên một ảnh tổng quan cho mỗi nhóm chức năng, bổ sung ảnh chi tiết cho nhập liệu, dự báo và giao nhiệm vụ. Ẩn thông tin định danh và không đưa mật khẩu/token vào hình.

**Minh chứng đề xuất:** Hình 6.6–6.11 — Đăng nhập; nhập liệu/dự báo; quản trị; cố vấn; giảng viên; sinh viên. Số thứ tự ảnh điều chỉnh theo số ảnh thực tế khi biên soạn.

## 6.7. Cấu hình và triển khai chương trình minh họa

### 6.7.1. Cấu hình ứng dụng

- Cấu hình kết nối database, khóa bảo mật, URL API và vị trí artifact qua biến môi trường phù hợp.
- Sử dụng file cấu hình mẫu; không đưa giá trị bí mật từ `.env` vào báo cáo hoặc mã công khai.
- Phân biệt dữ liệu OULAD lịch sử, dữ liệu demo và dữ liệu thực được phép sử dụng.

### 6.7.2. Chạy trong môi trường phát triển

- Cài dependency backend và frontend theo hướng dẫn hiện hành.
- Khởi tạo/nâng cấp database đúng trạng thái; chuẩn bị artifact và tài khoản minh họa.
- Chạy backend tại cổng 8000, Vite dev server tại cổng 5173 theo cấu hình hiện tại.
- Kiểm tra kết nối database, sức khỏe backend và một yêu cầu dự báo hợp lệ.

### 6.7.3. Triển khai bằng Docker Compose

- Trình bày các dịch vụ PostgreSQL, pgAdmin, backend và frontend nginx.
- Giải thích mạng nội bộ, biến môi trường, healthcheck và volume lưu dữ liệu/avatar/archive model.
- Phân biệt cổng phát triển với cổng frontend Docker 3000 và cổng PostgreSQL công bố mặc định 5433.
- Mô tả build frontend, khởi động dịch vụ, kiểm tra hoạt động và lưu dữ liệu bền vững.
- Chỉ mô tả triển khai local/minh họa đã kiểm chứng; không tuyên bố đã triển khai production nếu chưa có bằng chứng.

**Minh chứng đề xuất:** Hình 6.12 — Sơ đồ triển khai; Bảng 6.7 — Dịch vụ, cổng và vai trò; một nhóm lệnh chạy ngắn đã kiểm tra trên phiên bản bàn giao.

## 6.8. Kiểm thử hệ thống và kịch bản minh họa

### 6.8.1. Phạm vi và môi trường kiểm thử

- Tách database kiểm thử khỏi dữ liệu ứng dụng; dùng tài khoản và dữ liệu minh họa có nguồn rõ ràng.
- Phân biệt unit test, kiểm thử API/tích hợp, kiểm thử logic frontend và E2E.
- Ghi commit/phiên bản, môi trường, ngày chạy và giới hạn của mỗi lượt kiểm thử.

### 6.8.2. Các nhóm trường hợp kiểm thử

| Nhóm | Trường hợp cần trình bày | Kết quả mong đợi |
| --- | --- | --- |
| Xác thực | Đúng/sai thông tin; token không hợp lệ; tài khoản bị khóa | Chỉ phiên hợp lệ được truy cập |
| Phân quyền | Truy cập chéo vai trò hoặc ngoài lớp/học phần phụ trách | Từ chối yêu cầu ngoài phạm vi |
| Dự báo | Đầu vào hợp lệ, thiếu trường, giá trị sai và thiếu snapshot | Dự báo đúng hợp đồng hoặc trả lỗi/trạng thái thiếu phù hợp |
| Model | Nạp artifact, schema và metadata | Kiểm tra được phiên bản và đầu vào theo hợp đồng |
| Gợi ý | Đủ căn cứ, thiếu căn cứ, số liệu mâu thuẫn | Phát gợi ý hoặc từ chối đúng điều kiện |
| Nhiệm vụ | Giảng viên giao; sinh viên nhận và hoàn thành | Dữ liệu và trạng thái cập nhật theo quyền |
| Lịch sử | Tạo snapshot mới, xem/replay dự báo cũ | Giữ được nguồn gốc và đầu vào lịch sử |
| Giao diện | Tải, rỗng, lỗi API và đổi học phần | Hiển thị trạng thái rõ ràng, dữ liệu đúng ngữ cảnh |

Khi viết kết quả, bổ sung cột “thực tế”, “đạt/chưa đạt” và đường dẫn bằng chứng; bảng trên là kế hoạch trình bày, không phải xác nhận các ca đã đạt.

### 6.8.3. Kịch bản minh họa xuyên suốt

1. Đăng nhập tài khoản đúng vai trò và chọn học phần/sinh viên được phép xem.
2. Nhập dữ liệu cho luồng dự báo minh họa hoặc lấy snapshot từ luồng nghiệp vụ.
3. Hiển thị nguy cơ và giải thích phạm vi của kết quả.
4. Giảng viên xem nguồn, rà soát căn cứ và đọc gợi ý của học phần.
5. Chọn gợi ý, điều chỉnh nội dung và giao nhiệm vụ hỗ trợ.
6. Sinh viên đăng nhập, xem nhiệm vụ và cập nhật hoàn thành.
7. Giảng viên/cố vấn xem trạng thái và lịch sử liên quan.

Dùng một tình huống đã chuẩn bị với nguồn dữ liệu rõ ràng cho các bước cần dữ liệu thực. Nhánh nhập tay là minh họa riêng, không tự được coi là snapshot đã xác nhận để giao nhiệm vụ. Bổ sung một tình huống thiếu căn cứ để minh họa xử lý ngoại lệ.

### 6.8.4. Tổng hợp kết quả và hạn chế kiểm thử

- Trình bày số ca đã chạy, số ca đạt/chưa đạt và lỗi còn lại theo bằng chứng của phiên bản bàn giao.
- Dẫn kết quả tái thực nghiệm ML khi cần, nhưng tách metric dự báo khỏi kiểm thử chức năng.
- Kiểm thử phần mềm không thay thế đánh giá chuyên gia về gợi ý hoặc đo tác động học tập.
- Chưa đo tải, khả năng chịu lỗi hoặc chạy thử thực địa thì nêu rõ, không suy ra từ việc chạy demo thành công.

**Minh chứng đề xuất:** Bảng 6.8 — Kết quả kiểm thử; Hình 6.13 — Luồng demo hoàn chỉnh; bảng ngắn liệt kê hạn chế còn lại.

## 6.9. Tổng kết chương

Nội dung cần chốt trong khoảng 1–2 đoạn:

- Hệ thống đã hiện thực các thành phần lưu trữ dữ liệu, API, suy luận mô hình và giao diện theo vai trò ở phạm vi được kiểm chứng.
- Website kết nối dự báo nguy cơ với quy trình xem căn cứ, gợi ý và giao nhiệm vụ do giảng viên/cố vấn kiểm soát.
- Nêu kết quả kiểm thử và khả năng chạy chương trình minh họa theo bằng chứng thực tế.
- Nhắc các giới hạn chính: OULAD là dữ liệu lịch sử, model tại cutoff 75%, chất lượng gợi ý và tác động học tập cần bằng chứng đánh giá riêng.

**Đoạn mở đầu tham khảo:**

> Chương này trình bày quá trình cài đặt hệ thống gợi ý chiến lược học tập cá nhân hóa dưới dạng ứng dụng web. Trên cơ sở phương pháp nghiên cứu và kết quả thực nghiệm đã trình bày, hệ thống tích hợp pipeline dự báo LightGBM với tập đặc trưng được lựa chọn bằng HCO–VNLS, kết hợp các quy tắc gợi ý dựa trên căn cứ học tập và quy trình xử lý theo vai trò. Nội dung chương tập trung vào môi trường cài đặt, tổ chức mã nguồn, cơ sở dữ liệu, backend, frontend, triển khai và kiểm thử chương trình minh họa.

## Nguồn đối chiếu khi phát triển thành nội dung hoàn chỉnh

| Nội dung | Nguồn trong dự án |
| --- | --- |
| Yêu cầu và phạm vi website | [Đề cương khóa luận](../../docs/product/thesis-proposal.md) |
| Môi trường backend | [requirements.txt](../../apps/backend/requirements.txt) |
| Môi trường frontend | [package.json](../../apps/frontend/package.json), [vite.config.ts](../../apps/frontend/vite.config.ts) |
| Schema và migration | [Thiết kế database](../../database/database_design_plan.md), [hướng dẫn migration](../../docs/database/migrations.md) |
| API | [Router](../../apps/backend/api/router.py), [README backend](../../apps/backend/README.md) |
| Model triển khai | [Model registry](../../apps/backend/services/model_registry.py), [metadata artifact](../../apps/backend/artifacts/THONG_TIN_MODEL_HCO_VNLS_LIGHTGBM_75.json) |
| Gợi ý và căn cứ | [Quy tắc nghiệp vụ](../../docs/product/business-rules.md), [support_suggestions.py](../../apps/backend/services/support_suggestions.py), [support_evidence.py](../../apps/backend/services/support_evidence.py) |
| Giao diện | [App.tsx](../../apps/frontend/src/App.tsx), [pages](../../apps/frontend/src/pages/), [README frontend](../../apps/frontend/README.md) |
| Triển khai | [docker-compose.yml](../../docker-compose.yml), [README gốc](../../README.md) |
| Thực nghiệm tái lập | [packages/ml](../../packages/ml/README.md), [kết quả tái chạy](../../packages/ml/reports/rerun-20261025/README.md) |
| Kiểm thử | [Hướng dẫn browser testing](../../docs/guides/browser-testing.md), [backend tests](../../apps/backend/tests/), [frontend E2E](../../apps/frontend/e2e/workflow.spec.ts) |

## Checklist hoàn thiện Chương 6

- [ ] Giữ số mục và tên chương phù hợp mục lục chung của quyển báo cáo.
- [ ] Bổ sung cấu hình máy và phiên bản dependency thực tế.
- [ ] Chụp màn hình từ phiên bản demo cuối; ẩn định danh và dùng dữ liệu được phép sử dụng.
- [ ] Đối chiếu từng màn hình/API được mô tả với chức năng đã hiện thực.
- [ ] Dẫn đúng artifact triển khai, không gán artifact tái chạy vào backend nếu chưa thay thế.
- [ ] Bổ sung bảng kiểm thử từ lần chạy có bằng chứng, không dùng kết quả mong đợi thay kết quả thực tế.
- [ ] Đồng bộ thuật ngữ: đặc trưng gốc/chiều mã hóa, nguy cơ/xác suất, gợi ý/nhiệm vụ, snapshot/thời điểm quan sát.
- [ ] Kiểm tra đánh số hình/bảng, chú thích, nguồn và liên kết dẫn chiếu sang các chương khác.
