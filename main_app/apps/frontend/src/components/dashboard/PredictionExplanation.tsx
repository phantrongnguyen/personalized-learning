import React from 'react';
import { ArrowDownRight, ArrowUpRight, BrainCircuit, Info } from 'lucide-react';
import { FIELDS } from '@shared/constants';
import { FeatureContribution, PredictionResponse, StudentFeatures } from '@shared/types';

const fixedContext: (keyof StudentFeatures)[] = [
  'code_module', 'gender', 'highest_education', 'age_band', 'studied_credits', 'date_registration',
];

export function formatFeatureValue(item: FeatureContribution): string {
  if (typeof item.value === 'string') return item.value;
  if (item.feature === 'submission_rate' || item.feature === 'active_day_ratio') {
    return `${(item.value * 100).toLocaleString('vi-VN', { maximumFractionDigits: 1 })}%`;
  }
  return item.value.toLocaleString('vi-VN', { maximumFractionDigits: 2 });
}

export const PredictionExplanation: React.FC<{ result: PredictionResponse }> = ({ result }) => {
  const explanation = result.explanation;
  if (!explanation) {
    return (
      <div className="rounded-2xl border border-amber-500/30 bg-amber-500/10 p-5 text-sm text-amber-200" role="status">
        API chưa cung cấp dữ liệu giải thích. Không thể xác định yếu tố chi phối chỉ từ xác suất tổng.
      </div>
    );
  }

  const increasing = explanation.contributions.filter(item => item.direction === 'increase');
  const decreasing = explanation.contributions.filter(item => item.direction === 'decrease');
  const largest = Math.max(...explanation.contributions.map(item => Math.abs(item.contribution)), 0.001);
  const percent = (value: number) => `${(value * 100).toFixed(1)}%`;
  const signed = (value: number) => `${value > 0 ? '+' : ''}${value.toFixed(3)}`;
  const labelFor = (item: FeatureContribution) => FIELDS.find(field => field.key === item.feature)?.label ?? item.feature;
  const difference = (result.confidence - explanation.baseline_probability) * 100;

  const renderContribution = (item: FeatureContribution) => {
    const positive = item.direction === 'increase';
    return (
      <div key={item.feature} className="min-w-0 rounded-xl border border-slate-800 bg-slate-950/60 p-4">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <div className="min-w-0 flex-1 basis-40">
            <p className="break-words text-sm font-semibold text-slate-100">{labelFor(item)}</p>
            <p className="mt-1 text-xs text-slate-400">Giá trị đã phân tích: <strong className="text-slate-200">{formatFeatureValue(item)}</strong></p>
          </div>
          <span className={`shrink-0 rounded-lg px-2 py-1 text-xs font-mono ${positive ? 'bg-rose-500/10 text-rose-300' : 'bg-emerald-500/10 text-emerald-300'}`}>
            {signed(item.contribution)} log-odds
          </span>
        </div>
        <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-slate-800" aria-hidden="true">
          <div className={`h-full rounded-full ${positive ? 'bg-rose-400' : 'bg-emerald-400'}`} style={{ width: `${Math.max(1, Math.abs(item.contribution) / largest * 100)}%` }} />
        </div>
        <p className="mt-2 text-[11px] leading-relaxed text-slate-500">
          {fixedContext.includes(item.feature) ? 'Yếu tố bối cảnh — không dùng làm mục tiêu thay đổi cá nhân.' : 'Chỉ số hành vi — cần đối chiếu thực tế trước khi can thiệp.'}
        </p>
      </div>
    );
  };

  return (
    <section aria-labelledby="explanation-heading" className="min-w-0 rounded-2xl border border-slate-800 bg-slate-900/90 p-5 shadow-xl sm:p-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex min-w-0 items-start gap-3">
          <div className="shrink-0 rounded-xl bg-sky-500/10 p-2 text-sky-400"><BrainCircuit className="h-5 w-5" /></div>
          <div className="min-w-0">
            <h2 id="explanation-heading" className="text-lg font-bold text-foreground">Vì sao mô hình đưa ra xác suất này?</h2>
            <p className="mt-1 text-xs leading-relaxed text-slate-400">Đóng góp riêng của từng biến trong hồ sơ vừa phân tích, không phải mức quan trọng chung của mô hình.</p>
          </div>
        </div>
        <span className="rounded-full border border-sky-500/20 bg-sky-500/10 px-3 py-1 text-[11px] font-medium text-sky-300">{explanation.method} · {explanation.contributions.length} biến gốc</span>
      </div>

      <div className="mt-5 grid gap-3 sm:grid-cols-3">
        <div className="rounded-xl border border-slate-800 bg-slate-950/50 p-4">
          <p className="text-xs text-slate-400">Mức nền quy đổi của mô hình</p>
          <p className="mt-2 text-2xl font-bold text-slate-200">{percent(explanation.baseline_probability)}</p>
          <p className="mt-1 text-[11px] text-slate-500">Mốc tham chiếu SHAP, không phải tỷ lệ trượt thực tế.</p>
        </div>
        <div className="rounded-xl border border-slate-800 bg-slate-950/50 p-4">
          <p className="text-xs text-slate-400">Chênh lệch tổng so với mức nền</p>
          <p className={`mt-2 text-2xl font-bold ${difference >= 0 ? 'text-rose-300' : 'text-emerald-300'}`}>{difference >= 0 ? '+' : ''}{difference.toFixed(1)} <span className="text-xs font-normal">điểm %</span></p>
          <p className="mt-1 text-[11px] text-slate-500">Chênh lệch của toàn hồ sơ, không chia % tùy ý cho từng biến.</p>
        </div>
        <div className="rounded-xl border border-sky-500/20 bg-sky-500/5 p-4">
          <p className="text-xs text-sky-200">Xác suất sau khi xét hồ sơ</p>
          <p className="mt-2 text-2xl font-bold text-foreground">{percent(result.confidence)}</p>
          <p className="mt-1 text-[11px] text-slate-500">{result.threshold !== undefined ? `Ngưỡng phân lớp: ${percent(result.threshold)}` : 'Theo ngưỡng phân lớp của mô hình'}</p>
        </div>
      </div>

      <div className="mt-6 grid gap-5 md:grid-cols-2">
        <div className="min-w-0">
          <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-rose-300"><ArrowUpRight className="h-4 w-4" />Yếu tố làm tăng nguy cơ</h3>
          <div className="space-y-3">{increasing.length ? increasing.slice(0, 3).map(renderContribution) : <p className="text-xs text-slate-400">Không có đóng góp tăng đáng kể trong hồ sơ này.</p>}</div>
        </div>
        <div className="min-w-0">
          <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-emerald-300"><ArrowDownRight className="h-4 w-4" />Yếu tố làm giảm nguy cơ</h3>
          <div className="space-y-3">{decreasing.length ? decreasing.slice(0, 3).map(renderContribution) : <p className="text-xs text-slate-400">Không có đóng góp giảm đáng kể trong hồ sơ này.</p>}</div>
        </div>
      </div>

      <div className="mt-5 flex items-start gap-2 rounded-xl border border-sky-500/15 bg-sky-500/5 p-4 text-xs leading-relaxed text-slate-300">
        <Info className="mt-0.5 h-4 w-4 shrink-0 text-sky-400" />
        <p>Dấu +/− thể hiện tăng/giảm so với mốc tham chiếu của mô hình. Giá trị SHAP ở thang log-odds, không phải điểm phần trăm. Đây là giải thích dự đoán nguy cơ trượt/bỏ học, không chứng minh nguyên nhân thực tế hay kết luận về năng lực. Một chỉ số xấu vẫn có thể có đóng góp giảm trong hồ sơ cụ thể; không vì vậy mà nên làm xấu chỉ số đó.</p>
      </div>

      <details className="mt-4 rounded-xl border border-slate-800 p-4">
        <summary className="cursor-pointer text-sm font-semibold text-slate-300">Xem đầy đủ {explanation.contributions.length} biến và kiểm tra tổng đóng góp</summary>
        <div className="mt-4 space-y-2">
          {explanation.contributions.map(item => (
            <div key={item.feature} className="flex flex-wrap items-start justify-between gap-2 border-b border-slate-800/60 py-2 text-xs">
              <span className="min-w-0 flex-1 basis-44 break-words text-slate-300">{labelFor(item)} <span className="text-slate-500">· {formatFeatureValue(item)}</span></span>
              <span className={`font-mono ${item.direction === 'increase' ? 'text-rose-300' : item.direction === 'decrease' ? 'text-emerald-300' : 'text-slate-500'}`}>{signed(item.contribution)} · {item.direction === 'increase' ? 'Tăng' : item.direction === 'decrease' ? 'Giảm' : 'Trung tính'}</span>
            </div>
          ))}
          <p className="pt-3 break-words text-xs leading-relaxed text-slate-400">Mức nền {explanation.baseline_raw_score.toFixed(3)} + tổng đóng góp = {explanation.raw_score.toFixed(3)} log-odds → {percent(explanation.reconstructed_probability)}. Các biến mã hóa đã được gộp về biến gốc; số hiển thị được làm tròn.</p>
        </div>
      </details>
    </section>
  );
};
