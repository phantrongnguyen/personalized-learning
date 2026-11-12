# Quy ước duy trì tài liệu

Áp dụng từ **04/11/2026**. [README gốc](../README.md#tài-liệu-chuẩn-theo-chủ-đề) là bảng phân công nguồn chuẩn: hướng dẫn local ở gốc; backend, frontend, Docker ở README thành phần; schema ở thiết kế database; migration/backup ở tài liệu migration; quy tắc ở business-rules; kết luận nghiên cứu ở THESIS_EXPERIMENTS; mã tái chạy ở packages/ml.

## Cập nhật hiện trạng và lưu lịch sử

- Sửa trực tiếp nội dung hiện hành khi mã thay đổi; không nối thêm một đoạn “cập nhật mới thay thế nội dung cũ” vào cùng hướng dẫn.
- Ghi diễn biến vào [CHANGELOG](../CHANGELOG.md), kèm liên kết bằng chứng ngày/run nếu có. Giữ nhật ký tiến độ có giá trị bằng chứng; tra cứu phiên bản mã/tài liệu cũ bằng Git thay vì nhân bản README.
- Trang tổng quan liên kết tới nguồn chuẩn thay vì sao chép endpoint, bảng metric và hướng dẫn dài. API method/schema thực lấy từ OpenAPI của phiên bản đang chạy.
- Giữ anchor cũ đang được dùng hoặc sửa nơi tham chiếu khi đổi heading; dùng liên kết tương đối trong repository.
- Phân biệt “mã đã có”, “kiểm tra tĩnh đã đạt”, “đã chạy thành công vào ngày…” và “chưa kiểm chứng”. Không dùng kết quả test cũ làm kết luận cho môi trường hiện tại.

## Quy tắc công bố metric

Mỗi bảng metric/hình nghiên cứu có ngữ cảnh ở ngay trước bảng hoặc ngay trong bảng: **SHA-256 artifact**, **dataset/split**, **cutoff**, **threshold**, **ngày đánh giá hoặc ngày run** và liên kết nguồn. Nếu nhiều hàng dùng estimator khác nhau, ghi riêng từng hàng hoặc nêu rõ SHA chưa được lưu/công bố; không gán SHA artifact refit cho model train-only/CV.

Phân biệt ngày đánh giá trong hồ sơ, ngày tạo báo cáo và ngày tái chạy. Không suy đoán ngày còn thiếu. AP không thay ROC-AUC; validation train-only không thay test refit. Test lịch sử đã dùng trong nghiên cứu không trở thành external holdout vì chạy lại. Không đổi metric/checksum bằng chứng để làm tài liệu khớp.

Bảng so sánh chính trong [THESIS_EXPERIMENTS](../reports/evaluation/THESIS_EXPERIMENTS.md) được sinh từ JSON bằng chứng. Chỉ sửa nguồn khi có kết quả thực nghiệm mới được truy nguyên; sau đó chạy:

```powershell
python scripts/check_docs.py --write-metrics
python scripts/check_docs.py
python -m unittest discover -s tests -p test_check_docs.py
```

Review diff để xác nhận danh tính artifact và phạm vi kết luận. Rerun có artifact khác SHA không tự thay model đang active trong database. Metric validation và các bảng so sánh nhiều model vẫn do người duy trì đối chiếu CSV; checker không tự chứng nhận tính đúng đắn của toàn bộ nghiên cứu.

## Kiểm tra tự động

`scripts/check_docs.py` dùng Python standard library, chạy được từ bất kỳ cwd. Mặc định chỉ đọc file, không kết nối mạng/database hoặc nạp joblib. Tùy chọn `--write-metrics` chỉ cập nhật block metric được đánh dấu trong THESIS_EXPERIMENTS.

- `DOCUMENTS`: bộ tài liệu hiện hành cần kiểm tra liên kết nội bộ và heading anchor; đường dẫn thư mục cũng được kiểm tra tồn tại. Không quét PDF hay bản khảo sát/nhật ký lưu trữ.
- `COMMANDS`: các lệnh quan trọng phải có trong code fence hướng dẫn; kiểm tra script tồn tại/cú pháp AST, flag script, manifest requirements, npm script, uvicorn target, Compose service/Dockerfile và nguồn COPY.
- Đối chiếu SHA byte artifact app với metadata/bằng chứng lịch sử; kiểm tra run completed, threshold, checksum JSON rerun và block metric khớp nguồn. Không yêu cầu artifact/data riêng tư trong thư mục runs để clone mới kiểm tra được.
- Kiểm tra ví dụ VITE API base không có hậu tố `/api/v1`.

Khi thêm tài liệu hoặc lệnh chuẩn, cập nhật danh sách tương ứng và chạy checker. Đây là kiểm tra tĩnh về liên kết/hợp đồng lệnh, **không thực thi các lệnh hướng dẫn**, không xác nhận dependency thực tế, CLI bên thứ ba, URL mạng, Docker image hoặc PostgreSQL đang hoạt động. Kiểm chứng runtime dùng các runner backend, browser và stack riêng theo hướng dẫn tương ứng.

[Workflow docs](../.github/workflows/docs.yml) chạy checker trên push/pull request. Không in `.env`, URL chứa mật khẩu hoặc dữ liệu cấp sinh viên vào log.
