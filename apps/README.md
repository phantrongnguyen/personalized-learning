# Góc học tập — dự báo và gợi ý có căn cứ

Bản demo ngày 30/09/2026. Chạy xuyên suốt từ hồ sơ → model HCO–VNLS + LightGBM tại cutoff 75% → quy tắc gợi ý → bằng chứng và phiếu kết quả. Giữ nguyên file model đã đóng gói, không huấn luyện lại trong đợt đóng gói này.

## Bắt đầu ở đâu?

- App: http://127.0.0.1:5187/#goi-y, hoặc chọn “Hồ sơ & gợi ý” trong menu.
- Kịch bản nói và bấm khi báo cáo: [Hướng dẫn demo](docs/HUONG_DAN_DEMO.md).
- Phần ứng dụng để ghép vào khóa luận: [Bản Word đã chia cấp đề mục](docs/Bao_5.docx). Gồm 8 mục lớn và 39 mục con, dùng Heading 1/Heading 2 và số mục 1, 1.1, 1.2; giữ nội dung đã duyệt, không có bìa hay tên đề tài riêng.
- Tình trạng kiểm thử và phần còn thiếu: [Nghiệm thu demo](docs/TRANG_THAI_NGHIEM_THU.md).
- Cách đọc ba notebook đã có output: [Hướng dẫn notebook](notebooks/README.md).
- Ý nghĩa kết quả, hình và phần chưa đánh giá: [Kết quả](research_outputs/README.md).

## Chạy trên máy này

Mở PowerShell ở thư mục gốc repository, nơi chứa thư mục apps:

~~~powershell
./apps/Start-Demo.ps1
~~~

Lệnh mở hai tiến trình nền ẩn, chỉ lắng nghe 127.0.0.1, không tự mở trình duyệt. Nếu port đã có dịch vụ, lệnh không dừng hoặc chiếm dịch vụ đó. Tab cũ cần tải lại. Log nằm trong apps/.runtime, không đưa lên GitHub.

Dừng chỉ các tiến trình do lệnh trên quản lý:

~~~powershell
./apps/Start-Demo.ps1 -Stop
~~~

Nếu muốn xem log trực tiếp, chạy hai terminal thay cho script:

~~~powershell
cd apps/backend
./.venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
~~~

~~~powershell
cd apps/frontend
npm run dev -- --host 127.0.0.1 --port 5187 --strictPort
~~~

## Cài trên máy khác

Cần Python 3.12 và Node tương thích Vite trong package-lock.json (Node 20.19+ hoặc 22.12+ theo cấu hình dự án hiện tại). Trong apps/backend, tạo .venv rồi cài requirements-dev.txt; trong apps/frontend, chạy npm ci. File model và metadata phải có trong backend/model_store. Chỉ nạp joblib từ nguồn tin cậy.

~~~powershell
py -3.12 -m venv apps/backend/.venv
./apps/backend/.venv/Scripts/python.exe -m pip install -r apps/backend/requirements-dev.txt
./apps/backend/.venv/Scripts/python.exe -m ipykernel install --sys-prefix --name clht-demo --display-name "CLHT demo"
cd apps/frontend
npm ci
~~~

Không cần CSV gốc để chạy demo với hồ sơ đã chuẩn bị. Để tái tạo hồ sơ, cần dữ liệu nghiên cứu như hướng dẫn notebook. Không đưa dữ liệu cấp sinh viên đầy đủ hoặc thư mục .venv lên GitHub.

## App làm gì?

1. **Hồ sơ & gợi ý:** sáu bản trích rút train OULAD và một tình huống kiểm thử thiếu xác nhận nguồn. Có nhãn nguồn rõ, bỏ mã sinh viên/nhãn cuối kỳ, đổi mã bài. Không coi việc này là bảo đảm ẩn danh tuyệt đối.
2. **Đánh giá:** nhập số tổng hợp và, nếu có, từng bài đánh giá; xác nhận dữ liệu đến cutoff trước khi chạy model hoặc sinh lời khuyên. Không lưu các dữ liệu nhập vào cơ sở dữ liệu.
3. **Phương pháp:** giải thích cutoff, vai trò HCO–VNLS và giới hạn của các kết quả nghiên cứu.
4. **Tải phiếu:** xuất Markdown chứa kết quả vừa tính, căn cứ và giới hạn; không phải chứng nhận học vụ.

Quy tắc G01: bài đến hạn chưa có bản ghi; G02: từng nộp trễ; G03: không có click 7 ngày nhưng có trong 30 ngày; G04: không có click 30 ngày dù có lịch sử. Thiếu dữ liệu hoặc không khớp thì không tự tạo gợi ý.

## Giữ đúng vai trò mô hình

HCO–VNLS chọn 17/38 đặc trưng cho LightGBM 80 cây. Model tại cutoff 75% fit train + validation sau khi khóa mask; không dùng model này cho cutoff 50%. Hàm số của các feature cũ được giữ nguyên để không làm lệch đầu vào artifact.

Lời khuyên dùng nhánh bằng chứng riêng. Ví dụ, đối chiếu từng mã bài đến hạn với bài đã nộp, không lấy bài nộp sớm bù cho bài thiếu. Các feature lịch sử submission_rate/active_day_ratio không bị ghi đè; API chấp nhận hoạt động trước ngày mở môn đúng với dữ liệu nghiên cứu và kiểm tra một số quan hệ thời gian. Hai trường hợp mâu thuẫn còn chưa chặn được ghi rõ trong báo cáo và tài liệu nghiệm thu; không coi các kiểm tra hiện tại là đầy đủ.

G01–G04 không phải chiến lược trực tiếp do HCO–VNLS tối ưu. Chưa có bằng chứng gợi ý làm tăng điểm; phiếu chấm độ phù hợp còn trống, cần GVHD/người học đánh giá. Xác suất model không phải nguyên nhân, chưa hiệu chỉnh cho can thiệp và không tự quyết định học vụ. Test lịch sử từng được xem; chưa có kỳ học mới độc lập.

## Kiểm tra và chạy lại notebook

~~~powershell
cd apps/backend
./.venv/Scripts/python.exe -m pytest tests -q
~~~

~~~powershell
cd apps/frontend
npm run test
npm run build
~~~

Từ gốc checkout:

~~~powershell
./apps/backend/.venv/Scripts/python.exe apps/scripts/run_notebooks.py
~~~

Ba notebook dùng code nghiệp vụ cùng API với app, không mock model cho các bảng kết quả. Một kiểm thử riêng mock xác suất 1% được ghi rõ chỉ nhằm chứng minh gợi ý không bị khóa theo ngưỡng. Kiểm thử frontend là render trong Node/SSR, không phải kiểm thử thao tác trong trình duyệt.

## Cấu trúc gọn

~~~text
apps/
  backend/             API, model nguyên bản, bằng chứng và quy tắc
  frontend/            giao diện React
  notebooks/           11 → 12 → 13, đã chạy và lưu output
  research/            hàm dùng chung chuẩn bị hồ sơ từ train
  research_outputs/    bảng kiểm tra, kết quả demo, hình, phiếu chấm trống
  docs/                bản Word mới nhất, hướng dẫn và tình trạng nghiệm thu
  scripts/             chạy notebook tuần tự
  Start-Demo.ps1       bật/tắt demo tại máy
~~~

## Phạm vi gói đưa lên GitHub

- Nơi lưu: apps trên nhánh aBaoN9/clht-gb-github; không thay đổi các nhánh của thành viên khác.
- Bao gồm mã frontend/backend, model và metadata, kiểm thử, ba notebook đã có output, các kết quả minh họa và báo cáo Word mới nhất.
- Không bao gồm node_modules, .venv, log, cache, dữ liệu gốc cấp sinh viên hoặc các ảnh/PDF tạm dùng kiểm tra Word.
- Bản Word cũ được giữ tại máy, không đưa thêm vào gói app để tránh nhầm phiên bản.
- Chạy app không cần bộ dữ liệu gốc. Chạy lại bước chuẩn bị hồ sơ trong notebook cần nguồn nghiên cứu và biến CLHT_RESEARCH_DATA theo hướng dẫn notebook.
- Đây là gói demo cục bộ, không phải triển khai website công khai. Việc push mã nguồn không làm localhost trở thành đường dẫn truy cập từ máy khác.
