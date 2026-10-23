import React, { useId, useState } from 'react';
import { CourseStudentRiskItem, CourseSuggestion, CourseSuggestionResponse } from '@shared/types';
import { RadarCompetencyChart } from '../recommendation/RadarCompetencyChart';

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

type ReviewTab = 'evidence' | 'actions';

const tabs: { id: ReviewTab; label: string }[] = [
  { id: 'evidence', label: 'Thông tin & căn cứ' },
  { id: 'actions', label: 'Gợi ý & giao bài' },
];

type FeatureKey = keyof NonNullable<NonNullable<CourseSuggestionResponse['student_details']>['model_inputs']>;

const profileFields: Array<[FeatureKey, string]> = [
  ['code_module', 'Mã học phần'], ['gender', 'Giới tính'],
  ['highest_education', 'Trình độ học vấn'], ['age_band', 'Nhóm tuổi'],
  ['studied_credits', 'Số tín chỉ đã đăng ký'], ['date_registration', 'Ngày đăng ký so với ngày bắt đầu'],
];
const activityFields: Array<[FeatureKey, string]> = [
  ['total_clicks_to_t', 'Tổng click'], ['clicks_resource_to_t', 'Lượt mở học liệu'],
  ['clicks_url_to_t', 'Lượt mở liên kết'], ['active_days_to_t', 'Số ngày có hoạt động'],
  ['active_day_ratio', 'Tỷ lệ ngày có hoạt động'], ['days_since_last_activity', 'Ngày từ lần hoạt động cuối'],
  ['clicks_recent_7', 'Lượt tương tác 7 ngày cuối'], ['clicks_recent_30', 'Lượt tương tác 30 ngày cuối'],
];
const assessmentFields: Array<[FeatureKey, string]> = [
  ['assessments_submitted_to_t', 'Số bài đã nộp'], ['late_submissions_to_t', 'Số lượt nộp trễ'],
  ['submission_rate', 'Tỷ lệ nộp bài'],
];

const featureValue = (key: FeatureKey, value: string | number | null | undefined): string => {
  if (value == null) return 'Chưa có dữ liệu';
  if (key === 'gender') return value === 'M' ? 'Nam' : value === 'F' ? 'Nữ' : String(value);
  if (key === 'highest_education') return ({
    'A Level or Equivalent': 'Tương đương THPT', 'HE Qualification': 'Bằng cấp bậc cao',
    'Lower Than A Level': 'Dưới bậc tương đương THPT', 'No Formal quals': 'Chưa có bằng cấp chính quy',
    'Post Graduate Qualification': 'Sau đại học',
  } as Record<string, string>)[String(value)] ?? String(value);
  if (key === 'age_band') return value === '55<=' ? 'Từ 55 tuổi' : `${value} tuổi`;
  if (key === 'date_registration' && typeof value === 'number') return value < 0
    ? `${Math.abs(value)} ngày trước khi bắt đầu` : value === 0 ? 'Ngày bắt đầu' : `${value} ngày sau khi bắt đầu`;
  if (key === 'active_day_ratio' || key === 'submission_rate') return `${(Number(value) * 100).toFixed(1)}%`;
  if (typeof value === 'number') return value.toLocaleString('vi-VN');
  return String(value);
};

type EvidenceFilter = 'all' | 'assessment' | 'activity' | 'context';

const evidenceGroups: Array<{ id: Exclude<EvidenceFilter, 'all'>; title: string; fields: Array<[FeatureKey, string]>; note: string }> = [
  { id: 'assessment', title: 'Bài đánh giá', fields: assessmentFields, note: 'Hạn riêng và chủ đề bài cần được giảng viên đối chiếu.' },
  { id: 'activity', title: 'Hoạt động trên hệ thống', fields: activityFields, note: 'Lượt tương tác và ngày hoạt động không đo mức hiểu bài.' },
  { id: 'context', title: 'Thông tin học phần và nền', fields: profileFields, note: 'Đầu vào mô hình, không tự quyết định mức bài tập.' },
];

const EvidenceInventory: React.FC<{
  detail: CourseSuggestionResponse;
  inputs: NonNullable<CourseSuggestionResponse['student_details']>['model_inputs'];
  observedInputs: NonNullable<CourseSuggestionResponse['student_details']>['observed_features'];
}> = ({ detail, inputs, observedInputs }) => {
  const [filter, setFilter] = useState<EvidenceFilter>('all');
  const values = inputs ?? observedInputs;
  const assessments = detail.assessment_details ?? [];
  const filters: Array<{ id: EvidenceFilter; label: string }> = [
    { id: 'all', label: 'Tất cả' }, { id: 'assessment', label: 'Bài đánh giá' },
    { id: 'activity', label: 'Hoạt động' }, { id: 'context', label: 'Học phần và nền' },
  ];

  return <section className="rounded-2xl border border-slate-700 bg-slate-950/50 p-4 sm:p-5" aria-label="Dữ liệu ghi nhận">
    <div className="flex flex-wrap items-start justify-between gap-3">
      <div>
        <h4 className="font-bold text-white">Dữ liệu ghi nhận</h4>
        <p className="mt-1 text-xs text-slate-300">{values ? 'Toàn bộ 17 đầu vào được chia nhóm để đối chiếu, không xếp hạng nguyên nhân.' : 'Chưa có bộ đầu vào để hiển thị đầy đủ.'}</p>
      </div>
      <span className="rounded-full border border-slate-600 px-3 py-1 text-xs text-slate-300">
        {inputs ? 'Đầu vào lưu cùng lần dự báo' : values ? 'Số liệu quan sát, chưa khớp lần dự báo' : 'Thiếu dữ liệu'}
      </span>
    </div>
    <div className="mt-4 flex flex-wrap gap-2" aria-label="Lọc nhóm dữ liệu">
      {filters.map((item) => <button key={item.id} type="button" aria-pressed={filter === item.id} onClick={() => setFilter(item.id)}
        className={'rounded-full border px-3 py-1.5 text-xs font-semibold focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-400 ' + (filter === item.id ? 'border-brand-500 bg-brand-600 text-white' : 'border-slate-600 text-slate-300 hover:border-brand-400')}>
        {item.label}
      </button>)}
    </div>
    <div className="mt-4 space-y-4">
      {evidenceGroups.filter((group) => filter === 'all' || filter === group.id).map((group) => <div key={group.id} className="rounded-xl border border-slate-700 bg-slate-800/50 p-3 sm:p-4">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <h5 className="font-semibold text-white">{group.title}</h5>
          <span className="text-xs text-slate-400">{group.fields.length} chỉ số</span>
        </div>
        <p className="mt-1 text-xs text-slate-400">{group.note}</p>
        {group.id === 'assessment' && assessments.length > 0 && <div className="mt-3 rounded-lg border border-amber-500/30 bg-amber-500/5 p-3" aria-label="Bài đến hạn có bản nộp">
          <div className="flex items-baseline justify-between gap-2 text-xs"><span>Bài đến hạn có bản nộp</span><strong className="tabular-nums">{assessments.filter((item) => item.submitted_day != null).length}/{assessments.length}</strong></div>
          <div className="mt-2 h-2 overflow-hidden rounded-full bg-slate-700" role="progressbar" aria-label="Bài có bản nộp" aria-valuenow={assessments.filter((item) => item.submitted_day != null).length} aria-valuemin={0} aria-valuemax={assessments.length}>
            <div className="h-full bg-brand-400" style={{ width: String(assessments.filter((item) => item.submitted_day != null).length / assessments.length * 100) + '%' }} />
          </div>
          <p className="mt-2 text-xs tabular-nums text-slate-300">Tỷ lệ có bản nộp: {assessments.filter((item) => item.submitted_day != null).length} ÷ {assessments.length} × 100 = {(assessments.filter((item) => item.submitted_day != null).length / assessments.length * 100).toFixed(1)}%.</p>
        </div>}
        <dl className="mt-3 grid gap-x-5 sm:grid-cols-2">
          {group.fields.map(([key, label]) => <div key={key} className="flex items-baseline justify-between gap-3 border-t border-slate-700 py-2 text-xs">
            <dt className="min-w-0 text-slate-300">{label}</dt>
            <dd className="shrink-0 text-right font-semibold tabular-nums text-white">{featureValue(key, values?.[key])}</dd>
          </div>)}
        </dl>
        {group.id === 'assessment' && <details className="mt-2 border-t border-slate-700 pt-3 text-xs">
          <summary className="cursor-pointer font-semibold text-brand-300">{assessments.length ? 'Xem đủ ' + assessments.length + ' bài đến hạn' : 'Chưa xác nhận được từng bài đến hạn'}</summary>
          {assessments.length > 0 && <ul className="mt-3 space-y-2">{assessments.map((item) => <li key={item.id} className="flex flex-wrap justify-between gap-2 rounded-lg bg-slate-950/50 p-2">
            <span>{assessmentTypeLabel(item.type)} · hạn ngày thứ {item.due_day}</span>
            <strong>{item.submitted_day == null ? 'Chưa ghi nhận nộp' : 'Nộp ngày thứ ' + item.submitted_day + (item.submitted_day > item.due_day ? ' · sau hạn chung' : '')}{item.score != null ? ' · điểm ' + item.score : ''}</strong>
          </li>)}</ul>}
        </details>}
      </div>)}
    </div>
    <p className="mt-4 border-t border-slate-700 pt-3 text-xs text-slate-400">Các chỉ số liên quan có thể cùng phản ánh một hoạt động. Số liệu quan sát không phải nguyên nhân hay chẩn đoán; biểu đồ đóng góp cho mô hình nằm riêng ở phần dự báo.</p>
  </section>;
};

const contributionText = (value: number): string => Math.abs(value) < 0.000001 ? '≈0'
  : (value > 0 ? '+' : '') + value.toFixed(Math.abs(value) < 0.0005 ? 6 : 3);

const featureDescriptions: Record<FeatureKey, string> = {
  code_module: 'Mã học phần trong dữ liệu OULAD; không phải kết quả học tập.',
  gender: 'Thông tin nền, không dùng làm căn cứ giao bài.',
  highest_education: 'Trình độ học vấn đã khai báo; không xác định kiến thức yếu trong học phần.',
  age_band: 'Nhóm tuổi trong dữ liệu gốc, không dùng làm căn cứ giao bài.',
  studied_credits: 'Số tín chỉ đã đăng ký theo hồ sơ OULAD; không chỉ riêng học phần này.',
  date_registration: 'Số ngày đăng ký so với ngày bắt đầu học phần.',
  total_clicks_to_t: 'Tổng lượt tương tác trên hệ thống đến mốc đánh giá; không đo thời gian học.',
  clicks_resource_to_t: 'Lượt tương tác với học liệu đến mốc đánh giá; không đo mức hiểu bài.',
  clicks_url_to_t: 'Lượt tương tác với liên kết đến mốc đánh giá.',
  active_days_to_t: 'Số ngày ghi nhận hoạt động trên hệ thống đến mốc đánh giá.',
  assessments_submitted_to_t: 'Số bài đã ghi nhận nộp đến mốc đánh giá; cần xem từng bài bên dưới.',
  late_submissions_to_t: 'Số lượt nộp trễ tổng hợp; chưa xác định bài nào trễ.',
  active_day_ratio: 'Tỷ lệ ngày ghi nhận hoạt động trong khoảng thời gian đã quan sát.',
  submission_rate: 'Tỷ lệ bài đã ghi nhận nộp trong các bài đến hạn.',
  days_since_last_activity: 'Số ngày từ hoạt động gần nhất đến mốc đánh giá, không phải hiện tại.',
  clicks_recent_7: 'Lượt tương tác trong 7 ngày trước mốc đánh giá, không đo thời gian học.',
  clicks_recent_30: 'Lượt tương tác trong 30 ngày trước mốc đánh giá, không đo thời gian học.',
};

const ModelContributionPanel: React.FC<{ detail: CourseSuggestionResponse }> = ({ detail }) => {
  const tooltipId = useId().replace(/:/g, '');
  const explanation = detail.prediction_explanation;
  if (!explanation) return <div className="rounded-xl border border-slate-700 bg-slate-950/50 p-4 text-xs text-slate-300">
    Chưa có giải thích kiểm chứng được cho lần dự báo này. Dữ liệu ghi nhận bên dưới vẫn có thể dùng để đối chiếu, nhưng không phải mức đóng góp của mô hình.
  </div>;

  const contributions = explanation.contributions;
  const inputs = detail.student_details?.model_inputs;
  const maximum = Math.max(...Object.values(contributions).map((value) => Math.abs(value)), 0.001);
  const contributionSum = Object.values(contributions).reduce((sum, value) => sum + value, 0);
  const finalMargin = explanation.base_margin + contributionSum;
  return <section className="rounded-2xl border border-slate-700 bg-slate-950/50 p-4 sm:p-5" aria-label="Ảnh hưởng của 17 đầu vào tới dự báo">
    <div className="flex flex-wrap items-baseline justify-between gap-2">
      <h4 className="font-bold text-white">Mô hình dựa vào những gì</h4>
      <span className="text-xs text-slate-400">Đủ 17 đầu vào · cùng lần dự báo</span>
    </div>
    <p className="mt-2 text-xs text-slate-300">Cam: đẩy dự báo về phía nguy cơ. Xanh: kéo theo chiều ngược lại. Không có ngưỡng “ảnh hưởng cao/thấp” dùng chung cho mọi sinh viên.</p>
    <p className="mt-2 text-xs text-slate-400">Vạch giữa là 0; thanh dài nhất của hồ sơ này làm mốc, các thanh khác dùng cùng thước đo. Rê chuột hoặc dùng Tab để xem số liệu và cách đọc từng thanh. Chiều dài không phải phần trăm nguyên nhân.</p>
    <div className="mt-4 grid gap-1 text-[11px] text-slate-400 sm:grid-cols-[minmax(0,180px)_minmax(0,1fr)_84px] sm:items-end sm:gap-3" aria-label="Thước đo đóng góp của hồ sơ này">
      <span>Thước đo của hồ sơ này</span>
      <div className="flex justify-between tabular-nums"><span>−{contributionText(maximum).replace('+', '')}</span><span>0</span><span>+{contributionText(maximum).replace('+', '')}</span></div>
      <span className="sm:text-right">điểm mô hình</span>
    </div>
    <div className="mt-3 space-y-3">
      {evidenceGroups.map((group) => <details key={group.id} open={group.id === 'assessment' ? true : undefined} className="rounded-xl border border-slate-700 bg-slate-950/50 p-3">
        <summary className="cursor-pointer font-semibold text-white">{group.title} <span className="text-xs font-normal text-slate-400">({group.fields.length} đầu vào)</span></summary>
        <div className="mt-3 space-y-3">{group.fields.map(([key, label]) => {
          const value = contributions[key];
          const width = Math.abs(value) / maximum * 100;
          return <div key={key} className="grid gap-1 text-xs sm:grid-cols-[minmax(0,180px)_minmax(0,1fr)_84px] sm:items-center sm:gap-3">
            <span className="text-slate-200">{label}{inputs && <small className="block text-slate-400">{featureValue(key, inputs[key])}</small>}</span>
            <div className="contribution-track relative h-5 rounded bg-slate-900 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-400" role="img" tabIndex={0}
              aria-label={label + ': ' + (value > 0 ? 'đẩy dự báo về phía nguy cơ' : value < 0 ? 'kéo dự báo theo chiều ngược lại' : 'không ghi nhận ảnh hưởng') + ', ' + contributionText(value) + ' điểm log-odds'}
              aria-describedby={`${tooltipId}-${key}`}>
              <span className="absolute inset-y-0 left-1/2 w-px bg-slate-500" />
              {value !== 0 && <span className={`absolute inset-y-0 rounded-sm ${value > 0 ? 'bg-amber-400' : 'bg-sky-400'}`} style={{ width: (width / 2) + '%', left: value > 0 ? '50%' : (50 - width / 2) + '%' }} />}
              <span id={`${tooltipId}-${key}`} role="tooltip" className="contribution-tooltip">
                <strong>{label}</strong>
                <span>Giá trị ghi nhận: {inputs ? featureValue(key, inputs[key]) : 'Chưa có'}</span>
                <span className="contribution-tooltip-note">{featureDescriptions[key]}</span>
                <span>{value > 0 ? 'Đẩy điểm dự báo về phía nguy cơ' : value < 0 ? 'Kéo điểm dự báo theo chiều ngược lại' : 'Không ghi nhận ảnh hưởng ở lần này'}: {contributionText(value)} điểm.</span>
                <span className="contribution-tooltip-note">Thanh dài ngắn chỉ so với các đầu vào khác của cùng hồ sơ; không phải mức độ nghiêm trọng.</span>
              </span>
            </div>
            <span className={`tabular-nums sm:text-right ${value > 0 ? 'text-amber-200' : value < 0 ? 'text-sky-200' : 'text-slate-400'}`}>{contributionText(value)} <span className="text-slate-500">điểm</span></span>
          </div>;
        })}</div>
      </details>)}
    </div>
    <details className="mt-4 border-t border-slate-700 pt-3 text-xs text-slate-300">
      <summary className="cursor-pointer font-semibold text-brand-300">Cách đọc và giới hạn</summary>
      <div className="mt-3 grid gap-2 sm:grid-cols-4" aria-label="Các bước tính dự báo của hồ sơ">
        <div className="rounded-lg bg-slate-800/60 p-3"><span className="block text-slate-400">Điểm nền</span><strong className="mt-1 block tabular-nums text-white">{contributionText(explanation.base_margin)}</strong></div>
        <div className="rounded-lg bg-slate-800/60 p-3"><span className="block text-slate-400">Tổng 17 đóng góp</span><strong className="mt-1 block tabular-nums text-white">{contributionText(contributionSum)}</strong></div>
        <div className="rounded-lg bg-slate-800/60 p-3"><span className="block text-slate-400">Điểm cuối</span><strong className="mt-1 block tabular-nums text-white">{contributionText(finalMargin)}</strong></div>
        <div className="rounded-lg bg-brand-500/10 p-3"><span className="block text-slate-300">Xác suất dự báo</span><strong className="mt-1 block tabular-nums text-white">{detail.prediction ? (detail.prediction.risk_probability * 100).toFixed(1) + '%' : 'Chưa có'}</strong></div>
      </div>
      <p className="mt-2">Điểm cuối = điểm nền + tổng 17 đóng góp; xác suất = 1 / (1 + e^(-điểm cuối)). Các điểm hiển thị đã làm tròn.</p>
      <p className="mt-2">Đây là đóng góp LightGBM trên thang log-odds: điểm nền của mô hình cộng đủ 17 giá trị khôi phục đúng dự báo đã lưu. Các cột mã hóa của cùng một thuộc tính được cộng lại trước khi vẽ. Giá trị 0 không có nghĩa là chỉ số đó không quan trọng ở ca khác.</p>
      <p className="mt-2">Các chỉ số có thể liên quan nhau; thay đổi một giá trị riêng lẻ không đảm bảo xác suất thay đổi đúng bằng thanh hiển thị. Không dùng giới tính, tuổi hay trình độ để tự chọn mức bài tập. Dấu hiệu quan sát và gợi ý ở phần sau được xác định bằng quy tắc riêng.</p>
    </details>
  </section>;
};

interface SuggestionReviewProps {
  detail: CourseSuggestionResponse;
  student: CourseStudentRiskItem;
  selectedRuleId: string | null;
  onChoose: (suggestion: CourseSuggestion) => void;
  children?: React.ReactNode;
}

export const SuggestionReview: React.FC<SuggestionReviewProps> = ({ detail, student, selectedRuleId, onChoose, children }) => {
  const [activeTab, setActiveTab] = useState<ReviewTab>('evidence');
  const [showRiskDetails, setShowRiskDetails] = useState(false);
  const tabId = useId();
  const prediction = detail.prediction;
  const probability = prediction?.risk_probability;
  const assessments = detail.assessment_details ?? [];
  const submitted = assessments.filter((item) => item.submitted_day != null).length;
  const circumference = 2 * Math.PI * 44;
  const recordedInputs = detail.student_details?.model_inputs;
  const inputs = recordedInputs ?? detail.student_details?.observed_features;
  const history = detail.history ?? [];
  const warnings = [...new Set(detail.warnings
    .filter((warning) => !warning.includes('OULAD là dữ liệu lịch sử'))
    .map(explainWarning))];
  const selectedSuggestionIsVisible = detail.suggestions.some((suggestion) => suggestion.rule_id === selectedRuleId);
  const assignmentForm = <div className="rounded-xl border border-brand-500/40 bg-slate-950/70 p-4 sm:p-5" aria-label="Quyết định của giảng viên">
    <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
      <h5 className="font-semibold text-white">Giảng viên xem xét và giao bài</h5>
      {!detail.assignment.can_assign && <span className="rounded-full bg-amber-500/10 px-3 py-1 text-xs font-semibold text-amber-200">Chưa thể giao</span>}
    </div>
    <p className="mb-3 text-xs text-slate-300">Nội dung gợi ý chỉ điền vào bản soạn. Giảng viên kiểm tra, chỉnh sửa và chủ động quyết định giao.</p>
    {!detail.assignment.can_assign && <p className="mb-4 rounded-lg border border-amber-500/30 bg-amber-500/5 p-3 text-xs text-amber-100">Cần kế hoạch hỗ trợ đang hoạt động trong học phần để giao bài. Hãy liên hệ cố vấn lập hoặc kích hoạt kế hoạch; nội dung đang soạn chưa được lưu.</p>}
    {children}
  </div>;

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
        {detail.cutoff_day != null && <span>Đến ngày thứ {detail.cutoff_day} của học phần</span>}
        {detail.source_kind !== 'historical_oulad' && detail.status === 'insufficient_data' &&
          <span>Chưa xác minh đủ nguồn dữ liệu gợi ý</span>}
      </div>

      <div role="tablist" aria-label="Các phần hỗ trợ giảng viên" className="flex gap-1 overflow-x-auto rounded-xl border border-slate-700 bg-slate-950/60 p-1">
        {tabs.map((tab, index) => <button
          key={tab.id} id={`${tabId}-${tab.id}-tab`} role="tab" type="button"
          aria-selected={activeTab === tab.id} aria-controls={`${tabId}-panel`}
          tabIndex={activeTab === tab.id ? 0 : -1}
          onKeyDown={(event) => chooseTab(event, index)} onClick={() => setActiveTab(tab.id)}
          className={`shrink-0 rounded-lg px-3 py-2.5 text-xs font-semibold transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-400 ${
            activeTab === tab.id ? 'bg-brand-600 text-white shadow-sm' : 'text-slate-300 hover:bg-slate-800 hover:text-white'
          }`}
        >{tab.label}</button>)}
      </div>

      <div id={`${tabId}-panel`} role="tabpanel" aria-labelledby={`${tabId}-${activeTab}-tab`} tabIndex={0} className="min-h-64 focus:outline-none">
        {activeTab === 'evidence' && <div className="space-y-4">
          <div className="grid gap-4 md:grid-cols-[200px_minmax(0,1fr)]">
            <div className="flex flex-col items-center justify-center rounded-2xl border border-slate-700 bg-slate-950/70 p-5 text-center">
              <div className="relative h-32 w-32">
                <svg viewBox="0 0 120 120" className="h-full w-full -rotate-90" aria-hidden="true">
                  <circle cx="60" cy="60" r="44" fill="none" stroke="currentColor" strokeWidth="9" className="text-slate-800" />
                  {probability != null && <circle cx="60" cy="60" r="44" fill="none" stroke="currentColor" strokeWidth="9"
                    strokeLinecap="round" strokeDasharray={circumference} strokeDashoffset={circumference * (1 - probability)}
                    className={prediction?.prediction_label === 1 ? 'text-rose-400' : 'text-brand-400'} />}
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                  <strong className="text-xl tabular-nums text-white">{probability == null ? '—' : `${(probability * 100).toFixed(1)}%`}</strong>
                </div>
              </div>
              <span className="mt-1 text-xs text-slate-400">Xác suất lớp nguy cơ</span>
              <span className={`mt-2 rounded-full px-3 py-1 text-xs font-bold ${probability == null
                ? 'bg-slate-800 text-slate-300'
                : prediction?.prediction_label === 1 ? 'bg-rose-500/15 text-rose-300' : 'bg-brand-500/15 text-brand-300'}`}>
                {probability == null ? 'Chưa dự báo' : prediction?.prediction_label === 1 ? 'Cần theo dõi' : 'Dưới ngưỡng cảnh báo'}
              </span>
              {prediction && <span className="mt-2 text-xs text-slate-400">Ngưỡng cảnh báo: {(prediction.threshold * 100).toFixed(0)}%</span>}
              <button type="button" className="mt-3 text-xs font-semibold text-brand-300 underline underline-offset-2 hover:text-brand-200"
                aria-expanded={showRiskDetails} aria-controls={`${tabId}-risk-details`}
                onClick={() => setShowRiskDetails(!showRiskDetails)}>
                {showRiskDetails ? 'Ẩn chi tiết' : 'Xem chi tiết'}
              </button>
            </div>
            <div className="grid grid-cols-2 content-start gap-3">
              <Metric label="Tổng click" value={student.total_clicks == null ? 'Chưa có' : student.total_clicks.toLocaleString('vi-VN')} note="Tương tác trong dữ liệu gốc" />
              <Metric label="Nộp trễ" value={student.late_submissions == null ? 'Chưa có' : String(student.late_submissions)} note="Số lượt ghi nhận" />
              <Metric label="Tỷ lệ nộp" value={student.submission_rate == null ? 'Chưa có' : `${(student.submission_rate * 100).toFixed(0)}%`} note="Đến mốc đánh giá" />
              <Metric label="Bài đến hạn" value={assessments.length ? `${submitted}/${assessments.length}` : 'Chưa xác nhận'} note="Có bản nộp ghi nhận" />
            </div>
          </div>
          {showRiskDetails && <div id={`${tabId}-risk-details`} className="space-y-4">
            <div className="rounded-xl border border-slate-700 bg-slate-950/50 p-4">
              <h4 className="font-semibold text-white">Bức tranh học tập tại mốc đánh giá</h4>
              <p className="mt-1 text-xs text-slate-300">Các dấu hiệu giúp đối chiếu với sinh viên, không phải phần trăm đóng góp hoặc nguyên nhân gây ra kết quả học tập.</p>
            </div>
            {inputs ? <RadarCompetencyChart features={inputs} compact /> :
              <p className="rounded-xl border border-slate-700 p-4 text-slate-300">Chưa có đủ dữ liệu hành vi để vẽ đối sánh sáu chỉ số.</p>}
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              <Metric label="Học liệu / liên kết" value={inputs ? `${featureValue('clicks_resource_to_t', inputs.clicks_resource_to_t)} / ${featureValue('clicks_url_to_t', inputs.clicks_url_to_t)}` : 'Chưa có'} note="Lượt mở trong dữ liệu gốc" />
              <Metric label="Hoạt động 7 / 30 ngày cuối" value={inputs ? `${featureValue('clicks_recent_7', inputs.clicks_recent_7)} / ${featureValue('clicks_recent_30', inputs.clicks_recent_30)}` : 'Chưa có'} note="Lượt tương tác, không phải thời gian học" />
              <Metric label="Lần hoạt động gần nhất" value={inputs?.days_since_last_activity == null ? 'Chưa có' : `${inputs.days_since_last_activity} ngày trước`} note="Tính đến mốc đánh giá" />
              <Metric label="Bài có bản nộp" value={assessments.length ? `${submitted}/${assessments.length}` : 'Chưa xác nhận'} note="Trong các bài đến hạn được ghi nhận" />
              <Metric label="Nộp sau hạn chung" value={inputs?.late_submissions_to_t == null ? 'Chưa có' : featureValue('late_submissions_to_t', inputs.late_submissions_to_t)} note="Cần đối chiếu hạn riêng từng bài" />
              <Metric label="Ngày có hoạt động" value={inputs?.active_days_to_t == null ? 'Chưa có' : featureValue('active_days_to_t', inputs.active_days_to_t)} note="Không suy ra mức độ hiểu bài" />
            </div>
          </div>}
          <div className="rounded-xl border border-slate-700 bg-slate-950/50 p-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h4 className="font-semibold text-white">Giảng viên cần kiểm tra</h4>
              <button type="button" onClick={() => setActiveTab('actions')} className="text-xs font-semibold text-brand-300 hover:text-brand-200">Xem gợi ý và giao bài →</button>
            </div>
            {detail.suggestions.length ? <ul className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {detail.suggestions.map((suggestion) => <li key={suggestion.rule_id} className="rounded-lg border border-slate-700 bg-slate-800/60 p-3">
                <EvidenceVisual suggestion={suggestion} />
                <p className="mt-3 text-xs leading-relaxed text-slate-300">{explainObservation(suggestion.observation)}</p>
              </li>)}
            </ul> : <p className="mt-2 text-slate-300">{detail.status === 'insufficient_data' ? 'Chưa đủ căn cứ đã xác nhận để nêu dấu hiệu cụ thể.' : 'Chưa có dấu hiệu phù hợp quy tắc; vẫn cần trao đổi với sinh viên.'}</p>}
          </div>
          <p className="text-xs text-slate-400">Xác suất giúp ưu tiên xem xét, không đo mức hiểu bài. Tổng click không đo thời gian học.</p>
        <ModelContributionPanel detail={detail} />

        <div className="space-y-4">
          <div>
            <h4 className="font-bold text-white">Hồ sơ để đối chiếu với sinh viên</h4>
            <p className="mt-1 text-xs text-slate-400">{student.full_name} · {student.student_code}. {recordedInputs
              ? 'Các giá trị đã ghi cùng lần dự báo, không phải tình hình hiện tại.'
              : 'Các giá trị từ snapshot/hồ sơ mới nhất; chưa có bản ghi đủ để xác nhận chính xác đầu vào lần dự báo.'}</p>
          </div>
          <EvidenceInventory detail={detail} inputs={recordedInputs ?? null} observedInputs={detail.student_details?.observed_features ?? null} />
          <p className="rounded-xl border border-slate-700 bg-slate-950/50 p-4 text-xs text-slate-300">Số lần học trước học phần này: <strong className="text-white">{detail.student_details?.previous_attempts ?? 'Chưa có dữ liệu'}</strong>. Chỉ để đối chiếu hồ sơ, không dùng để suy luận kiến thức còn yếu.</p>
          <details className="rounded-xl border border-slate-700 bg-slate-950/50 p-4 text-xs text-slate-300">
            <summary className="cursor-pointer font-semibold text-white">Nguồn và giới hạn dữ liệu</summary>
            <p className="mt-3">{detail.source_kind === 'historical_oulad'
              ? `OULAD lịch sử, đến ngày thứ ${detail.cutoff_day} của học phần; không phải dữ liệu sinh viên HUIT hiện tại.`
              : `Hồ sơ học phần${detail.cutoff_date ? `, tính đến ${displayDate(detail.cutoff_date)}` : ', chưa xác nhận mốc đánh giá'}.`}</p>
            <p className="mt-2">Xác suất chỉ để ưu tiên xem xét; chưa xác định điểm yếu kiến thức hoặc mức bài tập phù hợp.</p>
            {warnings.length > 0 && <ul className="mt-2 list-disc space-y-1 pl-5">{warnings.map((warning) => <li key={warning}>{warning}</li>)}</ul>}
          </details>
        </div>
        </div>}

        {activeTab === 'actions' && <div className="space-y-5">
          <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-slate-700 bg-slate-950/50 p-4 sm:p-5">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-brand-300">Giảng viên quyết định</p>
              <p className="mt-1 font-semibold text-white">{detail.suggestions.length} dấu hiệu có hướng hỗ trợ tham khảo</p>
              <p className="mt-1 text-xs text-slate-400">Mỗi dấu hiệu cần đối chiếu trước khi chọn và chỉnh sửa bài tập.</p>
            </div>
            <button type="button" onClick={() => setActiveTab('evidence')} className="rounded-lg border border-brand-500/50 px-3 py-2 text-xs font-semibold text-brand-200 hover:bg-brand-500/15 focus-visible:outline focus-visible:outline-2 focus-visible:outline-brand-400">Xem thông tin & căn cứ</button>
          </div>
          <div>
            <h4 className="font-bold text-white">Dấu hiệu ghi nhận và hướng hỗ trợ</h4>
            <p className="mt-1 text-xs text-slate-400">{detail.suggestions.length} dấu hiệu đủ căn cứ để gợi ý theo quy tắc. Mỗi dòng nối số liệu với hướng hỗ trợ và quyết định của giảng viên; không phải toàn bộ nguyên nhân dự báo.</p>
          </div>
          <div className="overflow-hidden rounded-xl border border-slate-700" aria-label="Các gợi ý có căn cứ">
            <div className="hidden grid-cols-[minmax(0,1.2fr)_minmax(0,1fr)_auto] gap-4 bg-slate-800/50 px-4 py-2 text-xs font-semibold text-slate-300 sm:grid">
              <span>Dữ liệu ghi nhận</span><span>Hướng hỗ trợ</span><span>Giảng viên</span>
            </div>
            {detail.suggestions.map((suggestion) => <div key={suggestion.rule_id} className={`grid gap-3 border-t border-slate-700 px-4 py-3 text-xs sm:grid-cols-[minmax(0,1.2fr)_minmax(0,1fr)_auto] sm:items-center ${selectedRuleId === suggestion.rule_id ? 'bg-brand-500/10' : 'bg-slate-950/50'}`}>
              <div className="min-w-0"><strong className="text-sm text-white">{suggestion.title}</strong><p className="mt-1 leading-relaxed text-slate-300">{explainObservation(suggestion.observation)}</p></div>
              <p className="min-w-0 leading-relaxed text-brand-200">{suggestion.proposed_action}</p>
              <button type="button" aria-pressed={selectedRuleId === suggestion.rule_id} onClick={() => onChoose(suggestion)}
                className="justify-self-start rounded-lg border border-brand-500/50 px-3 py-2 font-semibold text-brand-200 hover:bg-brand-500/15 sm:justify-self-end">
                {selectedRuleId === suggestion.rule_id ? 'Đang soạn' : 'Xem và soạn'}
              </button>
            </div>)}
          </div>
          <div className="space-y-3" aria-label="Chi tiết dấu hiệu đang chọn">
                {detail.suggestions.filter((suggestion) => suggestion.rule_id === selectedRuleId).map((suggestion) => {
                  const assigned = history.filter((item) => item.rule_id === suggestion.rule_id);
                  return <article key={suggestion.rule_id} className={`rounded-lg border p-3 ${selectedRuleId === suggestion.rule_id ? 'border-brand-400 bg-brand-500/10' : 'border-slate-700 bg-slate-800/50'}`}>
                    <h5 className="mb-3 font-semibold text-white">{suggestion.title}</h5>
                    <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                      <div className="min-w-0 flex-1"><p className="text-xs font-semibold text-amber-200">Dữ liệu ghi nhận</p><p className="mt-1 text-slate-100">{explainObservation(suggestion.observation)}</p></div>
                      <button type="button" aria-pressed={selectedRuleId === suggestion.rule_id} onClick={() => onChoose(suggestion)}
                        className="shrink-0 rounded-lg border border-brand-500/40 px-3 py-2 text-xs font-semibold text-brand-200 hover:bg-brand-500/15">
                        {selectedRuleId === suggestion.rule_id ? 'Đang soạn từ gợi ý này' : 'Chọn để soạn bài'}
                      </button>
                    </div>
                    <div className="mt-3 grid gap-3 border-t border-slate-700 pt-3 sm:grid-cols-[minmax(0,170px)_minmax(0,1fr)]">
                      <EvidenceVisual suggestion={suggestion} />
                      <div className="min-w-0 rounded-xl border border-brand-500/20 bg-brand-500/5 p-4 text-xs text-slate-200"><span className="font-semibold text-brand-200">Hướng hỗ trợ tham khảo</span><p className="mt-2 text-sm leading-relaxed text-slate-100">{suggestion.proposed_action}</p></div>
                    </div>
                    {selectedRuleId === suggestion.rule_id && <div className="mt-4">{assignmentForm}</div>}
                    <details className="mt-3 border-t border-slate-700 pt-3 text-xs">
                      <summary className="cursor-pointer font-semibold text-slate-200">Lịch sử giao bài theo dấu hiệu này ({assigned.length})</summary>
                      {assigned.length ? <ul className="mt-2 space-y-2">{assigned.map((item) =>
                        <li key={item.task_id} className="flex flex-wrap items-start justify-between gap-2 rounded-lg bg-slate-800/50 px-3 py-2">
                          <div><strong className="text-white">{item.title}</strong><p className="text-slate-400">Giao {new Date(item.assigned_at).toLocaleString('vi-VN')}{item.snapshot_id !== detail.snapshot_id ? ' · theo dữ liệu cũ' : ''}</p></div>
                          <span className={item.is_completed ? 'text-brand-300' : 'text-amber-200'}>{item.is_completed ? 'Đã hoàn thành' : 'Đang thực hiện'}</span>
                        </li>)}</ul> : <p className="mt-1 text-slate-400">Chưa ghi nhận nhiệm vụ gắn với gợi ý này.</p>}
                    </details>
                    <details className="mt-3 border-t border-slate-700 pt-2 text-xs text-slate-300">
                      <summary className="cursor-pointer font-semibold text-slate-200">Xem căn cứ và điều chưa thể kết luận</summary>
                      <div className="mt-3 grid gap-2 sm:grid-cols-2">{Object.entries(suggestion.evidence).filter(([key]) => evidenceLabels[key]).map(([key, value]) =>
                        <p key={key}><span className="text-slate-400">{evidenceLabels[key]}:</span> {displayEvidence(key, value)}</p>)}</div>
                      <p className="mt-3 text-amber-200">Chưa thể kết luận: {explainObservation(suggestion.limitation)}</p>
                    </details>
                  </article>;
                })}
          </div>
          {!selectedSuggestionIsVisible && assignmentForm}
          {!detail.suggestions.length && <p className="text-xs text-slate-400">Chưa có gợi ý nào đủ điều kiện theo các quy tắc hiện tại. Dữ liệu ghi nhận vẫn có thể được đối chiếu để giảng viên tự xác minh và soạn bài.</p>}
          {history.some((item) => !item.rule_id || !detail.suggestions.some((suggestion) => suggestion.rule_id === item.rule_id)) && <details className="rounded-xl border border-slate-700 bg-slate-950/50 p-4 text-xs">
            <summary className="cursor-pointer font-semibold text-white">Nhiệm vụ từ dấu hiệu cũ hoặc giảng viên tự xác minh</summary>
            <ul className="mt-3 space-y-2">{history.filter((item) => !item.rule_id || !detail.suggestions.some((suggestion) => suggestion.rule_id === item.rule_id)).map((item) =>
              <li key={item.task_id} className="flex justify-between gap-3 rounded-lg bg-slate-800/50 p-3">
                <span>{item.title} · {new Date(item.assigned_at).toLocaleString('vi-VN')}</span>
                <span className="shrink-0">{item.is_completed ? 'Đã hoàn thành' : 'Đang thực hiện'}</span>
              </li>)}</ul>
          </details>}

        </div>}
      </div>
    </section>
  );
};

const EvidenceVisual: React.FC<{ suggestion: CourseSuggestion }> = ({ suggestion }) => {
  const evidence = suggestion.evidence;
  const due = Number(evidence.assessments_due);
  const missing = Number(evidence.assessments_missing);
  if (suggestion.rule_id === 'G01' && due > 0 && Number.isFinite(missing) && missing >= 0 && missing <= due) {
    return <div className="flex flex-col justify-center rounded-xl border border-amber-500/30 bg-amber-500/10 p-4" aria-label={`${missing} trong ${due} bài đến hạn chưa ghi nhận nộp`}>
      <span className="text-xs text-amber-200">Bài đến hạn chưa ghi nhận nộp</span>
      <strong className="mt-2 text-3xl tabular-nums text-white">{missing}<span className="text-base text-slate-300">/{due}</span></strong>
      <div className="mt-3 h-2 overflow-hidden rounded-full bg-slate-700" role="progressbar" aria-label="Bài chưa ghi nhận nộp" aria-valuenow={missing} aria-valuemin={0} aria-valuemax={due}>
        <div className="h-full bg-amber-400" style={{ width: `${missing / due * 100}%` }} />
      </div>
    </div>;
  }
  if (suggestion.rule_id === 'G02_AGGREGATE' && typeof evidence.late_submissions_to_t === 'number') {
    return <div className="flex flex-col justify-center rounded-xl border border-amber-500/30 bg-amber-500/10 p-4">
      <span className="text-xs text-amber-200">Số lượt nộp trễ ghi nhận</span>
      <strong className="mt-2 text-3xl tabular-nums text-white">{evidence.late_submissions_to_t}</strong>
      <span className="mt-2 text-xs text-slate-300">Số tổng hợp, chưa xác định từng bài</span>
    </div>;
  }
  const recent = evidence.window_days === 7 ? evidence.clicks_recent_7 : evidence.clicks_recent_30;
  if ((suggestion.rule_id === 'G03' || suggestion.rule_id === 'G04') && typeof evidence.window_days === 'number' && typeof recent === 'number') {
    return <div className="flex flex-col justify-center rounded-xl border border-sky-500/30 bg-sky-500/10 p-4">
      <span className="text-xs text-sky-200">Lượt hoạt động trên hệ thống</span>
      <strong className="mt-2 text-3xl tabular-nums text-white">{recent}</strong>
      <span className="mt-2 text-xs text-slate-300">Trong {evidence.window_days} ngày cuối tại mốc đánh giá</span>
    </div>;
  }
  return <div className="flex flex-col justify-center rounded-xl border border-slate-700 bg-slate-800/50 p-4">
    <span className="text-xs text-slate-300">Dấu hiệu cần đối chiếu</span>
    <strong className="mt-2 text-sm text-white">{suggestion.title}</strong>
  </div>;
};

const Metric: React.FC<{ label: string; value: string; note: string }> = ({ label, value, note }) => (
  <div className="rounded-xl border border-slate-700 bg-slate-950/50 p-3">
    <p className="text-xs text-slate-400">{label}</p>
    <strong className="mt-1 block text-lg text-white">{value}</strong>
    <p className="text-[11px] text-slate-500">{note}</p>
  </div>
);