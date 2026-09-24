# Các hình trong thực nghiệm dự báo và chọn đặc trưng

| Hình | Tạo ở notebook | Vì sao có hình này? | Đọc được gì? |
|---|---|---|---|
| `hgb_theo_cutoff_validation.png` | `03_so_sanh_cac_moc_cutoff.ipynb` | Vẽ Accuracy, Recall và AP của cùng HGB ở năm mốc. | Quan sát đánh đổi giữa cảnh báo sớm và thêm thông tin khi dự báo muộn. Các mốc không có cùng tập enrollment hợp lệ. |
| `hco_vnls_hoi_tu.png` | `05_hco_vnls_tren_boosting.ipynb` | Vẽ fitness tốt nhất theo các bước tìm kiếm của ba phương pháp ở seed 41. | Fitness có thưởng ít feature; đường cao hơn không tự chứng minh AP validation cao hơn. |
| `hco_vnls_catboost_hoi_tu.png` | `05c_hco_vnls_catboost.ipynb` | Vẽ fitness tốt nhất khi tìm mask bằng CatBoost 80 cây, tách hai cutoff. | Chỉ số cao trên trục Y là fitness CV; cần đối chiếu AP validation và số cột ở bảng riêng. |
| `thu_them_mo_hinh_validation.png` | `04c_thu_them_mo_hinh.ipynb` | Mỗi hàng là một trong **năm mô hình giữ lại**, hai dấu trên trục X là Recall nguy cơ (tròn) và AP (thoi); tách cutoff 50%/75%. | Thấy đánh đổi giữa phát hiện người học nguy cơ và xếp hạng nguy cơ; validation đã được dùng để chọn ứng viên, chưa xác nhận độc lập. |

Tất cả hình ở đây là từ dữ liệu của lần chạy mở rộng, không sao chép hình của thí nghiệm cũ.
