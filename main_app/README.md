# main_app — EduRisk dashboard

Bản app lấy từ nhánh `phantrongnguyen`, commit nguồn `de1970b`.
Không chứa notebooks, tập dữ liệu nghiên cứu hay báo cáo luận văn.

Xem [CAI_TIEN.md](CAI_TIEN.md) để biết các cải tiến đã thực hiện,
kết quả kiểm tra và những phần còn cần hoàn thiện.

## Chạy app trên Windows

Tại thư mục `main_app`, cài thư viện backend vào môi trường riêng:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
cd apps/backend
..\..\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 --lifespan on --reload
```

Ở terminal thứ hai, tại `main_app/apps/frontend`:

```powershell
npm ci
npm run dev -- --host 127.0.0.1
```

Dashboard: `http://127.0.0.1:5173/#dashboard`.
Chạy `npm run build` để tạo frontend `dist`; backend phục vụ bản build tại `/app/`.
Backend gốc dùng `CORSMiddleware(allow_private_network=True)` nên cần Starlette
hỗ trợ tham số này; môi trường đã kiểm thử dùng Starlette 1.7.0.

## Giải thích dự đoán

- API dự đoán trả thêm `threshold` và `explanation`, giữ nguyên `prediction` và `confidence`.
- Dùng `pred_contrib=True` của LightGBM đang có, không huấn luyện lại hay đổi model.
- Đóng góp của các cột one-hot được cộng về 17 biến gốc, bao gồm biến có đóng góp bằng 0.
- Mức nền cộng tổng đóng góp trên thang log-odds phải tái dựng đúng xác suất;
  backend kiểm tra điều này trước khi trả kết quả.
- Dashboard hiển thị ba yếu tố tăng và ba yếu tố giảm nổi bật, cùng bảng đầy đủ.
  Chênh lệch điểm phần trăm chỉ là chênh lệch tổng của cả hồ sơ so với mức nền quy đổi.
  Không coi một giá trị SHAP là số điểm phần trăm của riêng biến đó.
- Gợi ý hỗ trợ được ưu tiên theo các yếu tố hành vi đóng góp tăng;
  mỗi gợi ý có dữ liệu và đóng góp làm căn cứ. Mẫu hành động vẫn là hướng dẫn
  hỗ trợ do con người thiết kế, không phải hiệu quả can thiệp do model học được.
- Tuổi, giới tính, học vấn, mã học phần và thông tin đăng ký chỉ được xem là bối cảnh,
  không được chọn làm mục tiêu thay đổi cá nhân để giảm dự đoán.
- Kết quả, giải thích và radar dùng cùng hồ sơ đã gửi đi. Sửa form không tự đổi
  kết quả cũ; dashboard báo cần phân tích lại. Form bị khóa khi đang gửi yêu cầu.
- Nếu dùng backend cũ không có `explanation`, dashboard thông báo thiếu giải thích,
  không tự dựng nguyên nhân từ xác suất tổng.

Đây là giải thích dự đoán nguy cơ trượt/bỏ học, không phải bằng chứng nhân quả,
đánh giá toàn diện năng lực hay cam kết rằng một hành động sẽ làm giảm xác suất.
