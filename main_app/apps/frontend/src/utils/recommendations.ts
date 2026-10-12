import { InterventionStrategy, StudentFeatures } from '@shared/types';

export function generateInterventions(
  features: StudentFeatures,
  atRisk: boolean,
  probability: number
): InterventionStrategy[] {
  const strategies: InterventionStrategy[] = [];

  if (!atRisk) {
    if (probability >= 0.3) {
      strategies.push({
        id: 'watch-moderate',
        category: 'tien_do',
        priority: 'LOW',
        title: 'Theo dõi định kỳ giai đoạn nước rút',
        description:
          'Xác suất rủi ro nằm ở vùng ranh giới (30% – 50%). Cố vấn học tập nên ghi nhận và kiểm tra tiến độ của sinh viên sau 1–2 tuần.',
        targetMetric: 'Duy trì tỷ lệ nộp bài ≥ 80%',
      });
    } else {
      strategies.push({
        id: 'maintain-performance',
        category: 'hoc_thuat',
        priority: 'LOW',
        title: 'Duy trì phong độ và mở rộng thử thách',
        description:
          'Sinh viên có chỉ số tương tác và chuyên cần rất tốt. Khuyến khích tham gia trợ giảng nhóm hoặc giải các bài tập nâng cao.',
        targetMetric: 'Mục tiêu đạt điểm Xuất sắc (Distinction)',
      });
    }
    return strategies;
  }

  // Cảnh báo chuyên cần & gián đoạn
  if (features.days_since_last_activity >= 14) {
    strategies.push({
      id: 'high-inactivity',
      category: 'chuyen_can',
      priority: 'HIGH',
      title: 'Can thiệp liên lạc khẩn cấp (Nguy cơ bỏ học)',
      description: `Sinh viên đã ${features.days_since_last_activity} ngày không đăng nhập hệ thống LMS. Cần liên hệ trực tiếp qua Email hoặc gọi điện thoại để nắm bắt lý do gián đoạn.`,
      targetMetric: 'Đăng nhập lại LMS trong 24 giờ tới',
    });
  }

  // Tỷ lệ ngày học
  if (features.active_day_ratio < 0.35) {
    strategies.push({
      id: 'low-active-ratio',
      category: 'chuyen_can',
      priority: 'HIGH',
      title: 'Thiết lập thời gian biểu học tập cố định',
      description:
        'Tỷ lệ ngày hoạt động thấp (< 35%), thể hiện thói quen học dồn vào cuối tuần hoặc sát hạn nộp. Cần hướng dẫn phương pháp học phân tán (Spaced Learning).',
      targetMetric: 'Duy trì ít nhất 3 - 4 ngày/tuần có hoạt động',
    });
  }

  // Tình trạng nộp bài kiểm tra
  if (features.assessments_submitted_to_t === 0) {
    strategies.push({
      id: 'no-submission',
      category: 'tien_do',
      priority: 'HIGH',
      title: 'Hỗ trợ kỹ thuật nộp bài kiểm tra',
      description:
        'Chưa nộp bất kỳ bài đánh giá nào tính đến mốc quan sát. Kiểm tra xem sinh viên có gặp trục trặc kỹ thuật hoặc chưa nắm rõ quy chế nộp bài hay không.',
      targetMetric: 'Hoàn thành bài kiểm tra bù hoặc bài gần nhất',
    });
  } else if (features.submission_rate < 0.6 || features.late_submissions_to_t >= 2) {
    strategies.push({
      id: 'late-submission',
      category: 'tien_do',
      priority: 'MEDIUM',
      title: 'Kèm cặp kỹ năng quản lý thời gian & deadline',
      description: `Sinh viên có ${features.late_submissions_to_t} bài nộp trễ và tỷ lệ hoàn thành chỉ đạt ${(features.submission_rate * 100).toFixed(0)}%. Cần lập kế hoạch nhắc hẹn trước hạn nộp 48 giờ.`,
      targetMetric: 'Không nộp trễ thêm bất kỳ bài nào',
    });
  }

  // Động lực và tương tác gần nhất
  if (features.clicks_recent_30 > 0 && features.clicks_recent_7 < features.clicks_recent_30 / 10) {
    strategies.push({
      id: 'drop-recent',
      category: 'tam_ly',
      priority: 'MEDIUM',
      title: 'Khảo sát dấu hiệu sa sút phong độ đột biến',
      description:
        'Tương tác trong 7 ngày gần nhất sụt giảm nghiêm trọng so với tháng trước. Có khả năng sinh viên gặp vấn đề sức khỏe, việc làm thêm hoặc mất động lực học.',
      targetMetric: 'Phục hồi tương tác đạt ≥ 50 clicks/tuần',
    });
  }

  // Tải học tập quá nặng
  if (features.studied_credits >= 90) {
    strategies.push({
      id: 'credit-overload',
      category: 'hoc_thuat',
      priority: 'LOW',
      title: 'Tư vấn phân bổ khối lượng tín chỉ',
      description: `Đăng ký ${features.studied_credits} tín chỉ trong kỳ là mức tải cao. Khuyên sinh viên tập trung ưu tiên các môn tiên quyết và môn cốt lõi để tránh trượt môn hàng loạt.`,
      targetMetric: 'Ưu tiên học phần cốt lõi của ngành',
    });
  }

  if (strategies.length === 0) {
    strategies.push({
      id: 'general-consult',
      category: 'hoc_thuat',
      priority: 'MEDIUM',
      title: 'Tổ chức buổi tư vấn 1-1 với giảng viên',
      description:
        'Các chỉ số tổng quát cho thấy nguy cơ tiềm ẩn. Cần có buổi phỏng vấn trực tiếp ngắn để làm rõ điểm nghẽn kiến thức của sinh viên.',
      targetMetric: 'Hẹn lịch tư vấn trong tuần',
    });
  }

  return strategies;
}
