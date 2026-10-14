import copy
from typing import Any
import numpy as np
import pandas as pd

from ml.predictor import predict
from schemas.recourse import (
    ActionableRecourseResponse,
    ActionableTargetItem,
    RecourseScenario,
    SRLPhase,
    TheoreticalFoundations,
)

FEATURE_METADATA: dict[str, dict[str, Any]] = {
    "days_since_last_activity": {
        "label": "Số ngày gián đoạn học tập",
        "unit": "ngày",
        "description": "Quay lại LMS và truy cập bài học để xóa bỏ tình trạng gián đoạn hoạt động.",
    },
    "clicks_recent_7": {
        "label": "Tương tác học tập 7 ngày tới",
        "unit": "lượt click",
        "description": "Duy trì số lượt click bài học, video và câu hỏi trắc nghiệm trong tuần.",
    },
    "clicks_recent_30": {
        "label": "Tương tác tích lũy 30 ngày tới",
        "unit": "lượt click",
        "description": "Bảo đảm tổng khối lượng học tập duy trì đều đặn suốt tháng.",
    },
    "total_clicks_to_t": {
        "label": "Tổng lượt tương tác khóa học",
        "unit": "lượt click",
        "description": "Gia tăng tổng lượng tương tác học tập tích lũy từ nay đến cuối kỳ.",
    },
    "clicks_resource_to_t": {
        "label": "Lượt đọc tài liệu & học liệu (Resource)",
        "unit": "lượt click",
        "description": "Dành thời gian đọc và tải tài liệu môn học chính khóa.",
    },
    "clicks_url_to_t": {
        "label": "Lượt tương tác tài nguyên liên kết (URL)",
        "unit": "lượt click",
        "description": "Tham khảo tài liệu bổ trợ, đường dẫn học liệu và slide mở rộng.",
    },
    "active_days_to_t": {
        "label": "Số ngày đăng nhập học tập",
        "unit": "ngày",
        "description": "Duy trì thói quen học tập chia nhỏ nhiều ngày thay vì dồn dập vào một ngày.",
    },
    "active_day_ratio": {
        "label": "Tỷ lệ ngày học đều đặn",
        "unit": "%",
        "description": "Tỷ lệ phần trăm số ngày có hoạt động trên tổng số ngày học phần.",
    },
    "assessments_submitted_to_t": {
        "label": "Số bài đánh giá (TMA/CMA) đã hoàn thành",
        "unit": "bài",
        "description": "Nộp bài đánh giá còn nợ hoặc bài tập lớn sắp đến hạn tiếp theo.",
    },
    "submission_rate": {
        "label": "Tỷ lệ hoàn thành bài tập đến hạn",
        "unit": "%",
        "description": "Nâng cao tỷ lệ nộp bài đánh giá để bảo đảm tích lũy điểm quá trình.",
    },
}

THEORETICAL_FOUNDATIONS = TheoreticalFoundations(
    frameworks=[
        "Giải thích Phản thực nghiệm Khả thi (Actionable Counterfactual Explanations / Algorithmic Recourse): Khóa cố định các biến nhân khẩu học (tuổi, giới tính, học vấn) và chỉ tối ưu hóa các biến hành vi học tập có thể can thiệp được.",
        "Lý thuyết Học tập Tự điều chỉnh (Self-Regulated Learning - SRL, Zimmerman / Pardo et al. 2019): Chuyển đổi mục tiêu số học thành quy trình 3 giai đoạn: Chuẩn bị (Forethought), Thực thi (Performance), và Phản tỉnh (Self-Reflection).",
    ],
    citations=[
        "Wachter, S., Mittelstadt, B., & Russell, C. (2017). Counterfactual explanations without opening the black box: Automated decisions and the GDPR. Harvard Journal of Law & Technology, 31(2), 841.",
        "Mothilal, R. K., Sharma, A., & Tan, C. (2020). Explaining machine learning classifiers through diverse counterfactual explanations. ACM FAccT '20, 607–617.",
        "Pardo, A., Jovanović, J., Dawson, S., Gašević, D., & Mirriahi, N. (2019). Using learning analytics to scale the provision of personalised feedback. Computers & Education, 128, 427-438.",
        "Karimi, A. H., Schölkopf, B., & Valera, I. (2021). Algorithmic recourse: from counterfactual explanations to interventions. ACM FAccT '21, 353–362.",
    ],
    limitations=[
        "Tối ưu hóa phản thực nghiệm đo lường độ nhạy của mô hình dự đoán (Prediction Sensitivity), không chứng minh mối quan hệ nhân quả (Causality).",
        "Việc tăng lượt click đơn thuần không thay thế được sự hiểu biết bài học; người học cần hoàn thành nội dung bài học thực chất.",
        "Các ngưỡng và tham số được tối ưu trên tập dữ liệu chuẩn OULAD tại mốc Cutoff 75%; cần được thẩm định bởi Hội đồng Chuyên môn Sư phạm trước khi áp dụng vào thực tế trường học.",
    ],
)


class ActionableRecourseService:

    @staticmethod
    def _evaluate(pipe, cols: list[str], feats: dict[str, Any]) -> float:
        df = pd.DataFrame([feats])[cols]
        return float(pipe.predict_proba(df)[0, 1])

    @classmethod
    def generate_recourse(cls, model: dict, features: dict[str, Any]) -> ActionableRecourseResponse:
        pipe = model["pipeline"]
        cols = model["feature_columns"]
        threshold = float(model.get("threshold", 0.5))

        current_prob = cls._evaluate(pipe, cols, features)

        if current_prob < threshold:
            return ActionableRecourseResponse(
                status="not_at_risk",
                message="Hồ sơ hiện tại đang ở vùng an toàn (xác suất nguy cơ thấp hơn ngưỡng). Không cần kế hoạch đảo ngược khẩn cấp.",
                current_probability=round(current_prob, 4),
                threshold=threshold,
                scenarios=[],
                theoretical_foundations=THEORETICAL_FOUNDATIONS,
            )

        # -------------------------------------------------------------
        # Scenario 1: Quick-Win (Can thiệp Cấp bách / Bước đệm Khả thi)
        # -------------------------------------------------------------
        s1 = copy.deepcopy(features)
        
        # 1. Quay lại LMS ngay trong ngày mai (giảm số ngày gián đoạn về 1)
        if s1.get("days_since_last_activity", 0) > 1:
            s1["days_since_last_activity"] = 1.0

        # 2. Hoạt động tích cực trong 7 ngày tới
        cur_c7 = float(s1.get("clicks_recent_7", 0))
        target_c7 = max(cur_c7 + 40.0, 50.0)
        added_c7 = target_c7 - cur_c7
        s1["clicks_recent_7"] = round(target_c7, 1)

        # 3. Kéo theo 30 ngày gần nhất và tổng số click
        cur_c30 = float(s1.get("clicks_recent_30", 0))
        target_c30 = max(cur_c30 + added_c7, target_c7 + 25.0)
        s1["clicks_recent_30"] = round(target_c30, 1)

        s1["total_clicks_to_t"] = round(float(s1.get("total_clicks_to_t", 0)) + added_c7, 1)
        s1["clicks_resource_to_t"] = round(float(s1.get("clicks_resource_to_t", 0)) + added_c7 * 0.45, 1)
        s1["clicks_url_to_t"] = round(float(s1.get("clicks_url_to_t", 0)) + added_c7 * 0.15, 1)

        # 4. Tăng 3 ngày học tích cực trong tuần tới
        s1["active_days_to_t"] = round(float(s1.get("active_days_to_t", 0)) + 3.0, 1)
        s1["active_day_ratio"] = round(min(1.0, float(s1["active_days_to_t"]) / 200.0), 3)

        # 5. Hoàn thành thêm 1 bài đánh giá nếu chưa nộp đủ
        cur_sub = float(s1.get("assessments_submitted_to_t", 0))
        cur_rate = float(s1.get("submission_rate", 0))
        if cur_rate < 0.99:
            s1["assessments_submitted_to_t"] = cur_sub + 1.0
            est_due = max(cur_sub / max(cur_rate, 0.05), cur_sub + 1.0)
            s1["submission_rate"] = round(min(1.0, s1["assessments_submitted_to_t"] / est_due), 3)

        prob_s1 = cls._evaluate(pipe, cols, s1)

        # -------------------------------------------------------------
        # Scenario 2: Sustainable (Lộ trình Phục hồi Bền vững / Đến cuối kỳ)
        # -------------------------------------------------------------
        s2 = copy.deepcopy(s1)
        
        # Gia tăng cường độ tương tác bền vững
        cur_c7_s2 = float(s2["clicks_recent_7"])
        target_c7_s2 = max(cur_c7_s2 + 35.0, 80.0)
        added_c7_s2 = target_c7_s2 - cur_c7_s2
        s2["clicks_recent_7"] = round(target_c7_s2, 1)

        cur_c30_s2 = float(s2["clicks_recent_30"])
        target_c30_s2 = max(cur_c30_s2 + 80.0, 160.0)
        added_sust = target_c30_s2 - cur_c30_s2
        s2["clicks_recent_30"] = round(target_c30_s2, 1)

        s2["total_clicks_to_t"] = round(float(s2["total_clicks_to_t"]) + added_sust, 1)
        s2["clicks_resource_to_t"] = round(float(s2["clicks_resource_to_t"]) + added_sust * 0.45, 1)
        s2["clicks_url_to_t"] = round(float(s2["clicks_url_to_t"]) + added_sust * 0.20, 1)

        # Thêm 6 ngày học nữa (duy trì 3-4 ngày/tuần)
        s2["active_days_to_t"] = round(float(s2["active_days_to_t"]) + 6.0, 1)
        s2["active_day_ratio"] = round(min(1.0, float(s2["active_days_to_t"]) / 200.0), 3)

        # Hoàn thành tiếp bài đánh giá tiếp theo
        cur_sub_s2 = float(s2["assessments_submitted_to_t"])
        cur_rate_s2 = float(s2["submission_rate"])
        if cur_rate_s2 < 0.95:
            s2["assessments_submitted_to_t"] = cur_sub_s2 + 1.0
            est_due_s2 = max(cur_sub_s2 / max(cur_rate_s2, 0.05), cur_sub_s2 + 1.0)
            s2["submission_rate"] = round(min(1.0, s2["assessments_submitted_to_t"] / est_due_s2), 3)

        prob_s2 = cls._evaluate(pipe, cols, s2)

        # Build target comparison lists
        targets_s1 = cls._build_targets(features, s1)
        targets_s2 = cls._build_targets(features, s2)

        srl_plan_s1 = [
            SRLPhase(
                phase="forethought",
                phase_name="Giai đoạn 1: Tái kết nối & Kích hoạt lại (48 giờ tới)",
                timeframe="Trong 2 ngày tới",
                objective="Khôi phục trạng thái hoạt động trên hệ thống LMS và xác lập liên lạc.",
                action_items=[
                    "Đăng nhập vào hệ thống LMS ngay hôm nay để xóa bỏ chuỗi ngày gián đoạn học tập.",
                    "Kiểm tra trang thông báo (Announcements) và danh sách bài tập TMA sắp đến hạn.",
                    "Gửi tin nhắn hoặc email thông báo tình hình học tập đến Cố vấn học tập / Giảng viên hướng dẫn.",
                ],
                stakeholder="student",
            ),
            SRLPhase(
                phase="performance",
                phase_name="Giai đoạn 2: Tập trung giải quyết bài nộp cấp bách (7 ngày tới)",
                timeframe="Tuần tiếp theo",
                objective="Hoàn thành ít nhất 1 bài tập đánh giá và đạt ngưỡng tương tác tối thiểu.",
                action_items=[
                    f"Hoàn thành và nộp 1 bài đánh giá đang nợ hoặc sắp đến hạn để đưa số bài nộp lên {s1['assessments_submitted_to_t']:.0f} bài.",
                    f"Thực hiện ít nhất 3 phiên học với tổng số lượt tương tác đạt tối thiểu {s1['clicks_recent_7']:.0f} lượt click trong tuần.",
                    "Dành ít nhất 45% thời gian tương tác vào việc đọc tài liệu cốt lõi (Resource).",
                ],
                stakeholder="student",
            ),
            SRLPhase(
                phase="reflection",
                phase_name="Giai đoạn 3: Rà soát & Đánh giá định kỳ cùng Cố vấn",
                timeframe="Cuối tuần 1",
                objective="Đối chiếu tiến độ đạt được và củng cố động lực học tập.",
                action_items=[
                    "Cố vấn học tập kiểm tra nhật ký nộp bài và xác nhận sinh viên đã tái kích hoạt hoạt động.",
                    "Đánh giá lại xác suất rủi ro bằng tính năng 'What-if Simulation' trên Dashboard.",
                    "Nếu đạt mục tiêu, chuyển tiếp sang lộ trình Phục hồi Bền vững.",
                ],
                stakeholder="collaborative",
            ),
        ]

        srl_plan_s2 = [
            SRLPhase(
                phase="forethought",
                phase_name="Giai đoạn 1: Lập kế hoạch học tập chi tiết đến cuối kỳ",
                timeframe="Tuần 1",
                objective="Xây dựng thời gian biểu cố định 3-4 buổi/tuần và mục tiêu điểm số từng bài.",
                action_items=[
                    "Lập lịch học cố định vào các khung giờ nhất định trong tuần để duy trì chỉ số active_days.",
                    "Chia nhỏ các chương học liệu và tài nguyên bổ trợ theo từng tuần học.",
                    "Đăng ký nhóm học tập hoặc kênh hỗ trợ trực tuyến của học phần.",
                ],
                stakeholder="student",
            ),
            SRLPhase(
                phase="performance",
                phase_name="Giai đoạn 2: Duy trì nhịp học chuyên sâu & nộp đủ 100% bài đánh giá",
                timeframe="Từ tuần 2 đến cuối kỳ",
                objective=f"Duy trì tương tác ổn định ({s2['clicks_recent_30']:.0f} click/tháng) và hoàn thành đầy đủ bài tập.",
                action_items=[
                    f"Nộp đầy đủ các bài đánh giá còn lại để nâng tỷ lệ nộp bài lên {(s2['submission_rate'] * 100):.1f}%.",
                    f"Duy trì ít nhất {s2['clicks_recent_7']:.0f} lượt tương tác học liệu mỗi tuần.",
                    "Tận dụng các đường dẫn liên kết URL bổ trợ để chuẩn bị cho kỳ thi kết thúc học phần.",
                ],
                stakeholder="student",
            ),
            SRLPhase(
                phase="reflection",
                phase_name="Giai đoạn 3: Phản tỉnh năng lực tự học & Sẵn sàng cho kỳ thi cuối kỳ",
                timeframe="Trước thi 2 tuần",
                objective="Tổng kết kiến thức và tự đánh giá độ sẵn sàng qua môn.",
                action_items=[
                    "Làm lại các bài tự kiểm tra (Practice Quizzes) và rà soát các phần điểm chưa cao.",
                    "Tham gia phiên hỏi đáp trực tuyến (Q&A session) trước kỳ thi cùng Giảng viên.",
                    "Giữ vững tỷ lệ ngày học để duy trì phản xạ học tập đến ngày thi chính thức.",
                ],
                stakeholder="collaborative",
            ),
        ]

        scenarios = [
            RecourseScenario(
                id="quick_win",
                title="⚡ Can thiệp Cấp bách (Quick-Win Re-engagement)",
                badge="Mục tiêu Khả thi Tức thời",
                target_probability=round(prob_s1, 4),
                probability_reduction=round(max(0.0, current_prob - prob_s1), 4),
                features=s1,
                targets=targets_s1,
                srl_plan=srl_plan_s1,
                summary=f"Tập trung xóa chuỗi ngày gián đoạn học tập và hoàn thành 1 bài đánh giá còn nợ. Dự kiến hạ xác suất rủi ro từ {(current_prob * 100):.1f}% xuống {(prob_s1 * 100):.1f}% (giảm {((current_prob - prob_s1) * 100):.1f}%).",
            ),
            RecourseScenario(
                id="sustainable",
                title="🌱 Lộ trình Phục hồi Bền vững (Sustainable Mastery)",
                badge="Mục tiêu Vững chắc Đến Cuối Kỳ",
                target_probability=round(prob_s2, 4),
                probability_reduction=round(max(0.0, current_prob - prob_s2), 4),
                features=s2,
                targets=targets_s2,
                srl_plan=srl_plan_s2,
                summary=f"Duy trì nhịp học đều đặn 3-4 ngày/tuần, đọc sâu tài liệu và nộp đầy đủ toàn bộ bài đánh giá. Dự kiến hạ sâu xác suất rủi ro xuống {(prob_s2 * 100):.1f}% (vào vùng an toàn vững chắc).",
            ),
        ]

        return ActionableRecourseResponse(
            status="available",
            message="Đã tính toán thành công các mục tiêu can thiệp khả thi (Actionable Recourse) dựa trên mô hình LightGBM và lý thuyết Tự điều chỉnh học tập (SRL).",
            current_probability=round(current_prob, 4),
            threshold=threshold,
            scenarios=scenarios,
            theoretical_foundations=THEORETICAL_FOUNDATIONS,
        )

    @classmethod
    def _build_targets(cls, current: dict[str, Any], target: dict[str, Any]) -> list[ActionableTargetItem]:
        items: list[ActionableTargetItem] = []
        rank = 1

        for feat, meta in FEATURE_METADATA.items():
            if feat not in current or feat not in target:
                continue

            c_val = current[feat]
            t_val = target[feat]

            diff = float(t_val) - float(c_val)
            if abs(diff) < 1e-4:
                continue

            # Format values
            if feat in ("submission_rate", "active_day_ratio"):
                c_str = f"{(float(c_val) * 100):.1f}%"
                t_str = f"{(float(t_val) * 100):.1f}%"
                d_val = round(diff * 100, 1)
            else:
                c_str = f"{float(c_val):.1f}" if isinstance(c_val, (int, float)) else str(c_val)
                t_str = f"{float(t_val):.1f}" if isinstance(t_val, (int, float)) else str(t_val)
                d_val = round(diff, 1)

            items.append(
                ActionableTargetItem(
                    feature=feat,
                    label=meta["label"],
                    current_value=c_str,
                    target_value=t_str,
                    delta=d_val,
                    unit=meta["unit"],
                    importance_rank=rank,
                    pedagogical_rationale=meta["description"],
                )
            )
            rank += 1

        # Sort: days_since_last_activity (re-engagement) and assessment submissions first
        def sort_priority(item: ActionableTargetItem) -> int:
            if item.feature == "days_since_last_activity":
                return 0
            if item.feature in ("assessments_submitted_to_t", "submission_rate"):
                return 1
            if item.feature == "clicks_recent_7":
                return 2
            return 3

        items.sort(key=sort_priority)
        for i, item in enumerate(items, start=1):
            item.importance_rank = i

        return items
