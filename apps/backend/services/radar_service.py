from typing import Dict, Any, List


# Benchmark OULAD Top 25% sinh viên Giỏi (mốc Cutoff 75%)
BENCHMARK_TOP_25: Dict[str, float] = {
    "total_clicks": 350.0,
    "active_days": 40.0,
    "active_day_ratio": 0.45,
    "clicks_recent_7": 30.0,
    "submission_rate": 0.95,
    "late_submissions": 0.0,
}


def calculate_radar_6d(snap_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Tính toán 6 chiều năng lực học tập đối sánh với chuẩn Benchmark Top 25% sinh viên:
    1. Độ chuyên cần (active_days)
    2. Tổng tương tác VLE (total_clicks)
    3. Tương tác 7 ngày gần nhất (clicks_recent_7)
    4. Tỷ lệ nộp bài tập (submission_rate)
    5. Kỷ luật đúng hạn (late_submissions nghịch đảo)
    6. Mật độ ngày học tích lũy (active_day_ratio)
    """
    total_clicks = float(snap_data.get("total_clicks_to_t", 0))
    active_days = float(snap_data.get("active_days_to_t", 0))
    active_day_ratio = float(snap_data.get("active_day_ratio", 0.0))
    clicks_recent_7 = float(snap_data.get("clicks_recent_7", 0))
    submission_rate = float(snap_data.get("submission_rate", 0.0))
    late_submissions = float(snap_data.get("late_submissions_to_t", 0))

    # Kỷ luật nộp bài: nếu 0 bài trễ -> 100%, mỗi bài trễ trừ 25% (tối thiểu 0%)
    discipline_score = max(0.0, 1.0 - (late_submissions * 0.25))

    dimensions = [
        {
            "metric": "Tổng tương tác VLE",
            "student_value": total_clicks,
            "benchmark_value": BENCHMARK_TOP_25["total_clicks"],
            "percentile": min(100.0, round((total_clicks / BENCHMARK_TOP_25["total_clicks"]) * 100, 1)),
        },
        {
            "metric": "Số ngày học tích lũy",
            "student_value": active_days,
            "benchmark_value": BENCHMARK_TOP_25["active_days"],
            "percentile": min(100.0, round((active_days / BENCHMARK_TOP_25["active_days"]) * 100, 1)),
        },
        {
            "metric": "Mật độ ngày học",
            "student_value": round(active_day_ratio, 2),
            "benchmark_value": BENCHMARK_TOP_25["active_day_ratio"],
            "percentile": min(100.0, round((active_day_ratio / BENCHMARK_TOP_25["active_day_ratio"]) * 100, 1)),
        },
        {
            "metric": "Tương tác 7 ngày gần đây",
            "student_value": clicks_recent_7,
            "benchmark_value": BENCHMARK_TOP_25["clicks_recent_7"],
            "percentile": min(100.0, round((clicks_recent_7 / BENCHMARK_TOP_25["clicks_recent_7"]) * 100, 1)),
        },
        {
            "metric": "Tỷ lệ nộp bài tập",
            "student_value": round(submission_rate * 100, 1),
            "benchmark_value": round(BENCHMARK_TOP_25["submission_rate"] * 100, 1),
            "percentile": min(100.0, round((submission_rate / BENCHMARK_TOP_25["submission_rate"]) * 100, 1)),
        },
        {
            "metric": "Kỷ luật đúng hạn",
            "student_value": round(discipline_score * 100, 1),
            "benchmark_value": 100.0,
            "percentile": round(discipline_score * 100, 1),
        },
    ]

    return dimensions
