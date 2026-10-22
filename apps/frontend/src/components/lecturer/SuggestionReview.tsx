import React, { useId, useState } from 'react';
import { CourseStudentRiskItem, CourseSuggestion, CourseSuggestionResponse } from '@shared/types';

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

type ReviewTab = 'overview' | 'signals' | 'actions' | 'evidence';

const tabs: { id: ReviewTab; label: string }[] = [
  { id: 'overview', label: 'Tổng quan' },
  { id: 'signals', label: 'Dấu hiệu' },
  { id: 'actions', label: 'Gợi ý & giao' },
  { id: 'evidence', label: 'Căn cứ' },
];

interface SuggestionReviewProps {
  detail: CourseSuggestionResponse;
  student: CourseStudentRiskItem;
  selectedRuleId: string | null;
  onChoose: (suggestion: CourseSuggestion) => void;
  children?: React.ReactNode;
}

export const SuggestionReview: React.FC<SuggestionReviewProps> = ({ detail, student, selectedRuleId, onChoose, children }) => {
  const [activeTab, setActiveTab] = useState<ReviewTab>('overview');
  const tabId = useId();
  const prediction = detail.prediction;
  const atRisk = prediction?.prediction_label === 1;
  const probability = prediction?.risk_probability;
  const assessments = detail.assessment_details ?? [];
  const submitted = assessments.filter((item) => item.submitted_day != null).length;
  const submissionPercent = assessments.length ? Math.round(submitted / assessments.length * 100) : 0;
  const circumference = 2 * Math.PI * 44;
  const warnings = [...new Set(detail.warnings
    .filter((warning) => !warning.includes('OULAD là dữ liệu lịch sử'))
    .map(explainWarning))];

  const chooseTab = (event: React.KeyboardEvent<HTMLButtonElement>, index: number) => {
    const next = event.key === 'ArrowRight' ? (index + 1) % tabs.length
      : event.key === 'ArrowLeft' ? (index - 1 + tabs.length) % tabs.length
        : event.key === 'Home' ? 0 : event.key === 'End' ? tabs.length - 1 : -1;
    if (next < 0) return;
    event.preventDefault();
    setActiveTab(tabs[next].id);
    event.currentTarget.parentElement?.querySelectorAll<HTMLButtonElement>('[role="tab"]')[next]?.focus();
  };

  return (
    <section aria-label="Thông tin hỗ trợ quyết định" className="suggestion-review space-y-4 text-sm">
      <div className="flex flex-wrap items-center gap-2 text-xs text-slate-400">
        <span className="rounded-full border border-slate-700 px-3 py-1">
          {detail.source_kind === 'historical_oulad' ? 'Hồ sơ OULAD lịch sử' : 'Hồ sơ học phần'}
        </span>
        {detail.cutoff_day != null && <span>Dữ liệu đến ngày thứ {detail.cutoff_day} của học phần</span>}
        {detail.source_kind !== 'historical_oulad' && detail.status === 'insufficient_data' &&
          <span>Chưa xác minh đủ nguồn dữ liệu gợi ý</span>}
      </div>

      <div role="tablist" aria-label="Các phần gợi ý hỗ trợ" className="flex gap-1 overflow-x-auto rounded-xl border border-slate-700 bg-slate-950/60 p-1">
        {tabs.map((tab, index) => <button
          key={tab.id}
          id={`${tabId}-${tab.id}-tab`}
          role="tab"
          type="button"
          aria-selected={activeTab === tab.id}
          aria-controls={`${tabId}-panel`}
          tabIndex={activeTab === tab.id ? 0 : -1}
          onKeyDown={(event) => chooseTab(event, index)}
          onClick={() => setActiveTab(tab.id)}
          className={`shrink-0 rounded-lg px-3 py-2.5 text-xs font-semibold transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-400 ${
            activeTab === tab.id ? 'bg-brand-600 text-white shadow-sm' : 'text-slate-300 hover:bg-slate-800 hover:text-white'
          }`}
        >{tab.label}</button>)}
      </div>

      <div id={`${tabId}-panel`} role="tabpanel" aria-labelledby={`${tabId}-${activeTab}-tab`} tabIndex={0} className="min-h-64 focus:outline-none">
        {activeTab === 'overview' && <div className="grid gap-4 lg:grid-cols-[220px_1fr]">
          <div className="relative flex flex-col items-center justify-center rounded-2xl border border-slate-700 bg-slate-950/70 p-5 text-center">
            <div className="relative h-32 w-32">
              <svg viewBox="0 0 120 120" className="h-full w-full -rotate-90" aria-hidden="true">
                <circle cx="60" cy="60" r="44" fill="none" stroke="currentColor" strokeWidth="9" className="text-slate-800" />
                {probability != null && <circle cx="60" cy="60" r="44" fill="none" stroke="currentColor" strokeWidth="9"
                  strokeLinecap="round" strokeDasharray={circumference} strokeDashoffset={circumference * (1 - probability)}
                  className={atRisk ? 'text-rose-400' : 'text-brand-400'} />}
              </svg>
              <div className="absolute inset-0 flex items-center justify-center">
                <strong className="whitespace-nowrap text-xl tabular-nums text-white">{probability == null ? '—' : `${(probability * 100).toFixed(1)}%`}</strong>
              </div>
            </div>
            <span className="mt-1 text-xs text-slate-400">xác suất nguy cơ</span>
            <span className={`mt-2 rounded-full px-3 py-1 text-xs font-bold ${probability == null
              ? 'bg-slate-800 text-slate-300'
              : atRisk ? 'bg-rose-500/15 text-rose-300' : 'bg-brand-500/15 text-brand-300'}`}>
              {probability == null ? 'Chưa dự báo' : atRisk ? 'Cần theo dõi' : 'Dưới ngưỡng cảnh báo'}
            </span>
            <p className="mt-3 text-xs leading-relaxed text-slate-400">Xác suất là tín hiệu từ mô hình, không phải mức độ yếu kiến thức.</p>
          </div>
          <div className="grid grid-cols-2 gap-3 content-start">
            <Metric label="Tổng click" value={student.total_clicks == null ? 'Chưa có' : student.total_clicks.toLocaleString('vi-VN')} note={detail.cutoff_day == null ? "Số liệu tổng hợp" : "Đến mốc đánh giá"} />
            <Metric label="Bài đã nộp" value={assessments.length ? `${submitted}/${assessments.length}` : 'Chưa xác nhận'} note="Trong các bài đến hạn" />
            <Metric label="Nộp trễ" value={student.late_submissions == null ? 'Chưa có' : String(student.late_submissions)} note="Đã ghi nhận" />
            <Metric label="Tỷ lệ nộp" value={student.submission_rate == null ? 'Chưa có' : `${(student.submission_rate * 100).toFixed(0)}%`} note={detail.cutoff_day == null ? "Số liệu tổng hợp" : "Tính đến mốc đánh giá"} />
            {assessments.length > 0 && <div className="col-span-2 rounded-xl border border-slate-700 bg-slate-950/50 p-3">
              <div className="flex justify-between text-xs text-slate-300"><span>Tiến độ nộp bài đã ghi nhận</span><strong>{submitted}/{assessments.length}</strong></div>
              <div className="mt-2 h-2 overflow-hidden rounded-full bg-slate-800"><div className="h-full rounded-full bg-brand-400" style={{ width: `${submissionPercent}%` }} /></div>
            </div>}
          </div>
          <p className="lg:col-span-2 rounded-xl border border-amber-500/20 bg-amber-500/5 px-4 py-3 text-xs leading-relaxed text-amber-100">
            {detail.status === 'available' ? 'Có dấu hiệu cần kiểm tra. Xem tab Dấu hiệu, sau đó đối chiếu với sinh viên trước khi chọn hỗ trợ.'
              : 'Chưa đủ căn cứ để nêu điểm yếu cụ thể. Hãy trao đổi với sinh viên trước khi quyết định hỗ trợ.'}
          </p>
        </div>}

        {activeTab === 'signals' && <div className="space-y-3">
          <div className="flex items-center justify-between gap-3">
            <h4 className="font-bold text-white">Những điều cần kiểm tra</h4>
            <span className="text-xs text-slate-400">{detail.suggestions.length} dấu hiệu từ dữ liệu đã xác nhận</span>
          </div>
          {detail.suggestions.length ? <div className="grid gap-3 sm:grid-cols-2">
            {detail.suggestions.map((suggestion) => <div key={suggestion.rule_id} className="rounded-xl border border-slate-700 bg-slate-950/50 p-4">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-brand-300">Dấu hiệu cần đối chiếu</span>
              <h5 className="mt-1 font-bold text-white">{suggestion.title}</h5>
              <p className="mt-2 text-sm leading-relaxed text-slate-300">{explainObservation(suggestion.observation)}</p>
            </div>)}
          </div> : <p className="rounded-xl border border-slate-700 p-4 text-slate-300">
            {detail.status === 'insufficient_data' ? 'Chưa đủ dữ liệu đã xác nhận để đưa ra dấu hiệu cụ thể.' : 'Chưa có dấu hiệu phù hợp; điều này không có nghĩa là sinh viên không cần hỗ trợ.'}
          </p>}
          {detail.warnings.some((warning) => warning.includes('ánh xạ bài đánh giá')) && <p className="text-xs text-amber-200">Chưa biết bài nào đo chủ đề kiến thức nào; giảng viên cần đối chiếu đề bài và tiêu chí chấm.</p>}
        </div>}

        {activeTab === 'actions' && <div className="space-y-4">
          <div>
            <h4 className="font-bold text-white">Giảng viên chọn cách hỗ trợ</h4>
            <p className="mt-1 text-xs text-slate-400">Mô hình không tự chọn bài tập hoặc giao nhiệm vụ.</p>
          </div>
          {detail.suggestions.length ? <div className="grid gap-3 sm:grid-cols-2">
            {detail.suggestions.map((suggestion) => <div key={suggestion.rule_id} className={`rounded-xl border p-4 ${
              selectedRuleId === suggestion.rule_id ? 'border-brand-400 bg-brand-500/10' : 'border-slate-700 bg-slate-950/50'
            }`}>
              <h5 className="font-semibold text-white">{suggestion.title}</h5>
              <p className="mt-2 text-sm leading-relaxed text-slate-300">{suggestion.proposed_action}</p>
              {detail.assignment.can_assign && <button type="button" aria-pressed={selectedRuleId === suggestion.rule_id}
                onClick={() => onChoose(suggestion)} className="mt-3 rounded-lg border border-brand-500/40 px-3 py-2 text-xs font-semibold text-brand-200 hover:bg-brand-500/15">
                {selectedRuleId === suggestion.rule_id ? 'Đã đưa vào nháp' : 'Đưa vào nháp'}
              </button>}
            </div>)}
          </div> : <p className="text-sm text-slate-300">Hãy trao đổi và xác minh nhu cầu hỗ trợ với sinh viên trước khi tự soạn bài.</p>}
          {detail.assignment.can_assign ? children : <div className="rounded-xl border border-amber-500/30 bg-amber-500/5 p-4 text-sm text-amber-100">
            Chỉ xem gợi ý: cần có kế hoạch hỗ trợ đang hoạt động cho đúng sinh viên và học phần trước khi giao bài. Trao đổi với cố vấn để lập kế hoạch.
          </div>}
        </div>}

        {activeTab === 'evidence' && <div className="space-y-4 text-sm text-slate-300">
          <div className="rounded-xl border border-slate-700 bg-slate-950/50 p-4">
            <h4 className="font-bold text-white">Nguồn và giới hạn</h4>
            <p className="mt-2">{detail.source_kind === 'historical_oulad'
              ? `Hồ sơ OULAD lịch sử tại ngày thứ ${detail.cutoff_day} của học phần; không phản ánh sinh viên HUIT hiện tại.`
              : 'Dữ liệu học phần cần được xác nhận trước khi diễn giải thành gợi ý.'}</p>
            <p className="mt-2">{prediction
              ? `Mô hình ước tính xác suất lớp nguy cơ ${(prediction.risk_probability * 100).toFixed(1)}% tại mốc 75% học phần. Con số này không khẳng định kết quả cuối kỳ hoặc mức bài tập phù hợp.`
              : 'Chưa có kết quả dự báo cho dữ liệu học tập mới nhất.'}</p>
            {detail.cutoff_date && <p className="mt-2">Dữ liệu tính đến {displayDate(detail.cutoff_date)}.</p>}
            <p className="mt-2">Tổng click là số lượt tương tác trong dữ liệu gốc; không đo thời gian học hoặc mức hiểu bài.</p>
          </div>
          {assessments.length > 0 && <details className="rounded-xl border border-slate-700 p-4">
            <summary className="cursor-pointer font-semibold text-white">Xem từng bài đánh giá ({assessments.length})</summary>
            <ul className="mt-3 space-y-2 text-xs">{assessments.map((item) => <li key={item.id} className="border-t border-slate-700 pt-2">
              <strong>{assessmentTypeLabel(item.type)}</strong> · Hạn ngày thứ {item.due_day} · {item.submitted_day == null
                ? 'Chưa ghi nhận bản nộp đến mốc đánh giá'
                : `Nộp ngày thứ ${item.submitted_day}${item.submitted_day > item.due_day ? ' (sau hạn chung)' : ''}`}
              {item.score != null && ` · Điểm ghi nhận: ${item.score}`}
            </li>)}</ul>
            <p className="mt-3 text-xs text-amber-200">Chưa có chủ đề/rubric hay hạn cá nhân để kết luận lỗ hổng kiến thức.</p>
          </details>}
          {detail.suggestions.map((suggestion) => <details key={suggestion.rule_id} className="rounded-xl border border-slate-700 p-4">
            <summary className="cursor-pointer font-semibold text-white">Căn cứ cho: {suggestion.title}</summary>
            <p className="mt-3 text-xs text-amber-200">Giới hạn: {explainObservation(suggestion.limitation)}</p>
            <ul className="mt-2 list-disc space-y-1 pl-5 text-xs">{Object.entries(suggestion.evidence).filter(([key]) => evidenceLabels[key]).map(([key, value]) =>
              <li key={key}>{evidenceLabels[key]}: {displayEvidence(key, value)}</li>)}</ul>
          </details>)}
          {warnings.length > 0 && <details className="rounded-xl border border-amber-500/30 p-4">
            <summary className="cursor-pointer font-semibold text-amber-200">Điều dữ liệu chưa cho biết ({warnings.length})</summary>
            <ul className="mt-2 list-disc space-y-2 pl-5 text-xs">{warnings.map((warning) => <li key={warning}>{warning}</li>)}</ul>
          </details>}
        </div>}
      </div>
    </section>
  );
};

const Metric: React.FC<{ label: string; value: string; note: string }> = ({ label, value, note }) => (
  <div className="rounded-xl border border-slate-700 bg-slate-950/50 p-3">
    <p className="text-xs text-slate-400">{label}</p>
    <strong className="mt-1 block text-lg text-white">{value}</strong>
    <p className="text-[11px] text-slate-500">{note}</p>
  </div>
);
