# Quy trình tái thực nghiệm HCO–VNLS

Đây là nguồn mã ML chuẩn duy nhất sau khi hợp nhất từ thư mục thí nghiệm cũ; giữ nguyên giao thức lịch sử để tái kiểm chứng. Đây chưa phải phiên bản thuật toán cải tiến theo các đề xuất rà soát ngày 25/10.

## Cấu trúc

- `history/`: một bộ bảng lịch sử và provenance nguồn gốc Git; không lưu bản sao mã.
- `research_code/`: tạo dữ liệu as-of, pipeline, metric, tối ưu mask.
- `shared_code/`: chia nhóm sinh viên và tạo đặc trưng thời gian.
- `notebooks/`: bản nguồn đã xóa output lịch sử.
- `run_pipeline.py`: thực thi toàn bộ notebook, ghi manifest và đánh giá test sau đóng gói.
- `runs/<run-id>/`: dữ liệu, notebook đã chạy, hình, model và kết quả riêng từng lần; được Git ignore vì có dữ liệu cấp sinh viên.

## Chạy từ gốc repository

```powershell
python -m venv packages/ml/.venv
packages/ml/.venv/Scripts/python.exe -m pip install -r packages/ml/requirements.txt
# Tại gốc repository:
packages/ml/.venv/Scripts/python.exe packages/ml/run_pipeline.py --run-id rerun-20261025
```

Đặt bảy bảng OULAD tại `data/raw/`. Mỗi lần chạy mới yêu cầu run-id chưa tồn tại. Tiếp tục một lần lỗi bằng cùng lệnh có `--resume`; chỉ cho phép khi checksum mã/dữ liệu và phiên bản môi trường không đổi. Nếu sửa mã để khắc phục lỗi, dùng run-id mới.

## Thứ tự và thay đổi so với nguồn

1. Notebook 02 tạo lại dữ liệu tại các cutoff 50/60/65/70/75%, chia sinh viên seed 41.
2. Notebook 01 kiểm kê nguồn và kiểm tra rò rỉ trên dữ liệu vừa tạo. Nguồn gốc notebook 01 phụ thuộc đầu ra 02 nên không thể chạy đầy đủ 01 trước 02 trong thư mục sạch.
3. Notebook 05b: LightGBM, full/HCO/VNLS/hybrid tại 50/75%.
4. Notebook 06/07: CatBoost, XGBoost và bảng tổng hợp ba bộ học.
5. Notebook 09: năm seed, đối chứng random cùng số đặc trưng, trace và ablation.
6. Notebook 10: khóa mask từ kết quả mới, fit train + validation và đóng gói riêng.
7. Runner tính metric test và lưu dự đoán cấp enrollment, không tối ưu threshold trên test.

`ML_RUN_DIR` chuyển toàn bộ đầu ra notebook vào lần chạy hiện hành. Assertion ép mask phải có đúng 17 biến đã được thay bằng kiểm tra mask không rỗng/không trùng; mask vẫn phải khớp giữa 05b và 09. Không ép kết quả mới phải trùng lịch sử. Không cập nhật artifact backend.

## Giao thức và giới hạn

Giữ seed chia tập 41, budget 8, population 3, alpha 0,85, threshold 0,5; seed ổn định 41/77/103/211/307. HCO–VNLS chọn đặc trưng, bộ học dự báo; không có thử nghiệm chất lượng gợi ý hay tác động can thiệp trong pipeline này.

Đây là tái chạy trên tập OULAD lịch sử; test không phải holdout mới. Các hạn chế về ngân sách, cơ sở HCO/VNLS, độ ổn định mask và chuyển miền vẫn còn. Tái chạy thành công không tự giải quyết các hạn chế phương pháp đó.

`manifest.json` lưu trạng thái từng notebook, thời gian, nguồn, checksum dữ liệu/mã/đầu ra và phiên bản môi trường. Chỉ trạng thái `completed` mới xác nhận pipeline hoàn thành. Notebook lỗi được lưu để chẩn đoán; không coi output một phần là kết quả đầy đủ.

## Kiểm tra và xuất báo cáo

```powershell
packages/ml/.venv/Scripts/python.exe packages/ml/test_pipeline.py
packages/ml/.venv/Scripts/python.exe -m pip check
packages/ml/.venv/Scripts/python.exe packages/ml/summarize_run.py rerun-20261025
```

`requirements.lock.txt` ghi chính xác toàn bộ môi trường được cài cho lần chạy này; có thể dùng `pip install -r packages/ml/requirements.lock.txt` để cài lại cả phụ thuộc gián tiếp. Báo cáo tổng hợp chỉ được xuất khi manifest ghi `completed` và nằm trong `reports/<run-id>/` của package.

## Lần chạy đã hoàn tất

Xem [kết quả rerun-20261025](reports/rerun-20261025/README.md). Cả bảy notebook đã hoàn tất; AP validation của ba bộ học khớp lịch sử. Metric test mới được tính từ artifact mới và dự đoán cấp dòng, không chỉ sao chép bảng kết quả cũ.

## Quy ước loại bản trùng

- Chỉ duy trì mã và notebook nguồn tại package này; notebook đã thực thi là bằng chứng từng run.
- Bảng lịch sử tại `history/results/`; bảng mới có thời gian fit/search riêng nên vẫn là bằng chứng của một lần chạy khác.
- Hình và metric test giống hệt giữa run và báo cáo chỉ giữ bản trong `reports/<run-id>/`. `runs/<run-id>/output-locations.json` ánh xạ vị trí mới kèm checksum; dùng `storage.resolve_run_file()` để kiểm tra manifest cũ.
- Manifest của lần chạy hoàn tất được giữ nguyên. Runner trước khi hợp nhất được lưu byte-identical tại `runs/rerun-20261025/source_snapshot/run_pipeline.py`; mã gốc trước di chuyển truy xuất bằng Git theo `history/source-provenance.json`.
- Sau thay đổi đường dẫn, chưa huấn luyện lại; kiểm tra bằng test, audit và xác minh toàn bộ output cũ.
