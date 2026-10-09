# Toàn bộ 80 cây LightGBM — cutoff 75%

Đây là bản train-only khớp sơ đồ validation, không phải model train + validation của ứng dụng.

## Bắt đầu

Mở muc_luc.html để xem liên kết dữ liệu từng cây. Đây là gói GitHub không kèm bộ ảnh lớn.

- Ảnh cây/histogram được giữ ở bản xuất cục bộ, không có trong gói này.
- du_lieu/cay_N_nut.csv: mọi nút/lá, n, thuộc tính, ngưỡng, G/H và xác suất trung bình.
- du_lieu/cay_N_la.csv: T, delta_F, thống kê và khoảng xác suất ở từng lá.
- du_lieu/cay_N_bin.csv: histogram của thuộc tính được chọn tại từng nút chia. Lọc node_index theo ảnh.
- du_lieu/cay_N_dong.csv.gz: từng dòng với p/F trước và sau cây, g/h, lá và đóng góp.
- du_lieu/cay_N_cau_truc.json: cấu trúc native của từng cây.
- du_lieu_chung: đặc trưng gốc/30 cột, bin ID từng dòng, ánh xạ tên cột và min/max bin.
- vi_du_10_dong_qua_80_cay.csv: 5 dòng đầu mỗi nhãn qua tất cả cây để dễ đối chiếu.
- chi_so_theo_so_cay.csv/.png: train/validation log-loss, Accuracy và AP theo số cây.

## Ý nghĩa số liệu

n là số dòng train đến nút/lá của cây đó. T là đầu ra trước learning rate; delta_F=0.055*T.
F_after=F_before+delta_F; p_after=sigmoid(F_after). Nhiều dòng cùng lá nhận cùng delta_F, nhưng p có thể khác.
Ảnh dùng p TB (trung bình của p từng dòng), không khẳng định một xác suất chung cho lá.
Ở cây đầu, native leaf_value gồm F0; ở cây sau, native leaf_value đã nhân learning rate. Không nhân hai lần.
Gradient/Hessian được tính TRƯỚC cây tương ứng. Bin ID dùng mapper native chung; G/H thay đổi theo vòng và tập dòng ở nút.
Min/max là giá trị quan sát trong bin. Histogram xuất cho thuộc tính được chọn ở mỗi nút, không xuất tất cả ứng viên chưa được chọn.
Ghép row_id trong cay_N_dong với dữ liệu chung. Cây 0 ở bảng chỉ số là mức nền, không phải cây thứ 81.

## CSV nén

Các tệp .csv.gz chứa đầy đủ dòng nhưng được nén để giảm dung lượng. Có thể giải nén thành CSV hoặc đọc trực tiếp bằng pandas.read_csv(path).

## Kiểm chứng

Các con số số lượng tệp/dung lượng bên dưới là của lần xuất đầy đủ gồm ảnh. Gói GitHub bỏ ảnh cây/histogram nhưng giữ đủ CSV/GZ/JSON; manifest_sha256.csv ở thư mục cha liệt kê tệp thực tế của gói.

720 tệp đối chiếu cây được kiểm tra tồn tại; n của 15 lá cộng thành 16.297 ở mọi cây. G/H được đối chiếu với toàn bộ 1.200 giá trị lá. Điểm cộng dồn khớp native ở cây 1, 2, 40, 80. Kết quả validation cuối khớp ma trận [[2180,68],[362,805]] và AP 0.8967566497124569. Artifact nguồn không bị thay đổi. Chi tiết tại kiem_chung.json.

## Chạy lại

Python: C:\Users\nguye\OneDrive - HUFI\Nam_4\KL_CN\CLHT_GB_APP_WORKTREE\apps\backend\.venv\Scripts\python.exe
Script: C:\Users\nguye\OneDrive - HUFI\Nam_4\KL_CN\ChienLuocHocTap\output\lightgbm_training_inspection\export_all_trees.py
Tham số: --source-root "C:\Users\nguye\OneDrive - HUFI\Nam_4\KL_CN\CLHT_GB_APP_WORKTREE" --output "C:\Users\nguye\OneDrive - HUFI\Nam_4\KL_CN\ChienLuocHocTap\output\lightgbm_training_inspection\toan_bo_80_cay"
