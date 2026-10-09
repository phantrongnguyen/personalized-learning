# Model nghiên cứu và model chính

Nhánh `aBaoN9/clht-gb-github`, xuất ngày 09/10/2026. Có **25 artifact `.joblib`**:

- `baselines_50_75/`: 16 CatBoost/XGBoost × cutoff 50%/75% × Full features/HCO/VNLS/HCO-VNLS.
- `lightgbm_50_75/`: 8 LightGBM cùng các cutoff/phương pháp, gồm **`lightgbm_cutoff75_full_features.joblib`**, baseline 75% đủ 38 biến, chưa chọn biến HCO/VNLS.
- `model_hco_vnls_lightgbm_cutoff75.joblib`: model chính 80 cây, 17 biến gốc/30 cột mã hóa. Sao chép nguyên byte từ `apps/backend/model_store/`, SHA-256 `90c3f6e7bfdac2d9e62bcb836572f1a57c69fee3e4ef3dec22bd60b9850792db`. Không thay model app.

**24 bản so sánh fit train-only**, chấm validation ở ngưỡng 0,5; không chấm test hoặc tìm lại mask. **Model chính fit train + validation** sau khi khóa mask, không dùng test để fit; không đánh giá lại trên validation đã dùng fit. Hai loại không hoán đổi trong bảng so sánh. Cutoff là thời điểm lấy dữ liệu, không phải ngưỡng xác suất cảnh báo.

[Bảng so sánh kèm đường dẫn và hash](../ket_qua/so_sanh_tat_ca_model_da_xuat.csv) giữ nguyên metric/thời gian lịch sử; `export_fit_seconds` tách riêng thời gian fit xuất file. [Báo cáo](../bao_cao/SO_SANH_3_MODEL_BASELINE_50_75.md) có đầy đủ 24 trường hợp và phân biệt model chính.

## Nạp một model so sánh

Cài phiên bản ghim trong `CLHT_GB_GITHUB/requirements.txt`, dùng Python 3.12.6. Chạy từ gốc repository:

```python
from pathlib import Path
import sys
import pandas as pd

root = Path("CLHT_GB_GITHUB")
sys.path.insert(0, str(root.resolve()))
from NghienCuu_HCO_VNLS.code_dung_chung.baseline_artifacts import load_baseline, predict_risk

research = root / "NghienCuu_HCO_VNLS"
model = load_baseline(research / "mo_hinh/lightgbm_50_75/lightgbm_cutoff75_full_features.joblib")
inputs = pd.read_csv("du_lieu_dau_vao_cutoff75.csv")
probability = predict_risk(model, inputs)
alerts = (probability >= model["threshold"]).astype(int)
```

Đổi đường dẫn sang `baselines_50_75/catboost_cutoff50_hco.joblib` hoặc file trong danh sách. Input cần các biến gốc đúng cutoff; helper chọn đúng thứ tự từ artifact, không yêu cầu `risk`, `split`, `id_student`, và báo lỗi nếu thiếu biến. Tái tạo dữ liệu từ notebook 01/02 hoặc tự chuẩn bị đầu vào; không có dữ liệu cấp sinh viên trong gói này.

Chỉ nạp `.joblib` từ nguồn tin cậy vì pickle có thể thực thi mã. Helper kiểm tra SHA-256, phiên bản thư viện và schema. CatBoost lưu model cùng category gốc và chính sách thiếu category → `THIEU`; XGBoost/LightGBM lưu cả pipeline impute/One-Hot đã học trên train. Native `.cbm`/`.ubj`/`.txt` chỉ chứa bộ học; **không thay thế pipeline `.joblib`** cho XGBoost/LightGBM.

## Nạp model chính

Model chính dùng schema notebook 10, không phải schema helper `load_baseline`:

```python
import hashlib
import json
import joblib

model_path = research / "mo_hinh/model_hco_vnls_lightgbm_cutoff75.joblib"
metadata = json.loads((research / "mo_hinh/THONG_TIN_MODEL_HCO_VNLS_LIGHTGBM_75.json").read_text(encoding="utf-8"))
assert hashlib.sha256(model_path.read_bytes()).hexdigest() == metadata["model_sha256"]
production = joblib.load(model_path)
positive_index = list(production["pipeline"].classes_).index(1)
probability = production["pipeline"].predict_proba(inputs[production["feature_columns"]])[:, positive_index]
alerts = (probability >= production["threshold"]).astype(int)
```

`validation_reference_train_only` trong metadata chỉ là tham chiếu trước refit, không phải kết quả validation của artifact chính. Không fit lại hoặc đổi ngưỡng trên test.

## Tái kiểm chứng hoặc xuất lại

Chuẩn bị `ket_qua/du_lieu_cutoff_50.csv` và `du_lieu_cutoff_75.csv` đúng hash trong giao thức; CSV bị Git bỏ qua có chủ đích. Kiểm chứng file có sẵn, không fit lại:

```powershell
python CLHT_GB_GITHUB/NghienCuu_HCO_VNLS/code_dung_chung/export_baseline_models.py --verify-only
python CLHT_GB_GITHUB/NghienCuu_HCO_VNLS/code_dung_chung/export_lightgbm_models.py --verify-only
```

Script kiểm tra đủ 16/8 tổ hợp, toàn bộ metric validation so với CSV khóa, nạp lại joblib/native, nhóm sinh viên không giao nhau, checksum và model chính không đổi. Danh sách model và `manifest_sha256.csv` trong từng thư mục. `KIEM_CHUNG.json` của 16 baseline ghi hash nguồn tại thời điểm xuất. `.gitattributes` giữ nguyên byte các artifact/JSON/manifest/native qua checkout Windows để hash không đổi do LF/CRLF.

Để xuất mới, chạy hai lệnh **không có `--verify-only`**, theo thứ tự baseline rồi LightGBM. Script từ chối ghi đè nếu thư mục đã có `.joblib`; baseline hỗ trợ `--output` để chọn thư mục riêng. Không xóa artifact hiện có chỉ để chạy lại. Không chạy lại tối ưu HCO/VNLS trong quá trình xuất.
