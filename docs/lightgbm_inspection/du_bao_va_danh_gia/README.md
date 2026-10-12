# Dự báo và đánh giá LightGBM tại cutoff 75%

## Phạm vi và kiểm chứng

Các bảng ở đây dùng dữ liệu OULAD của dự án và **model train-only đã xuất**, khớp sơ đồ: 17 biến gốc, 30 cột số, 80 cây, learning rate 0,055. Không dùng dữ liệu giả định. Không thay đổi model ứng dụng, dữ liệu nguồn hoặc model train-only đã lưu.

Script nạp `train_only_lightgbm.txt`, tái tạo tiền xử lý bằng một bản clone chỉ fit trên train, rồi đối chiếu xác suất với toàn bộ pipeline clone. Chênh lệch xác suất tối đa bằng 0. Kiểm chứng đường đi của bốn ví dụ với `pred_leaf` của LightGBM, cộng đủ 80 đóng góp khớp `raw_score`, sigmoid khớp xác suất native. SHA-256 các file nguồn giữ nguyên.

Chỉ số validation tái hiện: TN=2.180, FP=68, FN=362, TP=805; Accuracy=87,41%, Precision nguy cơ=92,21%, Recall nguy cơ=68,98%, F1 nguy cơ=78,92%, AP=0,8967566497124569.

## Dữ liệu đối chiếu

- `du_bao_validation.csv`: toàn bộ 3.415 lượt học; nhãn thật, điểm F, xác suất, quyết định và TN/TP/FP/FN.
- `dau_vao_17_bien_validation.csv`, `dau_vao_30_cot_validation.csv`: đầu vào trước/sau bộ tiền xử lý train-only.
- `bon_vi_du_TP_TN_FP_FN.csv`: bốn lượt học đã có trong validation, chọn để minh họa từng loại kết quả; không đại diện tỷ lệ các loại kết quả trong toàn bộ tập.
- `bon_vi_du_duong_di_80_cay.csv`: điều kiện, giá trị đặc trưng, nhánh và lá của mỗi ví dụ trong cả 80 cây.
- `bon_vi_du_dong_gop_80_cay.csv`: F/p trước và sau từng cây, đóng góp đã nhân learning rate và T trước learning rate.
- `doi_chieu_nguong_validation.csv`: áp các ngưỡng 0,3/0,4/0,5/0,6 vào cùng xác suất validation. Đây là đối chiếu giải thích, không chọn hoặc thay ngưỡng triển khai.
- `xep_hang_nguy_co_validation.csv`: xếp xác suất giảm dần.
- `cac_buoc_tinh_AP.csv`: gom các xác suất bằng nhau, tính Precision/Recall ở từng mức, rồi cộng `precision * delta_recall`. Tổng khớp AP của scikit-learn.
- `ket_qua_test_model_chinh.csv`: chỉ số test của đúng artifact HCO-VNLS + LightGBM 17 biến, fit train + validation.
- `du_doan_test_model_chinh.csv`: xác suất, nhãn dự đoán và TN/TP/FP/FN của 3.447 lượt test.
- `xep_hang_nguy_co_test.csv`, `xep_hang_top_k_test.csv`: test được xếp từ xác suất nguy cơ cao xuống thấp và chất lượng ở các mốc top-k.
- `cac_buoc_tinh_AP_test.csv`: các mức xác suất, Precision/Recall và phần đóng góp tạo thành AP test.
- `kiem_chung_test_model_chinh.json`: checksum, chính sách đánh giá và kết quả kiểm chứng test.
- `test_lich_su_cac_model_khac.csv`: bản sao kết quả test đã có trước đó của HGB/XGBoost/XGBoost+MLP, không phải model chính.
- `kiem_chung_du_bao.json`: nguồn, checksum, số dòng, chỉ số và kết quả kiểm chứng.

`source_row_index` là vị trí dòng 0-based trong bảng `du_lieu_cutoff_75.csv`, không phải số dòng vật lý trong CSV vì CSV có tiêu đề. Một lượt học được nhận diện thêm bởi `id_student`, `code_module`, `code_presentation`.

## Theo một lượt học cụ thể

Lượt học `source_row_index=20508`, sinh viên 682985, FFF/2014J:

1. Đặc trưng tại cutoff: `clicks_recent_30=0`, `submission_rate=0,8`, `days_since_last_activity=30`.
2. Cây 1: 0 ≤ 1,5 → trái; 0,8 ≤ 0,861111 → trái; 30 ≤ 38,5 → trái; đến lá 0.
3. Điểm nền F0=-0,692410939039; cây 1 cộng 0,118668705755. F sau cây 1=-0,573742233284; p=36,0374%.
4. Sau 80 cây: F=1,375528439125; p=79,8271887756%.
5. Vì p ≥ 0,5, dự đoán risk=1. Sau khi dự báo mới đối chiếu `final_result=Fail`, risk=1: đây là TP.

Trong dự báo, các cây đã cố định. Không tính gradient/Hessian để học lại; không đổi nút/lá; không sửa đặc trưng hoặc sử dụng nhãn thật. Các cây nhận cùng bộ đặc trưng; điểm cộng dồn không phải đầu vào quyết định rẽ nhánh.

F là điểm log-odds, không phải xác suất; p=1/(1+exp(-F)). Không lấy trung bình xác suất của 80 cây hoặc bỏ phiếu 80 nhãn. Mỗi cây đóng góp một điểm vào tổng.

**Chi tiết native:** cây 1 đã gộp F0 vào `leaf_value`; các cây sau đã nhân learning rate trong `leaf_value`. Vì vậy script tách F0 khỏi cây 1 để trình bày `delta_F`; không nhân learning rate hai lần.

## Hai nhánh đánh giá

Nhánh phân loại: xác suất → so ngưỡng → dự đoán 0/1 → đối chiếu nhãn → ma trận → Accuracy/Precision/Recall/F1.

Nhánh xếp hạng: giữ nguyên xác suất → xếp cao xuống thấp → đối chiếu nhãn ở từng mức → AP. AP không phụ thuộc ngưỡng cảnh báo 0,5 đã chọn và không thể suy ra chỉ từ một ma trận nhầm lẫn.

Cutoff 75% là thời điểm dừng thu thập đặc trưng so với độ dài học phần; ngưỡng 0,5 là quy tắc ra quyết định từ xác suất. Hai con số không cùng ý nghĩa.

## Kết quả test của model chính

Ba tập tại cutoff 75%: train 16.297; validation 3.415; test 3.447. Các nhóm sinh viên giữa ba tập không giao nhau.

Sơ đồ là **validation của bản chỉ fit train**. Model ứng dụng đã fit lại train + validation (19.712 dòng) sau khi khóa mask; 3.447 dòng test không dùng để fit. Ngày 09/10/2026, đúng artifact ứng dụng được nạp nguyên trạng và chấm trên test, không fit lại và không dò ngưỡng trên test.

Kết quả model chính ở ngưỡng 0,5: Accuracy 86,19%; Precision nguy cơ 91,23%; Recall nguy cơ 65,70%; F1 nguy cơ 76,39%; weighted F1 85,53%; AP 0,881575; ROC-AUC 0,904932; Brier score 0,101370. Ma trận: TN=2.201, FP=74, FN=402, TP=770. Có 844 cảnh báo trên 3.447 lượt test; test chứa 1.172 lượt nguy cơ thật.

Dự án cũng có test lịch sử ngày 23/09/2026 cho HGB_160, XGBoost và XGBoost+MLP. Không lấy chỉ số của các model đó thay cho kết quả LightGBM ở trên.

Test nguồn đã được xem trong lịch sử nghiên cứu nên lần chấm ngày 09/10/2026 là **xác nhận lịch sử**, không phải một holdout hoàn toàn nguyên sơ cho cả đề tài. Nếu cần bằng chứng tổng quát hóa mạnh hơn, cần thiết kế một tập dữ liệu hoặc kỳ học held-out chưa dùng trong lựa chọn cấu hình.

## Xếp hạng và AP trên test

`Giữ xác suất để xếp hạng` nghĩa là không biến mọi xác suất thành 0/1 ngay. Sắp xếp 3.447 lượt test từ `p_risk` cao nhất xuống thấp nhất, rồi kiểm tra các vị trí đầu có chứa nhiều lượt nguy cơ thật hay không.

- Top 100: 100 lượt nguy cơ thật, Precision@100=100%, Recall@100=8,53%.
- Top 500: 499 lượt nguy cơ thật, Precision@500=99,80%, Recall@500=42,58%.
- Top 844: 770 lượt nguy cơ thật, Precision=91,23%, Recall=65,70%. Mốc này trùng số cảnh báo tại ngưỡng 0,5.
- Top 1.000: 843 lượt nguy cơ thật, Precision@1000=84,30%, Recall@1000=71,93%.

Ở mỗi mức xác suất khác nhau, tính Precision và Recall của toàn bộ phần danh sách đã lấy. Khi thêm được các lượt nguy cơ thật mới, Recall tăng; đóng góp AP tại bước đó là `Precision × phần Recall vừa tăng`. Cộng tất cả đóng góp cho AP test `0,8815750676130706`, khớp `average_precision_score`.

Tỷ lệ nguy cơ thật trong test chỉ là 34,00%, nên AP 0,8816 cho thấy model xếp phần lớn lượt nguy cơ thật lên cao hơn đáng kể so với một thứ tự không mang thông tin. AP đánh giá thứ tự của toàn bộ xác suất; ma trận nhầm lẫn chỉ đánh giá một lát cắt tại ngưỡng 0,5.

## Chạy lại

Python: `CLHT_GB_APP_WORKTREE/apps/backend/.venv/Scripts/python.exe`.

Giải thích validation: `ChienLuocHocTap/output/lightgbm_training_inspection/export_prediction_evaluation.py`.

Đánh giá test artifact chính: `ChienLuocHocTap/output/lightgbm_training_inspection/evaluate_main_model_test.py`.

Hai script đều nhận `--source-root` là đường dẫn tuyệt đối đến `CLHT_GB_APP_WORKTREE`; không cập nhật artifact.
