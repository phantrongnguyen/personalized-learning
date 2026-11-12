# Tổng hợp công việc đã thực hiện — EduRisk AI

**Dự án:** KLTN 13 — Hệ thống gợi ý chiến lược học tập cá nhân hóa.  
**Người tổng hợp:** Phan Trọng Nguyên.  
**Cập nhật:** 02/11/2026.  
**Phạm vi:** công việc phát triển, tích hợp, nghiên cứu, kiểm thử và tài liệu được ghi nhận trong lịch sử nhánh `phantrongnguyen` và các báo cáo của repository.

Tài liệu này tổng hợp các công việc đã thực hiện theo nhóm và theo thời gian. Một số thành phần được tiếp nhận hoặc gộp từ thành viên khác; việc xuất hiện trên nhánh cá nhân không đồng nghĩa toàn bộ mã nguồn do một người tự xây dựng. Các kết quả kiểm thử lịch sử được dẫn về báo cáo gốc, không được coi là đã chạy lại toàn bộ tại ngày cập nhật.

## 1. Khởi tạo dự án và nghiên cứu nền tảng

- Khởi tạo repository, điều chỉnh đường dẫn dự án và tổ chức quản lý mã nguồn trên GitHub.
- Thu thập nguồn dữ liệu và tài liệu nghiên cứu liên quan, bổ sung danh mục tham khảo phục vụ khóa luận.
- Xây dựng tài liệu mô tả bài toán, đề cương, phân tích hệ thống và kiến trúc ứng dụng.
- Thiết lập quy ước Git, tên nhánh và Conventional Commits trong [`.agents/commit_github.md`](../.agents/commit_github.md).
- Khảo sát dữ liệu OULAD và cách chuyển dữ liệu học tập thành đặc trưng phục vụ dự báo.
- Trong giai đoạn đầu, từng bổ sung công cụ thu thập CAPTCHA và notebook CRNN; phần thu thập cũ đã được loại bỏ khi tập trung vào hệ thống học tập.

**Tài liệu:** [đề cương khóa luận](../docs/product/thesis-proposal.md), [phân tích và kiến trúc](../docs/architecture/system_analysis_and_architecture.md).

## 2. Nghiên cứu mô hình và xử lý dữ liệu

### 2.1. Các bước nghiên cứu ban đầu

- Xây dựng pipeline trích xuất đặc trưng OULAD theo hướng vector hóa.
- Xây dựng bước xử lý thiếu, mã hóa biến và chuẩn hóa dữ liệu.
- Triển khai các phiên bản nghiên cứu HCO, VNLS, HCO–VNLS; bổ sung GA và PSO làm baseline ở giai đoạn đầu.
- Xây dựng `LearningRecommendationEngine` và các notebook khảo sát dữ liệu, so sánh mô hình, lưu/nạp mô hình.
- Điều chỉnh dependency và khả năng nạp artifact pipeline scikit-learn cũ để tích hợp suy luận vào backend.

Các nội dung trên được ghi nhận trong lịch sử tháng 8–10. Mã huấn luyện cũ từng được loại bỏ và sau đó được thay bằng nguồn thực nghiệm được đồng bộ, hợp nhất. Không coi mọi thuật toán từng có trong lịch sử là thành phần đang được sử dụng trong pipeline hiện hành.

### 2.2. Đồng bộ mô hình và kết quả thực nghiệm

- Tiếp nhận, đồng bộ mã và notebook HCO–VNLS từ nguồn nghiên cứu của nhóm; chuẩn hóa tên thư mục và tài liệu thực nghiệm.
- Tích hợp artifact LightGBM tại cutoff 75%, schema 17 đặc trưng, threshold 0,5 và metadata nguồn gốc.
- Phân biệt xác suất lớp nguy cơ với nhãn dự báo; sử dụng threshold của artifact khi suy luận.
- Lập báo cáo model đã chốt, biểu đồ đánh giá và script đối chiếu metric/checksum.
- Phân biệt kết quả validation của model train-only với test của artifact sau fit train + validation; phân biệt AP với ROC-AUC.
- Bổ sung công cụ audit bằng chứng mô hình và kiểm tra mask đặc trưng, metadata, metric, nguồn notebook.

**Bằng chứng:** [báo cáo model](model_final/MODEL_FINAL.md), [script tạo biểu đồ](model_final/generate_charts.py), [audit mô hình](../scripts/audit_model_evidence.py).

### 2.3. Tái chạy và hợp nhất pipeline ML

- Hợp nhất nguồn mã chuẩn về [`packages/ml`](../packages/ml/README.md), gồm `research_code`, `shared_code`, notebook và dependency.
- Tách bảng kết quả lịch sử và provenance vào `history/`; loại bỏ các bản mã/bảng trùng trong thư mục thí nghiệm cũ.
- Xóa output lịch sử trong notebook nguồn; tách đầu ra theo từng run và bỏ qua dữ liệu cấp sinh viên/model sinh ra bằng Git ignore.
- Xây dựng runner có manifest, checksum mã/dữ liệu, phiên bản môi trường, trạng thái từng notebook và cơ chế tiếp tục run có kiểm soát.
- Tạo lại dữ liệu từ bảy bảng OULAD tại cutoff 50/60/65/70/75%; chia nhóm theo sinh viên với seed 41.
- Kiểm tra dữ liệu trùng, giới hạn thời gian quan sát và loại nhãn/ID/split khỏi đặc trưng.
- Tái chạy LightGBM, CatBoost, XGBoost với full features, HCO, VNLS và hybrid tại cutoff 50/75%.
- Tái chạy năm seed, 30 mask thuật toán và 240 mask ngẫu nhiên cùng kích thước; lưu trace và kiểm tra độ ổn định.
- Tái chạy ablation, xuất biểu đồ, đóng gói artifact mới và tính metric test từ dự đoán cấp enrollment.
- Xây dựng công cụ tổng hợp báo cáo và hợp nhất đầu ra trùng bằng ánh xạ vị trí kèm checksum.
- Hoàn tất run `rerun-20261025`; không thay thế artifact đang dùng ở backend.

Kết quả HCO–VNLS + LightGBM cutoff 75% tiếp tục chọn **17/38 đặc trưng**. Artifact mới fit trên **19.712 enrollment** train + validation, đánh giá trên **3.447 enrollment** test lịch sử:

| Chỉ số test | Kết quả |
| --- | ---: |
| Accuracy | 0,861909 |
| Precision nguy cơ | 0,912322 |
| Recall nguy cơ | 0,656997 |
| F1 nguy cơ | 0,763889 |
| Average precision | 0,881575 |
| ROC-AUC | 0,904932 |
| Brier score | 0,101370 |
| TN / FP / FN / TP | 2201 / 74 / 402 / 770 |

AP validation trong bảng đối chiếu ba bộ học khớp lịch sử. Đây là kiểm chứng khả năng tái lập giao thức cũ trên split OULAD lịch sử; chưa phải holdout mới hoặc bằng chứng hiệu quả can thiệp thực tế.

**Bằng chứng:** [báo cáo tái thực nghiệm](../packages/ml/reports/rerun-20261025/README.md), [báo cáo ngày 25/10](dailys/25-10-2026.md), [kiểm thử pipeline](../packages/ml/test_pipeline.py).

## 3. Backend và API nghiệp vụ

- Xây dựng backend FastAPI phục vụ suy luận, xác thực và các nghiệp vụ hỗ trợ học tập.
- Tổ chức mã theo API, schema, repository, service và model; dùng SQLAlchemy async với PostgreSQL.
- Bổ sung entry point chạy backend, cấu hình môi trường và khả năng phục vụ frontend build qua static mount.
- Xây dựng API cho bốn vai trò ADMIN, ADVISOR, LECTURER, STUDENT và tích hợp frontend với API.
- Xây dựng dự báo từ đặc trưng lấy trong database; sửa ghép đủ đầu vào, giao dịch lưu dự báo và dự báo riêng một enrollment.
- Lưu snapshot, đầu vào suy luận, danh tính model, threshold và lịch sử để truy vết/replay dự báo.
- Biểu diễn snapshot chưa được dự báo bằng `null`/`NOT_PREDICTED`; không mặc định đánh dấu an toàn.
- Bổ sung model registry, kiểm tra checksum/schema artifact và đồng bộ nguồn model giữa các luồng dự báo.
- Tối ưu truy vấn nguy cơ theo batch và phân trang danh sách sinh viên.
- Bổ sung audit log và xử lý rollback khi thao tác gặp ràng buộc dữ liệu.

**Bằng chứng:** [tài liệu backend](../apps/backend/README.md), [báo cáo ngày 14/10](dailys/14-10-2026.md), [báo cáo ngày 18/10](dailys/18-10-2026.md).

## 4. Xác thực, tài khoản và hồ sơ

- Xây dựng đăng nhập với JWT access/refresh token và mật khẩu băm bcrypt.
- Cho phép sinh viên đăng nhập bằng MSSV; các vai trò khác dùng email, đồng thời giữ tương thích payload đăng nhập cũ.
- Xây dựng giao diện/API quản lý tài khoản: cấp tài khoản theo vai trò, xem chi tiết, chỉnh sửa, khóa/mở khóa, xóa và đặt lại mật khẩu.
- Bổ sung kiểm tra tự khóa/tự xóa và kiểm tra dữ liệu đầu vào trong các thao tác quản trị.
- Xây dựng hồ sơ theo vai trò, chỉnh sửa họ tên/điện thoại và lối tắt tới không gian làm việc.
- Bổ sung tải avatar với kiểm tra định dạng, dung lượng, kích thước ảnh, chuẩn hóa JPEG và dọn ảnh cũ sau khi lưu thành công.
- Cải thiện frontend quản lý phiên: refresh dùng chung cho nhiều request, ngăn phản hồi cũ khôi phục phiên sau đăng xuất/chuyển tài khoản, tách lịch sử dự báo theo tài khoản.

**Bằng chứng:** [12/10](dailys/12-10-2026.md), [16/10](dailys/16-10-2026.md), [18/10](dailys/18-10-2026.md).

## 5. Các không gian làm việc theo vai trò

### 5.1. Quản trị viên

- Tích hợp trang quản lý tài khoản với danh sách phân trang, tìm kiếm/lọc và hộp thoại thao tác.
- Xây dựng các API quản lý học phần, lớp học phần, phân công, mô hình và dự báo hàng loạt.
- Bổ sung API tra cứu audit phục vụ truy vết thay đổi.

Phạm vi giao diện quản trị chưa bao phủ toàn bộ API đã có.

### 5.2. Cố vấn học tập

- Xây dựng danh sách lớp/sinh viên phụ trách, thống kê và tổng quan/radar sinh viên.
- Xây dựng kế hoạch can thiệp, nhiệm vụ, ghi chú tư vấn và xuất báo cáo nguy cơ Excel.
- Yêu cầu chọn enrollment khi sinh viên có nhiều học phần; gắn kế hoạch với dự báo đúng học phần.
- Tổng hợp trạng thái nguy cơ theo các học phần, phân biệt trường hợp thiếu dự báo.

### 5.3. Giảng viên

- Xây dựng danh sách lớp phụ trách, bảng nguy cơ, chi tiết sinh viên và cập nhật đánh giá/tiến độ.
- Xây dựng luồng xem căn cứ → chọn gợi ý → chỉnh sửa nháp → chủ động giao nhiệm vụ bổ trợ.
- Kiểm tra phân công giảng viên và plan ACTIVE đúng sinh viên/học phần trước khi giao nhiệm vụ.
- Bổ sung cảnh báo tới cố vấn, gắn học phần và xác định người nhận từ quan hệ phân công.
- Tích hợp giao diện giảng viên từ thành viên nhóm, tổ chức bốn tab tổng quan, dấu hiệu, gợi ý/giao nhiệm vụ và căn cứ.
- Tích hợp nhập dữ liệu OULAD, rà soát nguồn, biểu đồ đánh giá và lịch sử giao nhiệm vụ.

### 5.4. Sinh viên

- Xây dựng trang hồ sơ, danh sách học phần, dự báo/radar và kế hoạch can thiệp.
- Xem/hoàn thành nhiệm vụ và gửi/xem yêu cầu trợ giúp.
- Phân tách nhiệm vụ, yêu cầu trợ giúp và thao tác hoàn thành theo enrollment; xử lý phản hồi cũ khi chuyển môn.
- Bổ sung thông tin sinh viên, bộ lọc học kỳ và nhắc nhở nhiệm vụ chưa hoàn thành.
- Chuông thông báo mở đúng môn/học kỳ, cập nhật khi hoàn thành nhiệm vụ; trạng thái đã đọc được lưu riêng theo tài khoản.

Nhắc nhở hiện phục vụ trong ứng dụng, chưa triển khai email/SMS hoặc thông báo khi đóng trang.

**Bằng chứng:** [11/10](dailys/11-10-2026.md), [16/10](dailys/16-10-2026.md), [so sánh trước/sau gộp](dailys/20-10-2026.md), [rà soát tích hợp](dailys/22-10-2026.md).

## 6. Gợi ý học tập và kiểm soát căn cứ

- Xây dựng gợi ý theo các chỉ số học tập và tích hợp vào dashboard/luồng giảng viên.
- Chuẩn hóa hợp đồng dữ liệu và quy tắc; làm rõ giới hạn heuristic trên dữ liệu OULAD.
- Bổ sung rà soát snapshot và nguồn dữ liệu, audit quyết định và điều kiện sử dụng căn cứ.
- Từ chối diễn giải khi thiếu căn cứ hoặc JSON căn cứ sai định dạng; phân biệt `insufficient_data` và `abstained`.
- Không suy ra bài cụ thể bị thiếu/trễ chỉ từ chỉ số tổng hợp; mức nhiệm vụ do giảng viên lựa chọn.
- Thống nhất công thức radar bằng cấu hình dùng chung, ghi rõ mốc tham chiếu minh họa và tô đỏ các điểm thấp hơn mốc.
- Chuẩn bị bộ tình huống minh họa, công cụ tổng hợp đánh giá chuyên gia và giao thức theo dõi can thiệp.

**Bằng chứng:** [báo cáo 21/10](dailys/21-10-2026.md), [thực nghiệm và giới hạn](evaluation/THESIS_EXPERIMENTS.md), [giao thức can thiệp](evaluation/INTERVENTION_PROTOCOL.md).

## 7. Frontend và trải nghiệm sử dụng

- Xây dựng dashboard ban đầu và chuyển frontend sang React, TypeScript, Vite.
- Tạo types và hằng số đặc trưng dùng chung trong `packages/shared`.
- Xây dựng Home, About, Contact, đăng nhập, hồ sơ và các trang theo vai trò.
- Chuẩn hóa nhận diện HUIT, giao diện trắng/xanh dương, logo, sidebar, navbar và footer.
- Bổ sung theme lưu trạng thái, nền trang đăng nhập, menu hồ sơ và avatar dùng chung.
- Xây dựng form 17 đặc trưng, RiskGauge, radar, lịch sử phân tích và xuất CSV UTF-8 BOM.
- Sửa chồng lấn radar và các chi tiết bố cục/điều hướng; bỏ địa chỉ máy chủ khỏi nội dung dashboard.
- Trình bày metric đã đối chiếu, biểu đồ đánh giá mô hình tương tác và hộp thoại hướng dẫn sử dụng/mô hình.

**Bằng chứng:** [10/10](dailys/10-10-2026.md), [12/10](dailys/12-10-2026.md), [16/10](dailys/16-10-2026.md), [21/10](dailys/21-10-2026.md).

## 8. Database, bảo toàn dữ liệu và môi trường chạy

- Thiết lập PostgreSQL/pgAdmin bằng Docker Compose; bổ sung schema, dữ liệu khởi tạo và hướng dẫn chạy local.
- Xây dựng thiết kế database, sơ đồ ERD/use case, từ điển dữ liệu và mô tả quan hệ bảng.
- Chuẩn hóa SQL/ORM về 19 bảng; bổ sung Alembic `0002_normalize`, ràng buộc CHECK/UNIQUE và chính sách RESTRICT để giữ lịch sử.
- Bổ sung quy trình migration có kiểm tra điều kiện, backup/khôi phục và kiểm thử rollback.
- Kiểm tra quyền trên bản ghi: sinh viên sở hữu enrollment, giảng viên được phân công lớp, cố vấn được phân công sinh viên.
- Tách môi trường kiểm thử PostgreSQL, dùng fixture có rollback để hạn chế ảnh hưởng dữ liệu vận hành.
- Bổ sung runtime Docker cho backend/frontend và hướng dẫn khởi chạy tái lập.
- Loại dữ liệu riêng tư, môi trường, cache, ảnh tải lên và artifact sinh ra khỏi phạm vi Git phù hợp.

**Bằng chứng:** [thiết kế database](../database/database_design_plan.md), [migration](../docs/database/migrations.md), [18/10](dailys/18-10-2026.md), [19/10](dailys/19-10-2026.md).

## 9. Kiểm thử và bằng chứng xác minh

- Bổ sung unit test và kiểm thử API cho xác thực, quản trị, hồ sơ và nghiệp vụ học tập.
- Kiểm thử PostgreSQL cho phạm vi học phần, nhắc nhở, avatar, phân quyền, giao dịch và migration/rollback.
- Kiểm thử snapshot, danh tính artifact, lịch sử dự báo, trạng thái chưa dự báo và điều kiện giao nhiệm vụ.
- Bổ sung kiểm thử frontend cho quản lý phiên và các hành vi dữ liệu/giao diện liên quan.
- Xây dựng và từng chạy Playwright E2E trên ứng dụng thật với PostgreSQL riêng cho chuỗi can thiệp; một số dữ liệu chuẩn bị qua API/DB có guard.
- Bổ sung test cho kiểm tra metric, chống thay đổi bằng chứng, tạo biểu đồ và giao thức pipeline ML.
- Thực hiện build frontend, kiểm tra diff và lưu kết quả theo từng báo cáo công việc.

Trong phiên ngày **02/11/2026**, trước khi commit/push, đã chạy thành công **7 kiểm thử pipeline ML** và **16 kiểm thử bằng chứng đánh giá/tạo biểu đồ**. Bộ pytest có một cảnh báo deprecation cấu hình Pydantic. Đây là **23 kiểm thử liên quan**, chưa phải kết quả chạy toàn bộ dự án hoặc E2E mới nhất.

Báo cáo ngày 22/10 ghi nhận locator E2E chưa khớp giao diện giảng viên sau gộp; kết quả E2E cũ không đủ để xác nhận phiên bản tích hợp hiện tại.

## 10. Tài liệu, rà soát và bàn giao GitHub

- Viết hướng dẫn backend, kiểm thử API bằng Postman, cấu hình và chạy frontend/backend.
- Cập nhật README, kiến trúc, thiết kế database, hợp đồng dữ liệu/quy tắc gợi ý và tài liệu model.
- Viết báo cáo tiến độ, phân tích trước/sau gộp, rà soát kỹ thuật và đối chiếu mức đáp ứng đề cương.
- Chuẩn bị tài liệu Word/slide, dàn ý và từng bổ sung bản nháp chương 6 cùng ảnh minh họa; bản Markdown chương 6 và bộ ảnh tương ứng đã được xóa ở trạng thái hiện tại.
- Sắp xếp tài liệu theo nhóm, cập nhật đường dẫn sau hợp nhất mã ML và loại bản sao trùng.
- Commit/push toàn bộ thay đổi sẵn có theo Conventional Commits lên nhánh `phantrongnguyen` ngày 02/11/2026:

| Commit | Công việc |
| --- | --- |
| `28f9c8d` | Hợp nhất pipeline huấn luyện và bằng chứng thực nghiệm ML |
| `def2b40` | Bổ sung rà soát kỹ thuật và kế hoạch hoàn thiện khóa luận |
| `4687c36` | Ghi nhận xóa bản nháp chương 6 và ảnh minh họa |

## 11. Mốc công việc và báo cáo chi tiết

| Thời gian | Công việc chính | Báo cáo/bằng chứng |
| --- | --- | --- |
| 12–27/08/2026 | Khởi tạo, nguồn dữ liệu, đặc trưng, tiền xử lý, thuật toán và notebook ban đầu | Lịch sử Git; một phần mã cũ đã được thay thế |
| 05–09/10/2026 | API suy luận, dashboard, React/Vite, kiến trúc và database | Lịch sử Git, tài liệu dự án |
| 10/10/2026 | Docker/database, cổng đăng nhập, sửa dashboard/radar | [10-10-2026.md](dailys/10-10-2026.md) |
| 11/10/2026 | Backend phân vai và tích hợp các phân hệ | [11-10-2026.md](dailys/11-10-2026.md) |
| 12/10/2026 | Giao diện HUIT, quản lý tài khoản, hồ sơ, đăng nhập MSSV | [12-10-2026.md](dailys/12-10-2026.md) |
| 13/10/2026 | Khảo sát backend, Postman, tài liệu và đánh giá kỹ thuật | [13-10-2026.md](dailys/13-10-2026.md) |
| 14/10/2026 | Dự báo từ database, snapshot CCC, radar, reset mật khẩu/theme | [14-10-2026.md](dailys/14-10-2026.md), lịch sử Git |
| 16/10/2026 | Phân tách nghiệp vụ theo học phần, avatar, nhắc nhở | [16-10-2026.md](dailys/16-10-2026.md) |
| 18/10/2026 | Phân quyền, bảo toàn dự báo, đồng bộ model, kiểm thử PostgreSQL | [18-10-2026.md](dailys/18-10-2026.md) |
| 19/10/2026 | Chuẩn hóa database/migration, đồng bộ nghiên cứu, gợi ý có căn cứ | [19-10-2026.md](dailys/19-10-2026.md), lịch sử Git |
| 20/10/2026 | Gộp giao diện giảng viên, đối chiếu khác biệt và kết quả model | [20-10-2026.md](dailys/20-10-2026.md) |
| 21/10/2026 | Radar, hợp đồng căn cứ, audit, giao thức đánh giá và E2E | [21-10-2026.md](dailys/21-10-2026.md) |
| 22–23/10/2026 | OULAD, giao diện giảng viên bốn tab, biểu đồ/lịch sử giao nhiệm vụ | [22-10-2026.md](dailys/22-10-2026.md), lịch sử Git |
| 25–27/10/2026 | Rà soát đề cương, tái thực nghiệm, hợp nhất ML, tổ chức tài liệu | [25-10-2026.md](dailys/25-10-2026.md), [run ML](../packages/ml/reports/rerun-20261025/README.md) |
| 02/11/2026 | Kiểm thử liên quan, commit/push thay đổi và tổng hợp công việc | Mục 9–10 của tài liệu này |

Ngày trong báo cáo phản ánh mốc công việc được ghi nhận; ngày commit có thể muộn hơn. Các mốc không có báo cáo riêng được đối chiếu bằng lịch sử Git.

## 12. Các phần còn mở sau những công việc trên

Các nội dung sau đã được xác định qua rà soát, chưa được coi là hoàn tất chỉ vì đã có kế hoạch hoặc công cụ hỗ trợ:

- Đối chiếu cơ sở thuật toán HCO/VNLS với tài liệu gốc; tăng ngân sách và khảo sát tham số/đối chứng phù hợp.
- Thu thập đánh giá chuyên gia thực tế về chất lượng gợi ý; công cụ và phiếu chấm hiện có chưa thay thế dữ liệu người tham gia.
- Đánh giá tác động can thiệp, nhóm so sánh, dữ liệu kỳ học mới và khả năng áp dụng tại HUIT.
- Xử lý/kiểm chứng các vấn đề được báo cáo ngày 22/10: hash snapshot bao phủ bài đánh giá, thời gian tương đối OULAD, phản hồi cũ khi đổi lớp và E2E sau gộp.
- Chốt cơ chế thu hồi token khi đổi/đặt lại mật khẩu, rà soát dependency và kiểm thử tải/nhiều worker.
- Hoàn thiện giao diện quản trị còn thiếu, tài liệu nộp cuối, slide và bằng chứng phân công/đóng góp nhóm.

Danh sách ưu tiên và điều kiện chốt được trình bày trong [báo cáo ngày 25/10](dailys/25-10-2026.md). Báo cáo hiện tại xác nhận phạm vi đã có bằng chứng trong repository; chưa khẳng định hệ thống sẵn sàng vận hành thực tế hoặc đã chứng minh hiệu quả học tập.
