# Chiến lược học tập dự đoán nguy cơ sinh viên

Đây là bản đóng gói gọn để đọc trên GitHub và xem lại quá trình nghiên cứu. Mục tiêu là dự đoán sớm sinh viên có nguy cơ `Fail` hoặc `Withdrawn`, sau đó dùng HCO, VNLS và HCO–VNLS để tìm bộ đặc trưng phù hợp hơn.

## Nếu bạn chưa xem dự án bao giờ

Hãy đọc theo thứ tự:

1. `docs/TOM_TAT_DE_TAI.md` - tóm tắt toàn bộ bài toán, quy trình, hành trình và kết quả hiện tại.
2. `notebooks/HUONG_DAN_DOC_CAC_NOTEBOOK.md` - giải thích vai trò, đầu vào, đầu ra và thứ tự đọc của từng notebook.
3. `notebooks/01_kham_pha_du_lieu.ipynb` - xem dữ liệu ban đầu.
4. `notebooks/02_gop_bang_tao_dac_trung.ipynb` - xem cách gộp 7 bảng.
5. `notebooks/03_chia_tap_va_baseline.ipynb` - xem các model học máy làm mốc.
6. `notebooks/04_hco_vnls_co_ban.ipynb` - xem HCO, VNLS và HCO–VNLS hoạt động ra sao.
7. `notebooks/06_hco_vnls_trong_tam.ipynb` - xem so sánh trọng tâm theo model và alpha.
8. `notebooks/07_tien_xu_ly_chia_tap_va_so_sanh.ipynb` - xem kiểm tra tiền xử lý và nhiều tỷ lệ chia.
9. `notebooks/08_toi_uu_hgb_va_hco_vnls.ipynb` - xem lần tối ưu mới nhất.
10. `notebooks/09_so_sanh_cac_moc_hoc_ky.ipynb` - xem thử nghiệm đầu kỳ, giữa kỳ và cuối kỳ.

Các notebook đã được chạy sẵn và giữ output để người đọc xem kết quả ngay. Những notebook cần dữ liệu gốc chỉ chạy lại được sau khi đặt đủ 7 file CSV vào `data/raw/` theo hướng dẫn.

## Luồng nghiên cứu

```text
7 bảng dữ liệu
    ↓
gộp theo một lượt học của sinh viên
    ↓
tiền xử lý tại cutoff 50% tiến trình
    ↓
chia train / validation / test theo id_student
    ↓
baseline học máy
    ↓
HCO, VNLS, HCO–VNLS chọn feature
    ↓
tinh chỉnh HGB và so sánh lại
    ↓
đánh giá Accuracy, Precision, Recall, F1, AP, Weighted F1, Brier, runtime
```

## Kết luận hiện tại

- HGB là baseline mạnh về AP và chất lượng tổng thể.
- Logistic Regression là đối chứng tốt khi ưu tiên Recall risk.
- Trong lần tối ưu mới nhất, HCO đạt AP validation `0.8460`.
- HCO–VNLS đạt fitness `0.7873` và giữ ít feature nhất, trung bình `11.33` feature.
- HCO–VNLS chưa thắng mọi metric phân loại; vì vậy chưa được thay thế bằng một kết luận quá mạnh.
- Test chưa được dùng để chọn cấu hình trong lần tối ưu mới nhất.

## Cấu trúc thư mục

- `notebooks/`: chuỗi notebook nghiên cứu đã chạy.
- `clht_code/`: các hàm tái sử dụng cho gộp dữ liệu, model, đánh giá và optimizer.
- `ket_qua/`: bảng CSV kết quả tiêu biểu.
- `hinh/`: các biểu đồ dùng trong báo cáo.
- `docs/`: một tài liệu Markdown tổng hợp và một bản Word cùng nội dung.
- `mo_hinh/`: file model demo HCO–VNLS + HGB và thông tin schema.
- `app_demo.py`: giao diện Streamlit tối giản để thử model.
- `hinh/GIAI_THICH_CAC_HINH.md`: giải thích nguồn và ý nghĩa từng hình.
- `ket_qua/GIAI_THICH_CAC_BANG_KET_QUA.md`: giải thích nguồn và ý nghĩa từng bảng.
- `data/README.md`: hướng dẫn dữ liệu; không kèm dữ liệu gốc dung lượng lớn.

## Chạy lại

Cài thư viện trong `requirements.txt`, đặt 7 file dữ liệu vào `data/`, rồi mở Jupyter từ thư mục dự án. Nên chạy notebook theo thứ tự, vì một số notebook sau dùng bảng đã sinh từ notebook trước. Bản GitHub không kèm dữ liệu sinh viên đã xử lý; các output CSV trong `ket_qua/` chỉ là kết quả tổng hợp.

```powershell
jupyter lab
```

Không commit dữ liệu cá nhân, token, đường dẫn máy cá nhân hoặc các thư mục cache. `.gitignore` đã được thêm để tránh các file tạm phổ biến.

## Phạm vi của kết quả

Các con số trong bảng là kết quả thực nghiệm trên bộ dữ liệu và giao thức hiện tại. Runtime phụ thuộc máy chạy. HCO/VNLS trong code hiện là triển khai theo phong cách thuật toán đã thiết kế; nếu cần khẳng định tái hiện đúng một bài báo cụ thể thì phải đối chiếu thêm công thức gốc.
