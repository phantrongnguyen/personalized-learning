"""
Module: Personalized Learning Strategy Recommendation Engine
Author: KLTN 13 - HUIT
"""

from typing import Dict, List, Any
import numpy as np
import pandas as pd


class LearningRecommendationEngine:
    """
    Engine that evaluates student behavioral patterns against optimal cohorts
    and produces personalized, actionable learning recommendations.
    """
    def __init__(self, feature_names: List[str], feature_mask: np.ndarray):
        self.feature_names = feature_names
        self.feature_mask = feature_mask
        self.selected_features = [f for f, m in zip(feature_names, feature_mask) if m == 1]
        self.benchmark_medians: Dict[str, float] = {}

    def fit_benchmarks(self, df_features: pd.DataFrame, y: pd.Series):
        """Calculates behavioral benchmarks from successful students (Pass / Distinction)."""
        successful_df = df_features[y == 1]
        for col in self.selected_features:
            if col in successful_df.columns and pd.api.types.is_numeric_dtype(successful_df[col]):
                self.benchmark_medians[col] = float(successful_df[col].median())

    def generate_student_recommendations(
        self,
        student_data: Dict[str, Any],
        predicted_risk_prob: float
    ) -> Dict[str, Any]:
        """
        Generates targeted, prioritized recommendations for an individual student.
        """
        strategies: List[Dict[str, Any]] = []
        strengths: List[str] = []
        weaknesses: List[str] = []

        # 1. Assessment Score Analysis
        avg_score = student_data.get("avg_score", 0)
        benchmark_score = self.benchmark_medians.get("avg_score", 70.0)
        if avg_score < 50:
            weaknesses.append("Điểm số bài tập quá thấp (< 50 điểm)")
            strategies.append({
                "category": "Củng cố kiến thức nền tảng",
                "priority": "HIGH",
                "action": "Xem lại tài nguyên giảng dạy cốt lõi (oucontent) các tuần trước và làm lại các bài tập trắc nghiệm ngắn tự luyện.",
                "target_metric": f"Nâng điểm trung bình từ {avg_score:.1f} lên trên {benchmark_score:.1f} điểm."
            })
        elif avg_score < benchmark_score:
            weaknesses.append("Điểm kiểm tra dưới mức trung vị nhóm khá giỏi")
            strategies.append({
                "category": "Tối ưu hóa điểm số",
                "priority": "MEDIUM",
                "action": "Tham khảo kỹ barem chấm điểm TMA và sửa lại các lỗi sai thường gặp trong bài kiểm tra định kỳ.",
                "target_metric": f"Nâng điểm trung bình đạt chuẩn kỳ vọng {benchmark_score:.1f}."
            })
        else:
            strengths.append(f"Điểm số bài tập tốt ({avg_score:.1f} điểm)")

        # 2. Submission Timeliness Analysis
        late_submissions = student_data.get("late_submissions", 0)
        if late_submissions > 0:
            weaknesses.append(f"Có {late_submissions} bài nộp trễ hạn")
            strategies.append({
                "category": "Quản lý thời gian & Hạn chót",
                "priority": "HIGH",
                "action": "Lập lịch biểu cá nhân hóa, đặt mốc hoàn thành trước hạn nộp chính thức 48 giờ để kịp rà soát bài nộp.",
                "target_metric": "Giảm số lần trễ hạn về 0 bài."
            })

        # 3. VLE Interaction & Active Days
        active_days = student_data.get("active_days", 0)
        benchmark_days = self.benchmark_medians.get("active_days", 45)
        if active_days < benchmark_days * 0.6:
            weaknesses.append(f"Mức độ chuyên cần trên hệ thống thấp ({active_days} ngày hoạt động)")
            strategies.append({
                "category": "Độ chuyên cần & Tính liên tục",
                "priority": "HIGH",
                "action": "Tạo thói quen đăng nhập LMS tối thiểu 4 ngày/tuần, mỗi phiên ít nhất 30-45 phút.",
                "target_metric": f"Tăng ngày hoạt động lên tối thiểu {int(benchmark_days * 0.8)} ngày."
            })
        else:
            strengths.append(f"Duy trì tính chuyên cần tốt ({active_days} ngày hoạt động)")

        # 4. Forum Discussion Activity
        forum_clicks = student_data.get("clicks_forumng", 0)
        benchmark_forum = self.benchmark_medians.get("clicks_forumng", 100)
        if forum_clicks < benchmark_forum * 0.4:
            strategies.append({
                "category": "Học tập cộng đồng & Diễn đàn",
                "priority": "MEDIUM",
                "action": "Chủ động tham gia thảo luận trên diễn đàn môn học (forumng), đặt câu hỏi khi gặp vướng mắc và theo dõi phản hồi của giảng viên.",
                "target_metric": f"Tăng tương tác diễn đàn từ {forum_clicks} lên {int(benchmark_forum)} lượt."
            })

        # 5. Early Semester Momentum
        clicks_early = student_data.get("clicks_early", 0)
        if clicks_early < 50:
            strategies.append({
                "category": "Động lực học giai đoạn đầu",
                "priority": "HIGH",
                "action": "Bắt nhịp sớm với giáo trình khóa học ngay trong 4 tuần đầu, tránh dồn ứ khối lượng kiến thức vào cuối kỳ.",
                "target_metric": "Hoàn thành toàn bộ tài nguyên dẫn nhập (week 1 - week 4)."
            })

        # Overall Status Assessment
        if predicted_risk_prob >= 0.6:
            status_text = "NGUY CƠ BỎ HỌC / RỚT MÔN CAO (HIGH RISK)"
            overall_color = "red"
        elif predicted_risk_prob >= 0.35:
            status_text = "CẦN CHÚ Ý & CAN THIỆP SỚM (MODERATE RISK)"
            overall_color = "orange"
        else:
            status_text = "LỘ TRÌNH HỌC TẬP TÍCH CỰC (GOOD STANDING)"
            overall_color = "green"

        return {
            "status_text": status_text,
            "risk_score": float(predicted_risk_prob),
            "strengths": strengths,
            "weaknesses": weaknesses,
            "strategies": strategies
        }
