import { InterventionStrategy, StudentFeatures } from '@shared/types';

export function generateInterventions(
  features: StudentFeatures,
  atRisk: boolean,
  probability: number
): InterventionStrategy[] {
  const strategies: InterventionStrategy[] = [];
  // Exploratory rules for manually entered OULAD-style data, not validated interventions.
  const counts = [features.days_since_last_activity, features.assessments_submitted_to_t,
    features.late_submissions_to_t, features.clicks_recent_7, features.clicks_recent_30];
  if (!Number.isFinite(probability) || probability < 0 || probability > 1 ||
      counts.some(v => !Number.isInteger(v) || v < 0) ||
      [features.active_day_ratio, features.submission_rate].some(v => !Number.isFinite(v) || v < 0 || v > 1) ||
      features.late_submissions_to_t > features.assessments_submitted_to_t ||
      features.clicks_recent_7 > features.clicks_recent_30) return [];


  if (!atRisk) {
    if (probability >= 0.3) {
      strategies.push({
        id: 'watch-moderate',
        category: 'tien_do',
        priority: 'LOW',
        title: 'Trao đổi và theo dõi thêm',
        description:
          'Dự báo dưới ngưỡng model; quy tắc minh họa dùng xác suất từ 30% để đề xuất trao đổi. Đây không phải ngưỡng can thiệp đã kiểm chứng; cố vấn xác minh tiến độ và thống nhất lịch theo dõi.',
        targetMetric: 'Cố vấn thống nhất mục tiêu nộp bài theo lịch học phần',
      });
    } else {
      strategies.push({
        id: 'maintain-performance',
        category: 'hoc_thuat',
        priority: 'LOW',
        title: 'Duy trì theo dõi theo kế hoạch học phần',
        description:
          'Dự báo dưới ngưỡng model và xác suất dưới 30% không chứng minh chuyên cần tốt hay chắc chắn đạt môn. Trao đổi nhu cầu học tập trước khi đề xuất hoạt động bổ sung.',
        targetMetric: 'Thống nhất mục tiêu theo yêu cầu học phần; không quy đổi Distinction sang xếp loại HUIT',
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
      title: 'Xác minh gián đoạn tương tác tại cutoff',
      description: `Không ghi nhận click trong ${features.days_since_last_activity} ngày tính đến cutoff theo dữ liệu nhập. Cần xác minh nguồn và cách học ngoài LMS trước khi trao đổi; không suy ra bỏ học hoặc tình trạng hiện tại.`,
      targetMetric: 'Xác minh tình trạng hiện tại và thống nhất bước hỗ trợ',
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
        'Tỷ lệ ngày có hoạt động tại cutoff dưới mốc minh họa 35%. Chỉ số này không xác định lịch học dồn; cần trao đổi lịch học và hoạt động ngoài LMS trước khi đề xuất lịch phù hợp.',
      targetMetric: 'Thống nhất lịch học phù hợp với sinh viên và học phần',
    });
  }

  // Tình trạng nộp bài kiểm tra
  if (features.assessments_submitted_to_t === 0) {
    strategies.push({
      id: 'no-submission',
      category: 'tien_do',
      priority: 'HIGH',
      title: 'Xác minh dữ liệu nộp bài tại cutoff',
      description:
        'Số bài đã nộp bằng 0 tại cutoff theo dữ liệu nhập; chưa biết có bài đến hạn, được miễn hoặc log thiếu hay không. Đối chiếu lịch bài và nguồn dữ liệu trước khi đề xuất hỗ trợ.',
      targetMetric: 'Xác minh bài đến hạn và quyền nộp trước khi đặt mục tiêu',
    });
  } else if (features.submission_rate < 0.6 || features.late_submissions_to_t >= 2) {
    strategies.push({
      id: 'late-submission',
      category: 'tien_do',
      priority: 'MEDIUM',
      title: 'Kèm cặp kỹ năng quản lý thời gian & deadline',
      description: `Dữ liệu tại cutoff ghi nhận ${features.late_submissions_to_t} bài nộp trễ và tỷ lệ nộp ${(features.submission_rate * 100).toFixed(0)}%. Kiểm tra tính đầy đủ, hạn cá nhân và lịch bài; ngưỡng 60% hoặc 2 bài trễ là giả định minh họa.`,
      targetMetric: 'Cố vấn và sinh viên thống nhất mục tiêu theo hạn nộp đã xác minh',
    });
  }

  // Cửa sổ click chồng lấn tại cutoff, không suy luận tâm lý
  if (features.clicks_recent_30 > 0 && features.clicks_recent_7 < features.clicks_recent_30 / 10) {
    strategies.push({
      id: 'drop-recent',
      category: 'chuyen_can',
      priority: 'MEDIUM',
      title: 'Xác minh khác biệt tương tác 7/30 ngày tại cutoff',
      description:
        'Click trong cửa sổ 7 ngày nhỏ hơn 1/10 click của cửa sổ 30 ngày cùng kết thúc tại cutoff. Hai cửa sổ chồng lấn; đây là quy tắc minh họa, không chứng minh xu hướng theo tháng hay nguyên nhân sức khỏe/tâm lý.',
      targetMetric: 'Kiểm tra lịch học và nguồn log trước khi thống nhất mục tiêu',
    });
  }

  // No credit-overload rule: OULAD credits have no validated HUIT conversion.

  if (strategies.length === 0) {
    strategies.push({
      id: 'general-consult',
      category: 'hoc_thuat',
      priority: 'MEDIUM',
      title: 'Tổ chức buổi tư vấn 1-1 với giảng viên',
      description:
        'Model trả nhãn cần theo dõi nhưng không có quy tắc minh họa phù hợp. Cố vấn xác minh dữ liệu và nhu cầu; không suy đoán nguyên nhân hoặc điểm nghẽn kiến thức từ xác suất.',
      targetMetric: 'Hẹn lịch tư vấn trong tuần',
    });
  }

  return strategies;
}
