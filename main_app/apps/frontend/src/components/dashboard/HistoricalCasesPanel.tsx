import React, { useEffect, useRef, useState } from 'react';
import { BookOpenCheck, ChevronDown, Info, Loader2, UsersRound } from 'lucide-react';
import { FIELDS } from '@shared/constants';
import { HistoricalCase, HistoricalCasesResponse, PredictionResponse, StudentFeatures } from '@shared/types';
import { compareHistoricalCases } from '../../services/api';
import { useApp } from '../../state/AppContext';

const number = (value: number) => value.toLocaleString('vi-VN', { maximumFractionDigits: 1 });
const percent = (value: number) => number(value * 100) + '%';
const featureLabel = (key: keyof StudentFeatures) => FIELDS.find(field => field.key === key)?.label ?? key;
const featureValue = (key: keyof StudentFeatures, value: number) => ['active_day_ratio', 'submission_rate'].includes(key) ? percent(value) : number(value);
const change = (difference: number, unit: string) => Math.abs(difference) < 0.00001 ? 'Không đổi' : (difference > 0 ? 'Tăng ' : 'Giảm ') + number(Math.abs(difference)) + ' ' + unit;

const HistoricalCaseCard: React.FC<{ item: HistoricalCase }> = ({ item }) => {
  const first = item.snapshots[0];
  const last = item.snapshots[item.snapshots.length - 1];
  return (
    <details className="group min-w-0 rounded-xl border border-slate-800 bg-slate-950/40">
      <summary className="history-inset flex cursor-pointer list-none flex-wrap items-start justify-between gap-3 p-4 focus-visible:outline focus-visible:outline-2 focus-visible:outline-brand-400">
        <span className="min-w-0 flex-1 basis-48">
          <span className="block break-all text-sm font-semibold text-foreground">{item.case_id}</span>
          <span className="mt-1 block text-xs text-slate-400">Học phần {item.module} · Đợt {item.presentation}</span>
          <span className="mt-2 block text-xs leading-relaxed text-slate-300">Model chấm nguy cơ {percent(item.risk_probability)} tại mốc 75%</span>
          <span className="mt-1 block text-[11px] leading-relaxed text-slate-500">Khoảng cách đối chiếu {item.distance.toFixed(3)} · thấp hơn là gần hơn, không phải xác suất</span>
        </span>
        <span className="history-case-status flex min-w-0 max-w-full items-center gap-2">
          <span className="rounded-lg border border-emerald-500/20 bg-emerald-500/10 px-2 py-1 text-xs font-semibold text-emerald-300">{item.final_result === 'Distinction' ? 'Đạt xuất sắc' : 'Đạt cuối kỳ'}</span>
          <ChevronDown className="h-4 w-4 text-slate-400 transition-transform group-open:rotate-180" aria-hidden="true" />
        </span>
        <span className="block w-full text-xs font-medium text-brand-300 group-open:hidden">Mở hồ sơ: điểm giống nhau và diễn biến thực tế</span>
        <span className="hidden w-full text-xs font-medium text-brand-300 group-open:block">Thu gọn hồ sơ đối chiếu</span>
      </summary>
      <div className="history-inset space-y-5 border-t border-slate-800 p-4 sm:p-5">
        <div>
          <h4 className="text-sm font-semibold text-slate-200">Vì sao chọn hồ sơ này?</h4>
          <p className="mt-1 text-xs leading-relaxed text-slate-400">Đối chiếu các yếu tố hành vi làm tăng nguy cơ của bạn, cùng học phần và cùng mốc. Không ghép chỉ vì cùng xác suất.</p>
          <dl className="mt-3 space-y-3">
            {item.matching_features.map(feature => (
              <div key={feature.feature} className="history-inset rounded-lg border border-slate-800 p-3">
                <dt className="break-words text-xs font-semibold text-slate-200">{featureLabel(feature.feature)}</dt>
                <dd className="history-matching-grid mt-2 grid grid-cols-1 gap-2 text-xs">
                  <span className="min-w-0 break-words text-slate-400">Bạn tại mốc 75%: <strong className="text-slate-100">{featureValue(feature.feature, feature.current_value)}</strong><span className="mt-1 block text-[11px]">SHAP {feature.current_contribution > 0 ? '+' : ''}{feature.current_contribution.toFixed(3)} log-odds</span></span>
                  <span className="min-w-0 break-words text-slate-400">Hồ sơ này tại mốc 75%: <strong className="text-slate-100">{featureValue(feature.feature, feature.historical_value)}</strong><span className="mt-1 block text-[11px]">SHAP {feature.historical_contribution > 0 ? '+' : ''}{feature.historical_contribution.toFixed(3)} log-odds</span></span>
                </dd>
              </div>
            ))}
          </dl>
        </div>
        <div>
          <h4 className="text-sm font-semibold text-slate-200">Sau mốc dự báo, điều gì đã được ghi nhận?</h4>
          <p className="mt-1 text-xs leading-relaxed text-slate-400">Đây là nhật ký theo thời gian, không phải nguy cơ được chấm lại bằng model ở cuối kỳ.</p>
          <div className="history-snapshots mt-3 grid grid-cols-1 gap-3">
            {item.snapshots.map(snapshot => (
              <div key={snapshot.fraction} className="history-inset min-w-0 rounded-xl border border-slate-800 bg-slate-900/60 p-3">
                <p className="text-xs font-bold text-brand-300">{snapshot.fraction === 0.75 ? 'Lúc dự báo · 75%' : snapshot.fraction === 1 ? 'Cuối học phần · 100%' : 'Theo dõi · 85%'}</p>
                <p className="mt-1 text-[11px] text-slate-500">Ngày {snapshot.day} từ đầu học phần</p>
                <dl className="mt-3 space-y-3 text-xs">
                  <div><dt className="text-slate-400">Ngày có hoạt động / 30 ngày</dt><dd className="mt-1 break-words font-semibold text-slate-100">{number(snapshot.recent_active_days)} / 30</dd></div>
                  <div><dt className="text-slate-400">Lượt tương tác / 30 ngày</dt><dd className="mt-1 break-words font-semibold text-slate-100">{number(snapshot.recent_clicks)}</dd></div>
                  <div><dt className="text-slate-400">Bài đến hạn đã nộp</dt><dd className="mt-1 break-words font-semibold text-slate-100">{number(snapshot.due_assessments_submitted)} / {number(snapshot.due_assessments)}{snapshot.due_submission_rate !== null && <span> · {percent(snapshot.due_submission_rate)}</span>}</dd></div>
                </dl>
              </div>
            ))}
          </div>
          <p className="mt-2 text-[11px] leading-relaxed text-slate-500">Cửa sổ hoạt động luôn là 30 ngày trước từng mốc. Tỷ lệ bài chỉ xét bài có hạn nộp đã biết và đã đến hạn; số bài đến hạn thay đổi theo thời gian, không suy ra điểm thi.</p>
        </div>
        <div className="history-inset rounded-xl border border-brand-500/20 bg-brand-500/5 p-4">
          <h4 className="text-xs font-semibold text-brand-300">Đối chiếu mốc 75% với cuối học phần</h4>
          <ul className="mt-2 space-y-2 text-xs leading-relaxed text-slate-300">
            <li>Ngày có hoạt động trong cửa sổ 30 ngày: {change(last.recent_active_days - first.recent_active_days, 'ngày')}.</li>
            <li>Lượt tương tác trong cửa sổ 30 ngày: {change(last.recent_clicks - first.recent_clicks, 'lượt')}.</li>
            <li>Tỷ lệ bài đến hạn đã nộp: {first.due_submission_rate !== null && last.due_submission_rate !== null ? change((last.due_submission_rate - first.due_submission_rate) * 100, 'điểm %') : 'Chưa đủ bài có hạn nộp để so sánh'}.</li>
          </ul>
          <p className="mt-3 text-xs leading-relaxed text-slate-400">Dùng các điểm giống nhau để trao đổi về trở ngại thực tế và cách hỗ trợ phù hợp. Hồ sơ vẫn có thể đạt dù tương tác giảm; không biến các mức cuối kỳ thành chỉ tiêu bắt buộc hay kết luận tăng click là học tốt hơn.</p>
        </div>
      </div>
    </details>
  );
};

interface HistoricalCasesPanelProps {
  features: StudentFeatures;
  prediction: PredictionResponse;
  busy: boolean;
}

export const HistoricalCasesPanel: React.FC<HistoricalCasesPanelProps> = ({ features, prediction, busy }) => {
  const { apiBase } = useApp();
  const [confirmed, setConfirmed] = useState(false);
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<HistoricalCasesResponse | null>(null);
  const [error, setError] = useState('');
  const pending = useRef<AbortController | null>(null);

  useEffect(() => {
    pending.current?.abort();
    setData(null);
    setError('');
    setLoading(false);
    setConfirmed(false);
    return () => { pending.current?.abort(); };
  }, [features, prediction, apiBase]);

  const handleCompare = async () => {
    if (!confirmed || loading || busy) return;
    pending.current?.abort();
    const controller = new AbortController();
    pending.current = controller;
    setLoading(true);
    setData(null);
    setError('');
    try {
      const response = await compareHistoricalCases(apiBase, features, controller.signal);
      if (!controller.signal.aborted) setData(response);
    } catch (failure) {
      if (!controller.signal.aborted) setError(failure instanceof Error && failure.name !== 'AbortError' ? failure.message : 'Đối chiếu quá thời gian hoặc mất kết nối. Bạn có thể thử lại; kết quả dự đoán vẫn được giữ.');
    } finally {
      if (!controller.signal.aborted) setLoading(false);
    }
  };

  return (
    <section aria-labelledby="historical-cases-heading" className="historical-cases-panel min-w-0 rounded-2xl border border-slate-800 bg-slate-900/90 shadow-xl">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="history-heading flex min-w-0 flex-1 basis-64 items-start gap-3">
          <span className="shrink-0 rounded-xl bg-brand-500/10 p-2 text-brand-400"><BookOpenCheck className="h-5 w-5" aria-hidden="true" /></span>
          <div className="min-w-0"><h2 id="historical-cases-heading" className="text-lg font-bold text-foreground">Hồ sơ tương tự đã vượt qua nguy cơ</h2><p className="mt-1 text-xs leading-relaxed text-slate-400">Không chỉ biết vì sao có nguy cơ: xem những trường hợp gần bạn đã diễn biến thế nào và đạt kết quả gì.</p></div>
        </div>
        <span className="rounded-full border border-brand-500/20 bg-brand-500/10 px-3 py-1 text-[11px] font-medium text-brand-300">Đối chiếu hồi cứu · OULAD</span>
      </div>
      <div className="history-inset mt-5 rounded-xl border border-slate-800 bg-slate-950/40 p-4">
        <label className="history-confirmation flex cursor-pointer items-start gap-3 text-xs leading-relaxed text-slate-300">
          <input type="checkbox" checked={confirmed} disabled={loading || busy} onChange={event => { setConfirmed(event.target.checked); setData(null); setError(''); }} className="mt-0.5 h-4 w-4 shrink-0 accent-blue-600" />
          <span>Hồ sơ vừa phân tích phản ánh <strong className="text-slate-100">mốc 75% thời lượng học phần</strong>. Chỉ so sánh cùng mốc; chưa hỗ trợ hồ sơ ở tuần đầu hoặc mốc khác.</span>
        </label>
        <button type="button" onClick={handleCompare} disabled={!confirmed || loading || busy} className="history-search mt-4 inline-flex min-h-11 max-w-full items-center justify-center gap-2 rounded-xl bg-brand-600 px-4 py-2.5 text-xs font-semibold text-white transition-colors hover:bg-brand-500 disabled:cursor-not-allowed disabled:opacity-50">
          {loading ? <Loader2 className="h-4 w-4 shrink-0 animate-spin" aria-hidden="true" /> : <UsersRound className="h-4 w-4 shrink-0" aria-hidden="true" />}
          <span className="min-w-0 break-words">{loading ? 'Đang tìm hồ sơ gần nhất...' : 'Tìm trường hợp đối chiếu'}</span>
        </button>
        <p className="mt-2 text-[11px] leading-relaxed text-slate-500">Dùng bản hồ sơ đã phân tích, không tự lấy các giá trị đang sửa trên form. Xét hành vi và lý do SHAP, không đối chiếu trực tiếp tuổi/giới tính.</p>
      </div>
      <div aria-live="polite" aria-atomic="true" className="mt-4">
        {loading && <p className="text-xs text-slate-400">Đang đối chiếu thư viện thật; không tạo ví dụ minh họa thay cho dữ liệu.</p>}
        {error && <p role="alert" className="history-inset rounded-xl border border-amber-500/30 bg-amber-500/10 p-4 text-xs leading-relaxed text-amber-200">{error}</p>}
        {data && <p className={'history-inset rounded-xl border p-4 text-xs leading-relaxed ' + (data.status === 'available' ? 'border-brand-500/20 bg-brand-500/5 text-slate-300' : 'border-amber-500/30 bg-amber-500/10 text-amber-200')}>{data.message}</p>}
      </div>
      {data && data.neighborhood_count > 0 && (
        <div className="mt-5">
          <div className="history-counts grid grid-cols-1 gap-3">
            {[['Hồ sơ gần nhất', data.neighborhood_count, 'text-slate-100'], ['Đạt / đạt xuất sắc', data.successful_count, 'text-emerald-300'], ['Không đạt / rút lui', data.unsuccessful_count, 'text-rose-300']].map(([label, value, color]) => (
              <div key={String(label)} className="history-inset min-w-0 rounded-xl border border-slate-800 bg-slate-950/50 p-4"><p className="text-xs leading-relaxed text-slate-400">{label}</p><p className={'mt-2 text-2xl font-bold ' + color}>{value}</p></div>
            ))}
          </div>
          <p className="mt-2 text-[11px] leading-relaxed text-slate-500">Ghép hồ sơ trước khi xem kết quả cuối kỳ; có cả trường hợp không vượt qua, không chỉ chọn chuyện thành công. Đây là số đếm trong nhóm tham chiếu, không phải xác suất bạn sẽ đạt.</p>
        </div>
      )}
      {data && data.cases.length > 0 && <div className="mt-5 space-y-4"><h3 className="text-sm font-semibold text-slate-200">{data.cases.length} hồ sơ đạt gần nhất trong {data.successful_count} hồ sơ đạt của nhóm đối chiếu</h3>{data.cases.map(item => <HistoricalCaseCard key={item.case_id} item={item} />)}</div>}
      {data && (
        <details className="history-inset mt-5 rounded-xl border border-slate-800 p-4">
          <summary className="cursor-pointer text-xs font-semibold text-slate-300">Nguồn, cách đối chiếu và giới hạn</summary>
          <div className="mt-3 space-y-3 text-xs leading-relaxed text-slate-400">
            <p className="break-words">{data.source} · {number(data.reference_count)} enrollment tham chiếu tại mốc 75%.</p>
            <p>Cùng học phần, cùng nhóm nguy cơ, xác suất lệch không quá 20 điểm %, có ít nhất một yếu tố hành vi tăng nguy cơ chung trong top 3. Khoảng cách gồm 70% hành vi, 20% cấu trúc SHAP tăng và 10% chênh lệch xác suất; nhận hồ sơ có khoảng cách ≤ 0,25.</p>
            <p>Chọn tối đa 20 người gần nhất, mỗi người một hồ sơ; hiển thị tối đa 3 trường hợp đạt. Khoảng cách và ngưỡng là quy tắc đối chiếu thực nghiệm, chưa được kiểm chứng cho trường của bạn.</p>
            <ul className="list-disc space-y-2 pl-4">{data.limitations.map(limit => <li key={limit}>{limit}</li>)}</ul>
          </div>
        </details>
      )}
      <div className="mt-5 flex items-start gap-2 text-xs leading-relaxed text-slate-400"><Info className="mt-0.5 h-4 w-4 shrink-0 text-brand-400" aria-hidden="true" /><p>“Đã vượt qua nguy cơ” nghĩa là từng được model xếp nguy cơ nhưng kết quả cuối kỳ đạt. Chưa thể khẳng định đã “lật kèo” nhờ một hành động cụ thể.</p></div>
    </section>
  );
};
