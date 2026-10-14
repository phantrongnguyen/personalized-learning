import gzip
import hashlib
import json
import logging
import math
from pathlib import Path

import numpy as np

from ml.predictor import predict
from schemas.historical_cases import HistoricalSnapshot
from schemas.prediction import StudentFeatures

BEHAVIOR_FEATURES = (
    "total_clicks_to_t", "clicks_resource_to_t", "clicks_url_to_t",
    "active_days_to_t", "assessments_submitted_to_t", "late_submissions_to_t",
    "active_day_ratio", "submission_rate", "days_since_last_activity",
    "clicks_recent_7", "clicks_recent_30",
)
LIMITATIONS = [
    "Đối chiếu hồi cứu trên OULAD, không phải dữ liệu học sinh của trường và chưa phải đánh giá hiệu quả can thiệp.",
    "Model hiện tại chấm lại hồ sơ lịch sử tại mốc 75%; không có bằng chứng người học đã nhận cảnh báo hay được can thiệp lúc đó.",
    "Chỉ dùng hành vi tại mốc 75% để ghép hồ sơ. Kết quả cuối kỳ và dữ liệu sau mốc chỉ dùng để mô tả diễn biến.",
    "Tương tự không phải xác suất thành công. Thay đổi quan sát được không chứng minh nguyên nhân hay bảo đảm làm theo sẽ vượt qua.",
    "Các mốc dùng phần trăm thời lượng học phần, không nhất thiết cùng tuần lịch. Nhật ký LMS không phản ánh toàn bộ việc học ngoài hệ thống.",
]


class HistoricalCaseLibrary:
    def __init__(self, path: Path, model_path: Path, model: dict):
        self.model = model
        self.records = []
        self.scales = {}
        self.source = "OULAD · thư viện tham chiếu cục bộ"
        self.unavailable_message = "Chưa có thư viện lịch sử. Cần tạo từ dữ liệu OULAD thật; không hiển thị trường hợp giả lập."
        if not path.exists():
            return
        try:
            with gzip.open(path, "rt", encoding="utf-8") as source:
                payload = json.load(source)
            expected = hashlib.sha256(model_path.read_bytes()).hexdigest()
            if payload["schema_version"] != 1 or payload["model_sha256"] != expected:
                raise ValueError("Artifact lịch sử không khớp model hiện tại")
            if payload["cutoff_fraction"] != 0.75 or not math.isclose(payload["threshold"], model["threshold"]):
                raise ValueError("Artifact lịch sử khác mốc hoặc ngưỡng model")
            records = payload["records"]
            case_ids = set()
            for record in records:
                checked_features = StudentFeatures(**record["features"])
                if checked_features.code_module != record["module"] or not math.isfinite(checked_features.date_registration):
                    raise ValueError("Học phần hoặc ngày đăng ký không khớp hồ sơ")
                if record["case_id"] in case_ids or not record["learner_key"]:
                    raise ValueError("Trùng hồ sơ hoặc thiếu khóa người học")
                case_ids.add(record["case_id"])
                if record["final_result"] not in ("Pass", "Distinction", "Fail", "Withdrawn"):
                    raise ValueError("Kết quả cuối kỳ không hợp lệ")
                if not 0 <= record["risk_probability"] <= 1:
                    raise ValueError("Xác suất lịch sử không hợp lệ")
                for feature in BEHAVIOR_FEATURES:
                    if not math.isfinite(record["features"][feature]) or record["features"][feature] < 0:
                        raise ValueError("Thiếu đặc trưng hành vi")
                    if not math.isfinite(record["contributions"][feature]):
                        raise ValueError("Đóng góp lịch sử không hữu hạn")
                if [snapshot["fraction"] for snapshot in record["snapshots"]] != [0.75, 0.85, 1.0]:
                    raise ValueError("Thiếu mốc diễn biến")
                days = [snapshot["day"] for snapshot in record["snapshots"]]
                if days != sorted(days) or days[0] < 0:
                    raise ValueError("Mốc thời gian không hợp lệ")
                for snapshot in record["snapshots"]:
                    checked = HistoricalSnapshot(**snapshot)
                    if not 0 <= checked.recent_active_days <= 30 or checked.recent_clicks < 0:
                        raise ValueError("Cửa sổ hoạt động không hợp lệ")
                    if not 0 <= checked.due_assessments_submitted <= checked.due_assessments:
                        raise ValueError("Số bài đến hạn không hợp lệ")
                    expected_rate = checked.due_assessments_submitted / checked.due_assessments if checked.due_assessments else None
                    if checked.due_submission_rate != expected_rate:
                        raise ValueError("Tỷ lệ bài đến hạn không khớp")
            for feature in BEHAVIOR_FEATURES:
                if not math.isfinite(payload["numeric_scales"][feature]) or payload["numeric_scales"][feature] <= 0:
                    raise ValueError("Thang so sánh không hợp lệ")
            self.records = records
            self.scales = payload["numeric_scales"]
            self.source = payload["source"]
        except (OSError, ValueError, KeyError, TypeError, EOFError, IndexError):
            logging.getLogger(__name__).exception("Cannot load historical case library")
            self.unavailable_message = "Thư viện lịch sử không hợp lệ hoặc không khớp model. Cần dựng lại; dự đoán hiện tại vẫn dùng được."

    @staticmethod
    def _positive_profile(contributions):
        values = np.array([max(0.0, contributions[feature]) for feature in BEHAVIOR_FEATURES])
        return values / max(float(values.sum()), 1e-10)

    @staticmethod
    def _normalized_value(feature, value):
        return float(value) if feature in ("active_day_ratio", "submission_rate") else math.log1p(value)

    def compare(self, features):
        response = {"status": "unavailable", "message": self.unavailable_message, "source": self.source, "cutoff_fraction": 0.75, "threshold": float(self.model["threshold"]), "reference_count": len(self.records), "eligible_count": 0, "neighborhood_count": 0, "successful_count": 0, "unsuccessful_count": 0, "risk_drivers": [], "cases": [], "limitations": LIMITATIONS}
        if not self.records:
            return response
        prediction = predict(self.model, features)
        probability = prediction["confidence"]
        response["current_probability"] = probability
        if prediction["prediction"] != 1:
            response.update(status="not_at_risk", message="Hồ sơ hiện chưa vượt ngưỡng nguy cơ của model; không gán nhãn cần ‘lật kèo’.")
            return response
        contributions = {item["feature"]: item["contribution"] for item in prediction["explanation"]["contributions"]}
        drivers = sorted((feature for feature in BEHAVIOR_FEATURES if contributions[feature] > 1e-10), key=lambda feature: contributions[feature], reverse=True)[:3]
        response["risk_drivers"] = drivers
        if not drivers:
            response.update(status="no_matches", message="Không có yếu tố hành vi đóng góp tăng rõ ràng để ghép hồ sơ; không đối chiếu dựa trên tuổi hay giới tính.")
            return response
        current_profile = self._positive_profile(contributions)
        distances = []
        for record in self.records:
            if record["module"] != features["code_module"] or record["risk_probability"] < self.model["threshold"]:
                continue
            probability_gap = abs(record["risk_probability"] - probability)
            if probability_gap > 0.20:
                continue
            historical_drivers = sorted((feature for feature in BEHAVIOR_FEATURES if record["contributions"][feature] > 1e-10), key=lambda feature: record["contributions"][feature], reverse=True)[:3]
            if not set(drivers).intersection(historical_drivers):
                continue
            weighted_distance = 0.0
            total_weight = 0.0
            for feature in BEHAVIOR_FEATURES:
                weight = 2.0 if feature in drivers else 1.0
                difference = abs(self._normalized_value(feature, features[feature]) - self._normalized_value(feature, record["features"][feature]))
                weighted_distance += weight * min(difference / self.scales[feature], 1.0)
                total_weight += weight
            driver_distance = float(np.abs(current_profile - self._positive_profile(record["contributions"])).sum() / 2)
            distance = 0.70 * weighted_distance / total_weight + 0.20 * driver_distance + 0.10 * probability_gap / 0.20
            distances.append((distance, record))
        response["eligible_count"] = len({record["learner_key"] for _, record in distances})
        neighbors = []
        seen_learners = set()
        for distance, record in sorted(distances, key=lambda item: (item[0], item[1]["case_id"])):
            if distance > 0.25:
                break
            if record["learner_key"] not in seen_learners:
                neighbors.append((distance, record))
                seen_learners.add(record["learner_key"])
            if len(neighbors) == 20:
                break
        response["neighborhood_count"] = len(neighbors)
        successful = [(distance, record) for distance, record in neighbors if record["final_result"] in ("Pass", "Distinction")]
        response["successful_count"] = len(successful)
        response["unsuccessful_count"] = len(neighbors) - len(successful)
        if not neighbors:
            response.update(status="no_matches", message="Chưa tìm thấy hồ sơ đủ gần ở cùng học phần và mốc 75%. Không tự nới điều kiện để tạo ví dụ thành công.")
            return response
        if not successful:
            response.update(status="no_recoveries", message="Có hồ sơ tương tự, nhưng chưa có trường hợp vượt qua cuối kỳ trong nhóm gần nhất. Không lấy hồ sơ xa hơn chỉ để đưa ra câu chuyện thành công.")
            return response
        for distance, record in successful[:3]:
            response["cases"].append({"case_id": record["case_id"], "module": record["module"], "presentation": record["presentation"], "risk_probability": record["risk_probability"], "final_result": record["final_result"], "distance": distance, "matching_features": [{"feature": feature, "current_value": features[feature], "historical_value": record["features"][feature], "current_contribution": contributions[feature], "historical_contribution": record["contributions"][feature]} for feature in drivers], "snapshots": record["snapshots"]})
        response.update(status="available", message="Các hồ sơ gần nhất từng được model xếp nguy cơ tại mốc 75%, nhưng kết quả thật là Pass/Distinction. Diễn biến bên dưới là quan sát, không phải công thức bảo đảm thành công.")
        return response
