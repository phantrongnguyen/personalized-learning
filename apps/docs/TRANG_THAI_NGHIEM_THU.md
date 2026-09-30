# Tình trạng bản demo — 30/09/2026

## Đã thực hiện

- Tích hợp model HCO–VNLS + LightGBM nguyên bản với nhánh gợi ý riêng, chỉ ở cutoff 75%.
- Đối chiếu bài đến hạn theo mã bài, không dùng bài nộp sớm để bù bài còn thiếu.
- Bốn quy tắc G01–G04, có căn cứ và giới hạn; không cần vượt ngưỡng nguy cơ mới được nhận lời khuyên.
- Từ chối dự báo/gợi ý tương ứng khi chưa xác nhận nguồn, không còn theo học hoặc thiếu bằng chứng.
- Trang Hồ sơ & gợi ý với sáu bản trích rút train và một tình huống kiểm thử tổng hợp; nhập liệu thủ công vẫn sử dụng được.
- Xuất phiếu Markdown từ kết quả vừa tính; không lưu đầu vào vào cơ sở dữ liệu.
- Ba notebook đã chạy, có bảng, hình và đoạn giải thích. Mọi thí nghiệm mới nằm dưới apps, không ghi đè các notebook nghiên cứu cũ.

## Kiểm tra đã chạy

| Hạng mục | Kết quả | Bằng chứng |
|---|---|---|
| Backend/API | 35 kiểm thử đạt | research_outputs/kiem_thu_api.txt; notebook 13 |
| Render thành phần frontend trong Node/SSR | 7 kiểm thử đạt | research_outputs/kiem_thu_giao_dien.txt |
| Build frontend | Thành công | research_outputs/build_frontend.txt |
| Notebook 11 | 5 cell code đã chạy, không có output lỗi | notebooks/11_kiem_tra_bang_chung_goi_y.ipynb |
| Notebook 12 | 4 cell code đã chạy, gọi model thật | notebooks/12_goi_y_chien_luoc_co_giai_thich.ipynb |
| Notebook 13 | 4 cell code đã chạy | notebooks/13_danh_gia_ky_thuat_va_phieu_gop_y.ipynb |
| Hình từ notebook | Đã mở kiểm tra; chữ tiếng Việt và trục hiển thị đầy đủ | research_outputs/hinh/du_bao_ho_so_minh_hoa.png |
| Model | SHA-256 khớp metadata, không đổi trọng số | backend/model_store/THONG_TIN_MODEL_HCO_VNLS_LIGHTGBM_75.json |
| Khởi động | Backend và frontend lắng nghe ở 8000 và 5187, chỉ localhost | Script Start-Demo.ps1 và log trong .runtime |

SHA-256 file model: 90c3f6e7bfdac2d9e62bcb836572f1a57c69fee3e4ef3dec22bd60b9850792db.

## Chưa xác nhận hoặc chưa làm

1. **Chưa kiểm thử thao tác trực tiếp bằng trình duyệt:** công cụ truy cập tab bị chính sách trình duyệt chặn. Không dùng công cụ khác để vòng qua hạn chế này. Kiểm thử render/SSR không thay thế thao tác, kiểm tra bố cục thực tế và tải file trong trình duyệt.
2. **Chưa chấm độ phù hợp bởi giảng viên/người học:** phiếu đánh giá cố ý để trống.
3. **Chưa chứng minh cải thiện điểm hoặc giảm bỏ học.** Gợi ý hiện là quy tắc có giải thích.
4. **Chưa tối ưu trực tiếp chiến lược bằng HCO–VNLS:** thuật toán đang chọn đặc trưng cho dự báo. Cần xác nhận phạm vi với GVHD.
5. **Chưa triển khai production, chưa kiểm tra công bằng hoặc kỳ học mới độc lập.** Demo localhost không thay thế phân quyền, bảo mật, đồng ý sử dụng dữ liệu và kiểm toán khi triển khai thực tế.
6. **Hai đầu vào mâu thuẫn vẫn được chấp nhận:** tổng 1 click nhưng 2 ngày hoạt động; ngày hoạt động cuối đúng cutoff nhưng click 7/30 ngày đều 0. Trường hợp thứ hai có thể sinh G04 không nhất quán. Đợt đóng gói không thay đổi logic này; chi tiết có trong bản Word.

Có một cảnh báo deprecation từ Starlette/AnyIO khi chạy TestClient, nhưng không làm thất bại kiểm thử. Jupyter trên Windows có cảnh báo về event loop và transport TCP cục bộ; các kernel đã kết thúc sau khi chạy notebook. Không coi những cảnh báo này là kết quả nghiên cứu.

## Kiểm tra nhanh bằng tay trước buổi báo cáo

- Tải lại tab app, chọn Hồ sơ & gợi ý, chạy trường hợp “Nộp sớm không bù được bài thiếu”. Kiểm tra 1 bài cần đối chiếu dù tổng nộp bằng tổng đến hạn.
- Chọn “Thiếu bằng chứng”, kiểm tra không có xác suất giả 0% và không có lời khuyên tự tạo.
- Mở căn cứ từng gợi ý và tải phiếu Markdown. Thử màn hình hẹp và thao tác bàn phím.
- Khi nhập tay, thử một ngày nộp sau cutoff hoặc mã bài trùng; hệ thống phải chặn trước khi báo kết quả.

Phạm vi nghiệm thu hiện tại là **bản demo tích hợp có kiểm thử kỹ thuật và bằng chứng tái lập**, không phải kết luận khoa học về hiệu quả can thiệp.

## Báo cáo trong gói app

- Bản Word hiện dùng: [Bao_5.docx](Bao_5.docx), giữ nguyên nội dung đã duyệt và thêm cấp mục 1, 1.1, 1.2 với Heading 1/Heading 2.
- Không kèm các bản Word trước trong gói app; các bản đó vẫn được giữ ở máy làm việc.
- Các kết quả 7 kiểm thử giao diện trong bảng trên là bằng chứng lưu từ notebook 13. Kiểm tra bổ sung sau đó gồm 10 kiểm thử giao diện; không diễn giải thành một lần chạy notebook mới.
