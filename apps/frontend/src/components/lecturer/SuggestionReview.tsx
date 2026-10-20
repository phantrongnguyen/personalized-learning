import React from 'react';
import { CourseSuggestion, CourseSuggestionResponse } from '@shared/types';

const explainWarning = (warning: string): string => {
  if (warning.includes('bài và hạn nộp')) return 'Chưa có thông tin từng bài và hạn nộp; không thể biết bài nào thiếu hoặc trễ.';
  if (warning.includes('snapshot hợp lệ')) return 'Chưa có dữ liệu học tập được ghi nhận ở mốc 75% thời lượng học phần.';
  if (warning.includes('độ dài học phần')) return 'Chưa biết thời lượng học phần nên không thể xác định mốc đánh giá.';
  if (warning.includes('Thiếu ngày cutoff')) return 'Chưa xác nhận được ngày quan sát hoặc nguồn dữ liệu dùng cho gợi ý.';
  if (warning.includes('Thời điểm xác nhận không hợp lệ')) return 'Ngày xác nhận dữ liệu chưa hợp lệ.';
  if (warning.includes('Thời điểm xác nhận phải')) return 'Ngày xác nhận dữ liệu thiếu thông tin múi giờ hoặc nằm trong tương lai.';
  if (warning.includes('có trước ngày cutoff')) return 'Dữ liệu được ghi hoặc xác nhận trước mốc đánh giá nên chưa đủ căn cứ.';
  if (warning.includes('Ngày cutoff ở tương lai')) return 'Chưa đến mốc đánh giá của học phần.';
  if (warning.includes('Dữ liệu chỉ phản ánh')) return 'Thông tin chỉ phản ánh mốc đánh giá, không phải tình hình hiện tại.';
  if (warning.includes('nộp trễ/tổng bài')) return 'Số lượt nộp trễ và số bài đã nộp không khớp; cần kiểm tra lại.';
  if (warning.includes('dữ liệu bài đánh giá')) return 'Chưa xác nhận dữ liệu bài tập đầy đủ; không thể kết luận bài nào thiếu hoặc trễ.';
  if (warning.includes('click/mốc hoạt động')) return 'Số lượt hoạt động và thời gian không khớp; cần kiểm tra lại.';
  if (warning.includes('log hoạt động')) return 'Chưa xác nhận dữ liệu hoạt động trên hệ thống đầy đủ đến mốc đánh giá.';
  if (warning.includes('Chưa có tín hiệu')) return 'Không có gợi ý tự động không có nghĩa là sinh viên không cần hỗ trợ.';
  if (warning.includes('PredictionRun')) return 'Chưa có kết quả dự báo cho dữ liệu học tập mới nhất.';
  return 'Có dữ liệu cần người quản trị kiểm tra thêm trước khi dùng để gợi ý.';
};

const evidenceLabels: Record<string, string> = {
  source: 'Nguồn dữ liệu',
  confirmed_at: 'Được xác nhận lúc',
  cutoff_date: 'Dữ liệu tính đến',
  late_submissions_to_t: 'Số lượt nộp trễ đã ghi nhận',
  window_days: 'Khoảng thời gian kiểm tra (ngày)',
  total_clicks_to_t: 'Tổng lượt hoạt động được ghi nhận',
  clicks_recent_7: 'Lượt hoạt động trong 7 ngày cuối',
  clicks_recent_30: 'Lượt hoạt động trong 30 ngày cuối',
  days_since_last_activity: 'Số ngày từ lần hoạt động cuối',
};

export const explainObservation = (text: string): string =>
  text.replace(/cutoff/g, 'mốc đánh giá').replace(/click/g, 'lượt hoạt động trên hệ thống');

const displayDate = (value: string): string => {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value);
  return match ? [match[3], match[2], match[1]].join('/') : value;
};

const displayEvidence = (key: string, value: string | number): string => {
  if (key === 'cutoff_date' && typeof value === 'string') return displayDate(value);
  if (key === 'confirmed_at' && typeof value === 'string') {
    const time = new Date(value);
    return Number.isNaN(time.getTime()) ? value : time.toLocaleString('vi-VN');
  }
  return String(value);
};

interface SuggestionReviewProps {
  detail: CourseSuggestionResponse;
  onChoose: (suggestion: CourseSuggestion) => void;
}

export const SuggestionReview: React.FC<SuggestionReviewProps> = ({ detail, onChoose }) => (
  <section aria-label="Thông tin hỗ trợ quyết định" className="space-y-3 text-xs mb-4 max-h-72 overflow-y-auto border-y border-slate-700 py-3">
    <p className="font-semibold text-slate-200">
      {detail.status === 'available' ? 'Có gợi ý để giảng viên tham khảo.' :
        detail.status === 'insufficient_data' ? 'Chưa đủ dữ liệu đã xác nhận để gợi ý nhiệm vụ cụ thể.' :
          'Chưa có gợi ý phù hợp từ dữ liệu hiện có.'}
    </p>
    {detail.prediction ? (
      <p className="text-slate-300">
        {detail.prediction.model_version.toLowerCase().includes('demo') && <strong>Dữ liệu minh họa. </strong>}
        Dự báo riêng tại mốc 75% thời lượng học phần: điểm nguy cơ {(detail.prediction.risk_probability * 100).toFixed(1)}% theo mô hình.
        Đây là ước tính, không khẳng định sinh viên sẽ bỏ học hay cần nhận nhiệm vụ.
      </p>
    ) : <p className="text-amber-300">Chưa có kết quả dự báo cho dữ liệu học tập mới nhất.</p>}
    {detail.cutoff_date && <p className="text-slate-400">Dữ liệu gợi ý tính đến ngày {displayDate(detail.cutoff_date)}.</p>}
    {detail.suggestions.map((suggestion) => (
      <div key={suggestion.rule_id} className="rounded-xl border border-slate-700 p-3 space-y-1">
        <p className="font-semibold text-white">{suggestion.title}</p>
        <p className="text-slate-200">Quan sát: {explainObservation(suggestion.observation)}</p>
        <p className="text-slate-300">Hành động đề xuất: {suggestion.proposed_action}</p>
        <p className="text-amber-300">Giới hạn: {explainObservation(suggestion.limitation)}</p>
        <details className="text-slate-400">
          <summary className="cursor-pointer">Xem dữ liệu làm căn cứ</summary>
          <ul className="mt-1 pl-4 list-disc">
            {Object.entries(suggestion.evidence).filter(([key]) => evidenceLabels[key]).map(([key, value]) => (
              <li key={key}>{evidenceLabels[key]}: {displayEvidence(key, value)}</li>
            ))}
          </ul>
        </details>
        <button type="button" className="text-purple-300 underline" onClick={() => onChoose(suggestion)}>
          Chọn để điền nháp (có thể chỉnh sửa)
        </button>
      </div>
    ))}
    {detail.warnings.length > 0 && <details className="text-amber-300">
      <summary className="cursor-pointer">Những điều dữ liệu chưa cho biết</summary>
      <ul className="mt-1 pl-4 list-disc">
        {[...new Set(detail.warnings.map(explainWarning))].map((warning) => <li key={warning}>{warning}</li>)}
      </ul>
    </details>}
    <p className="text-slate-300">
      {detail.assignment.can_assign
        ? 'Giảng viên kiểm tra, chỉnh nháp rồi mới chủ động giao; hệ thống không tự tạo nhiệm vụ.'
        : 'Chưa thể giao nhiệm vụ: cần có kế hoạch hỗ trợ đang hoạt động cho sinh viên trong học phần này.'}
    </p>
  </section>
);
