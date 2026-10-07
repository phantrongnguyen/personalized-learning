# Bảng 30 cột số đưa vào LightGBM

**Cập nhật ngày 07/10/2026:** CSV cấp từng lượt học đã được bỏ khỏi bản chia sẻ và thêm vào `.gitignore`. Thư mục chỉ giữ giải thích tên cột và metadata xuất; khi cần xem toàn bộ ma trận, tái tạo cục bộ từ dữ liệu được phép sử dụng và model đã lưu. App không cần CSV này để hoạt động.

## Đây là bảng gì?

Bảng được xuất từ đúng bộ tiền xử lý nằm trong model **HCO–VNLS + LightGBM 80 cây, cutoff 75%** đang dùng cho app. Không tạo dữ liệu giả, không chọn lại đặc trưng và không huấn luyện lại model.

Nguồn có 23.159 dòng, mỗi dòng là một lần sinh viên đăng ký một học phần trong một kỳ học. Một sinh viên có thể xuất hiện nhiều lần, nên số dòng không phải số sinh viên duy nhất.

Quy trình: **38 đặc trưng ứng viên → HCO–VNLS chọn 17 đặc trưng gốc → điền dữ liệu thiếu và One-hot encoding → 30 cột số → LightGBM**. Bảng nguồn có 47 cột nếu tính cả nhãn, mã định danh và thông tin quản lý.

## Các file trong thư mục

| File | Nội dung |
|---|---|
| `du_lieu_30_dac_trung_cutoff_75.csv` | Chỉ lưu/tái tạo cục bộ: 23.159 dòng và 30 cột số; không đính kèm trên GitHub. |
| `giai_thich_30_cot.csv` | Giải thích lần lượt 30 cột, chỉ rõ đặc trưng gốc và giá trị được mã hóa. |
| `THONG_TIN_XUAT.json` | Số dòng, thứ tự cột, số dòng theo tập trong nguồn và SHA-256 để đối chiếu nguồn, model, CSV. |

CSV dùng UTF-8 có BOM để mở bằng Excel dễ đọc tiếng Việt. Nếu Excel không tách cột, dùng **Data → From Text/CSV**, chọn UTF-8 và dấu phân cách là dấu phẩy.

## Vì sao 17 đặc trưng thành 30 cột?

Có **13 đặc trưng số** được giữ thành 13 cột. Bốn đặc trưng phân loại được tách thành **17 cột chỉ báo 0/1**:

| Đặc trưng gốc | Số cột sau mã hóa | Cách hiểu |
|---|---:|---|
| `code_module` | 7 | Mỗi học phần AAA đến GGG có một cột. |
| `gender` | 2 | Hai cột cho F và M theo dữ liệu OULAD. |
| `highest_education` | 5 | Mỗi nhóm trình độ học vấn có một cột. |
| `age_band` | 3 | Ba nhóm tuổi theo cách phân nhóm của nguồn. |
| **Tổng cột phân loại** | **17** | **13 cột số + 17 cột chỉ báo = 30 cột đầu vào.** |

Ví dụ, `cat__code_module_AAA = 1` nghĩa là dòng đó thuộc học phần AAA. Nếu thuộc BBB thì cột AAA bằng 0 và cột BBB bằng 1. Các cột này không phải những đặc trưng mới do HCO–VNLS chọn thêm. Chúng là cách biểu diễn số của bốn đặc trưng phân loại đã chọn.

Tiền tố `num__` chỉ cột thuộc nhánh xử lý số, còn `cat__` chỉ cột thuộc nhánh xử lý phân loại. Tên cột và thứ tự cột giữ đúng kết quả `get_feature_names_out()` của model để đối chiếu, không dịch hoặc đổi tên tùy ý.

## Model đã xử lý dữ liệu như thế nào?

- Đặc trưng số thiếu được điền bằng trung vị đã học trong lúc fit model.
- Đặc trưng phân loại thiếu được điền bằng giá trị thường gặp nhất đã học trong lúc fit model.
- Các biến phân loại được One-hot encoding. Bộ mã hóa trong model cho phép bỏ qua nhóm chưa gặp, nhưng bảng nguồn đang xuất không có nhóm ngoài bộ mã hóa.
- Không chuẩn hóa các cột số trong pipeline này.
- Chỉ gọi `transform` của bộ tiền xử lý đã lưu. Không gọi `fit` hoặc `fit_transform` trên toàn bộ dữ liệu.

Model đóng gói đã được fit trên **train + validation: 19.712 dòng**, loại **3.447 dòng test** khỏi quá trình fit. Bản xuất này dùng chính bộ tiền xử lý đó để biến đổi toàn bộ bảng nguồn và phục vụ kiểm tra đầu vào của app. Nó **không** tái tạo ma trận của thí nghiệm cũ chỉ fit trên train, và không tạo ra kết quả đánh giá mới.

## Đọc và dùng bảng đúng cách

1. Mở bảng giải thích để biết ý nghĩa từng cột trước khi xem bảng dữ liệu.
2. Mỗi dòng trong CSV giữ nguyên thứ tự của bảng nguồn cutoff 75%. Khi đối chiếu bằng pandas, dùng vị trí dòng bắt đầu từ 0. Dòng dữ liệu đầu tiên nằm ở dòng 2 nếu tính cả tiêu đề CSV.
3. Bảng chỉ có 30 cột đặc trưng. Không chứa `id_student`, `risk`, `final_result`, `split` hoặc `code_presentation`. Vì không có nhãn và thông tin chia tập, đây chưa phải bộ dữ liệu độc lập để huấn luyện hoặc đánh giá lại.
4. Nguồn có 16.297 dòng train, 3.415 dòng validation và 3.447 dòng test. Các dòng được giữ theo thứ tự nguồn, không xếp thành ba khối theo tập. Muốn biết một dòng thuộc tập nào phải đối chiếu bảng nguồn cục bộ.
5. Không đưa CSV 30 cột vào `pipeline.predict_proba()` của app: pipeline đó nhận 17 đặc trưng gốc rồi tự biến đổi. Nếu kiểm tra trực tiếp đầu vào đã mã hóa, dùng bộ phân loại ở `pipeline.named_steps['model']` và giữ đúng thứ tự 30 cột.
6. Cutoff 75% là mốc 75% thời lượng học phần dùng giới hạn thông tin quan sát. Không có nghĩa lấy 75% số dòng.

## Tái tạo từ model đã lưu

Khi đã có bảng nguồn cục bộ và đúng model, phần biến đổi tương đương là:

```python
artifact = joblib.load(model_path)
source = pd.read_csv(source_path)
preprocess = artifact['pipeline'].named_steps['preprocess']
matrix = preprocess.transform(source[artifact['feature_columns']])
columns = preprocess.get_feature_names_out()
```

Không dùng bộ mã hóa mới hoặc tự sắp xếp lại các cột. Các thống kê điền thiếu và nhóm mã hóa phải là những giá trị model đã học. SHA-256 trong file thông tin giúp phát hiện dùng nhầm nguồn hoặc nhầm phiên bản model.

## Kiểm tra và giới hạn chia sẻ

Bản xuất được kiểm tra số dòng, 30 tên cột duy nhất, dữ liệu số hữu hạn, các cột One-hot chỉ có 0/1 và tổng chỉ báo bằng 1 trong từng nhóm phân loại của bảng nguồn. Ma trận đọc lại từ CSV được đối chiếu với kết quả biến đổi trực tiếp; xác suất dự đoán qua bộ phân loại được đối chiếu với pipeline gốc.

File này được đưa lên nhánh theo yêu cầu chia sẻ riêng bảng 30 cột. Các CSV nguồn bị loại khỏi Git vẫn giữ nguyên quy tắc loại trừ. Không có mã sinh viên trực tiếp trong bản xuất, nhưng dữ liệu cấp lần đăng ký vẫn có thể chứa thông tin nhạy cảm hoặc khả năng liên kết. Việc bỏ mã định danh không bảo đảm ẩn danh tuyệt đối. Khi phân phối ngoài nhóm, cần tuân thủ điều kiện sử dụng OULAD và chính sách dữ liệu của dự án.
