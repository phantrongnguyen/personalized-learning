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
  if (warning.includes('OULAD là dữ liệu lịch sử')) return 'Đây là hồ sơ OULAD lịch sử, không phải sinh viên HUIT; ngày trong học phần không phải ngày trên lịch.';
  if (warning.includes('ánh xạ bài đánh giá')) return 'Chưa có thông tin bài nào kiểm tra chủ đề hoặc tiêu chí kiến thức nào; cần giảng viên đối chiếu.';
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
  snapshot_day: 'Ngày thứ mấy trong học phần',
  assessments_due: 'Số bài đến hạn',
  assessments_missing: 'Số bài chưa ghi nhận nộp',
  late_submissions_to_t: 'Số lượt nộp trễ đã ghi nhận',
  window_days: 'Khoảng thời gian kiểm tra (ngày)',
  total_clicks_to_t: 'Tổng click',
  clicks_recent_7: 'Lượt hoạt động trong 7 ngày cuối',
  clicks_recent_30: 'Lượt hoạt động trong 30 ngày cuối',
  days_since_last_activity: 'Số ngày từ lần hoạt động cuối',
};

const assessmentTypeLabel = (type: string): string => ({
  TMA: 'Bài giảng viên chấm', CMA: 'Bài hệ thống chấm', Exam: 'Bài thi',
}[type] || 'Bài đánh giá');

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
  <section aria-label="Thông tin hỗ trợ quyết định" className="mb-4 space-y-4 border-y border-slate-700 py-4 text-sm">

    <div className="space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h4 className="font-bold text-white">1. Điều đáng chú ý</h4>
        {detail.prediction && <span className="rounded-full bg-rose-500/10 px-3 py-1 text-xs font-semibold text-rose-300">
          {detail.prediction.model_version.toLowerCase().includes('demo') && <strong>Dữ liệu minh họa · </strong>}
          Điểm dự báo {(detail.prediction.risk_probability * 100).toFixed(1)}% · cần kiểm tra
        </span>}
      </div>
      <p className="text-slate-300">
        {detail.status === 'available' ? 'Các dấu hiệu dưới đây cần giảng viên đối chiếu với sinh viên.' :
          detail.status === 'insufficient_data' ? 'Chưa đủ dữ liệu đã xác nhận để chỉ ra vấn đề cụ thể.' :
            'Chưa có dấu hiệu phù hợp để đưa ra gợi ý từ dữ liệu hiện có.'}
      </p>
      {detail.suggestions.map((suggestion) => <div key={suggestion.rule_id} className="rounded-xl border border-purple-500/20 bg-purple-500/5 p-3">
        <p className="font-semibold text-white">{suggestion.title}</p>
        <p className="mt-1 text-slate-200">{explainObservation(suggestion.observation)}</p>
      </div>)}
      {detail.warnings.some((warning) => warning.includes('ánh xạ bài đánh giá')) && <p className="text-amber-300">
        Chưa xác định được sinh viên yếu chủ đề kiến thức nào; cần đối chiếu bài học và tiêu chí chấm.
      </p>}
    </div>

    <div className="space-y-3 border-t border-slate-700 pt-4">
      <h4 className="font-bold text-white">2. Việc giảng viên nên làm trước</h4>
      {detail.suggestions.length > 0 ? detail.suggestions.map((suggestion) => <div key={suggestion.rule_id} className="rounded-xl border border-slate-700 p-3">
        <p className="font-semibold text-slate-200">{suggestion.title}</p>
        <p className="mt-1 text-slate-300">{suggestion.proposed_action}</p>
        {detail.assignment.can_assign && <button type="button" className="mt-2 font-semibold text-purple-300 underline" onClick={() => onChoose(suggestion)}>
          Đưa gợi ý này vào nháp
        </button>}
      </div>) : <p className="text-slate-300">Trao đổi và xác minh nhu cầu hỗ trợ với sinh viên trước khi chọn bài tập.</p>}
    </div>

    <div className="space-y-2 border-t border-slate-700 pt-4">
      <h4 className="font-bold text-white">3. Giáo viên quyết định</h4>
      <p className="text-slate-300">{detail.assignment.can_assign
        ? detail.suggestions.length > 0
          ? 'Chọn gợi ý để tạo nháp, kiểm tra và chỉnh nội dung trước khi chủ động giao bài. Điểm dự báo không tự quyết định nhiệm vụ.'
          : 'Chưa có gợi ý đủ căn cứ. Hãy trao đổi với sinh viên, ghi điều đã xác minh và tự soạn nhiệm vụ phù hợp trước khi giao.'
        : 'Hiện chỉ xem được gợi ý; hãy trao đổi với cố vấn để lập và kích hoạt kế hoạch hỗ trợ cho đúng sinh viên, học phần trước khi giao bài.'}</p>
    </div>

    <details className="rounded-xl border border-slate-700 p-3 text-slate-300">
      <summary className="cursor-pointer font-semibold text-slate-200">Xem căn cứ và giới hạn dữ liệu</summary>
      <div className="mt-3 space-y-3 text-xs">
        {detail.source_kind === 'historical_oulad' && <p>
          Hồ sơ OULAD lịch sử tại ngày thứ {detail.cutoff_day} của học phần; không phản ánh sinh viên HUIT hiện tại.
        </p>}
        {detail.prediction ? <p>
          {detail.prediction.model_version.toLowerCase().includes('demo') && <strong>Dữ liệu minh họa. </strong>}
          Mô hình ước tính nguy cơ {(detail.prediction.risk_probability * 100).toFixed(1)}% tại mốc 75% thời lượng học phần.
          Con số này không khẳng định sinh viên sẽ bỏ học hoặc cần nhận một nhiệm vụ cụ thể.
        </p> : <p>Chưa có kết quả dự báo cho dữ liệu học tập mới nhất.</p>}
        {detail.cutoff_date && <p>Dữ liệu tính đến ngày {displayDate(detail.cutoff_date)}.</p>}
        {detail.assessment_details && detail.assessment_details.length > 0 && <details className="rounded-lg border border-slate-700 p-3">
          <summary className="cursor-pointer font-semibold">Xem từng bài đánh giá ({detail.assessment_details.length})</summary>
          <ul className="mt-2 space-y-2">
            {detail.assessment_details.map((item) => <li key={item.id} className="border-t border-slate-700 pt-2">
              <strong>{assessmentTypeLabel(item.type)}</strong> · Hạn ngày thứ {item.due_day} · {item.submitted_day == null
                ? 'Chưa ghi nhận bản nộp đến mốc đánh giá'
                : `Nộp ngày thứ ${item.submitted_day}${item.submitted_day > item.due_day ? ' (sau hạn chung)' : ''}`}
              {item.score != null && ` · Điểm ghi nhận: ${item.score}`}
            </li>)}
          </ul>
          <p className="mt-2 text-amber-300">Chưa có chủ đề/rubric hay hạn cá nhân để kết luận lỗ hổng kiến thức hoặc nguyên nhân chưa nộp.</p>
        </details>}
        <p>Tổng click là số lượt tương tác được ghi trong dữ liệu gốc đến mốc đánh giá; không đo thời gian học hoặc mức hiểu bài.</p>
        {detail.suggestions.map((suggestion) => <div key={suggestion.rule_id} className="rounded-lg border border-slate-700 p-3">
          <p className="font-semibold text-slate-200">{suggestion.title}</p>
          <p className="mt-1 text-amber-300">Giới hạn: {explainObservation(suggestion.limitation)}</p>
          <details className="mt-2">
            <summary className="cursor-pointer">Số liệu làm căn cứ</summary>
            <ul className="mt-1 list-disc pl-4">
              {Object.entries(suggestion.evidence).filter(([key]) => evidenceLabels[key]).map(([key, value]) => (
                <li key={key}>{evidenceLabels[key]}: {displayEvidence(key, value)}</li>
              ))}
            </ul>
          </details>
        </div>)}
        {detail.warnings.some((warning) => !warning.includes('OULAD là dữ liệu lịch sử')) && <div className="text-amber-300">
          <p className="font-semibold">Thông tin còn thiếu hoặc cần kiểm tra</p>
          <ul className="mt-1 list-disc pl-4">
            {[...new Set(detail.warnings.filter((warning) => !warning.includes('OULAD là dữ liệu lịch sử')).map(explainWarning))].map((warning) => <li key={warning}>{warning}</li>)}
          </ul>
        </div>}
      </div>
    </details>
  </section>
);
