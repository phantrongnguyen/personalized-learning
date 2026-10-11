import { FIELDS } from '@shared/constants';
import { InterventionStrategy, PredictionExplanation, StudentFeatures } from '@shared/types';

type ActionTemplate = Pick<InterventionStrategy, 'category' | 'title' | 'description' | 'targetMetric'>;

const actions: Partial<Record<keyof StudentFeatures, ActionTemplate>> = {
  submission_rate: { category: 'tien_do', title: 'Ưu tiên kiểm tra tiến độ nộp bài', description: 'Đối chiếu những bài đến hạn còn thiếu, xác nhận trở ngại với sinh viên và lập kế hoạch hoàn thành từng bài. Không suy diễn rằng sinh viên thiếu năng lực.', targetMetric: 'Có danh sách bài cần hoàn thành và hạn nộp cụ thể' },
  assessments_submitted_to_t: { category: 'tien_do', title: 'Rà soát bài đánh giá chưa hoàn thành', description: 'Kiểm tra số bài đã đến hạn tại mốc quan sát, quyền truy cập và khả năng nộp bài; ưu tiên bài có trọng số cao.', targetMetric: 'Xác nhận tiến độ bài đánh giá trong tuần' },
  late_submissions_to_t: { category: 'tien_do', title: 'Hỗ trợ quản lý hạn nộp', description: 'Cùng sinh viên chia nhỏ công việc và đặt nhắc hẹn trước hạn. Xác minh nguyên nhân nộp trễ trước khi lựa chọn hỗ trợ.', targetMetric: 'Theo dõi việc nộp đúng hạn của bài tiếp theo' },
  days_since_last_activity: { category: 'chuyen_can', title: 'Kiểm tra gián đoạn hoạt động học tập', description: 'Liên hệ để xác nhận tình trạng truy cập LMS, lịch học và trở ngại thực tế. Không kết luận có vấn đề tâm lý chỉ từ nhật ký truy cập.', targetMetric: 'Thống nhất một hoạt động học tiếp theo và ngày theo dõi' },
  active_day_ratio: { category: 'chuyen_can', title: 'Điều chỉnh nhịp học phù hợp', description: 'Xem lại lịch hoạt động và cách học ngoài LMS; thống nhất các phiên học đều đặn phù hợp với hoàn cảnh sinh viên.', targetMetric: 'Theo dõi nhịp hoạt động trong 7 ngày tiếp theo' },
  active_days_to_t: { category: 'chuyen_can', title: 'Rà soát mức duy trì học tập', description: 'Đối chiếu số ngày có hoạt động với độ dài học phần và lịch học thực tế; chọn lịch học khả thi thay vì áp một ngưỡng chung.', targetMetric: 'Có lịch học được sinh viên xác nhận' },
  clicks_recent_7: { category: 'chuyen_can', title: 'Kiểm tra hoạt động học gần đây', description: 'Xem các nội dung cần học trong tuần và hỏi về hình thức học ngoài LMS. Ưu tiên hoàn thành nhiệm vụ học, không tăng lượt click cho đủ số.', targetMetric: 'Hoàn thành một nhiệm vụ học cụ thể trong tuần' },
  clicks_recent_30: { category: 'chuyen_can', title: 'Rà soát tiến độ học trong tháng', description: 'Đối chiếu nhật ký tương tác với lịch bài học và kết quả thực tế; xác định nội dung cần hỗ trợ.', targetMetric: 'Có kế hoạch bù nội dung còn thiếu' },
  total_clicks_to_t: { category: 'hoc_thuat', title: 'Kiểm tra mức tiếp cận nội dung học', description: 'Đối chiếu mức tương tác với nội dung bắt buộc và việc học ngoài LMS. Tập trung vào hiểu bài thay vì số lượt truy cập.', targetMetric: 'Xác nhận các nội dung cốt lõi đã học' },
  clicks_resource_to_t: { category: 'hoc_thuat', title: 'Hỗ trợ sử dụng học liệu', description: 'Kiểm tra khả năng truy cập và mức hiểu học liệu; đề xuất tài liệu phù hợp với nội dung còn thiếu.', targetMetric: 'Hoàn thành một nội dung học liệu kèm tự kiểm tra' },
  clicks_url_to_t: { category: 'hoc_thuat', title: 'Kiểm tra khả năng tiếp cận tài nguyên', description: 'Xác nhận sinh viên truy cập được tài nguyên liên kết và tài nguyên đó có cần thiết với học phần hay không.', targetMetric: 'Giải quyết trở ngại truy cập hoặc cung cấp tài liệu thay thế' },
};

export function generateExplainedInterventions(explanation: PredictionExplanation | null | undefined, atRisk: boolean): InterventionStrategy[] {
  if (!explanation) return [];
  const drivers = explanation.contributions
    .filter(item => item.direction === 'increase' && actions[item.feature])
    .sort((left, right) => right.contribution - left.contribution)
    .slice(0, 3);

  if (!drivers.length) {
    return [{
      id: 'explanation-context', category: 'hoc_thuat', priority: atRisk ? 'MEDIUM' : 'LOW',
      title: atRisk ? 'Xác minh bối cảnh trước khi chọn can thiệp' : 'Duy trì các yếu tố đang bảo vệ sinh viên',
      description: atRisk ? 'Không có yếu tố hành vi đóng góp tăng rõ ràng để chọn hành động trực tiếp. Cần trao đổi với sinh viên, không đề xuất thay đổi tuổi, giới tính hay học vấn để giảm dự đoán.' : 'Hồ sơ không có yếu tố hành vi đóng góp tăng đáng kể. Tiếp tục theo dõi tiến độ và xác minh nhu cầu hỗ trợ thực tế.',
      targetMetric: 'Đánh giá lại sau khi có dữ liệu học tập mới',
    }];
  }

  return drivers.map((driver, index) => {
    const action = actions[driver.feature]!;
    const label = FIELDS.find(field => field.key === driver.feature)?.label ?? driver.feature;
    const value = typeof driver.value === 'number' && ['submission_rate', 'active_day_ratio'].includes(driver.feature)
      ? `${(driver.value * 100).toFixed(1)}%` : String(driver.value);
    return {
      ...action, id: `shap-${driver.feature}`, priority: atRisk ? index === 0 ? 'HIGH' : 'MEDIUM' : 'LOW',
      evidence: `${label} = ${value}; đóng góp +${driver.contribution.toFixed(3)} log-odds vào nguy cơ của hồ sơ này.`,
    };
  });
}
