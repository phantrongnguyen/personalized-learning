import React, { useState } from 'react';
import { modelEvaluation } from '../../data/modelEvaluation';
import { ZoomableChart } from './ZoomableChart';

type Evaluation = typeof modelEvaluation[number];
type Model = Evaluation['model'];
type Method = Evaluation['method'];
const models: Model[] = ['LightGBM', 'XGBoost', 'CatBoost'];
const methods: Method[] = ['Full features', 'HCO', 'VNLS', 'HCO-VNLS'];
const colors: Record<Model, string> = { LightGBM: 'var(--chart-lightgbm)', XGBoost: 'var(--chart-xgboost)', CatBoost: 'var(--chart-catboost)' };
const label = (method: Method) => method === 'Full features' ? 'Đủ đặc trưng' : method;
const pct = (value: number) => `${(value * 100).toLocaleString('vi-VN', { maximumFractionDigits: 2 })}%`;
const number = (value: number) => value.toLocaleString('vi-VN');
const decimal = (value: number) => value.toLocaleString('vi-VN', { minimumFractionDigits: 6, maximumFractionDigits: 6 });
const controlClass = 'w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500';
const metrics = [
  { key: 'accuracy', name: 'Accuracy' },
  { key: 'precision_risk', name: 'Precision' },
  { key: 'recall_risk', name: 'Recall' },
  { key: 'f1_risk', name: 'F1 nguy cơ' },
] as const;

const Legend = () => <div className="flex flex-wrap gap-x-5 gap-y-2 text-xs text-slate-300">
  {models.map(model => <span key={model} className="inline-flex items-center gap-2">
    <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: colors[model] }} />{model}
  </span>)}
</div>;

export const EvaluationCharts: React.FC<{ cutoff: number }> = ({ cutoff }) => {
  const [model, setModel] = useState<Model>('LightGBM');
  const [method, setMethod] = useState<Method>('HCO-VNLS');
  const [cutoffMetric, setCutoffMetric] = useState<'average_precision_risk' | 'recall_risk'>('average_precision_risk');
  const rows = modelEvaluation.filter(row => row.cutoff === cutoff);
  const selected = rows.find(row => row.model === model && row.method === method)!;
  const comparison = rows.filter(row => row.method === method);
  const activeMetricName = cutoffMetric === 'average_precision_risk' ? 'AP' : 'Recall nguy cơ';
  const selectPoint = (row: Evaluation) => { setModel(row.model); setMethod(row.method); };

  return <section className="evaluation-charts space-y-5" aria-labelledby="evaluation-charts-heading">
    <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-4">
      <div>
        <h3 id="evaluation-charts-heading" className="text-lg font-bold text-white">Khám phá kết quả bằng biểu đồ</h3>
        <p className="text-xs text-slate-400 mt-2 leading-relaxed">Cutoff {pct(cutoff)} · Chọn phương pháp để so sánh ba bộ học. Chọn điểm trên biểu đồ AP để xem ma trận tương ứng.</p>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 lg:min-w-[360px]">
        <label className="text-xs text-slate-300 space-y-2"><span className="block">Phương pháp chọn đặc trưng</span>
          <select className={controlClass} value={method} onChange={event => setMethod(event.target.value as Method)}>
            {methods.map(value => <option key={value} value={value}>{label(value)}</option>)}
          </select>
        </label>
        <label className="text-xs text-slate-300 space-y-2"><span className="block">Bộ học xem chi tiết</span>
          <select className={controlClass} value={model} onChange={event => setModel(event.target.value as Model)}>
            {models.map(value => <option key={value}>{value}</option>)}
          </select>
        </label>
      </div>
    </div>

    <div className="grid grid-cols-1 xl:grid-cols-2 gap-5">
      <ZoomableChart title="So sánh chất lượng phân loại">
        <h4 className="text-sm font-bold text-white mb-1">So sánh chất lượng phân loại</h4>
        <p className="text-xs text-slate-400 mb-4">{label(method)} · Các cột cùng thang đo 0–100% · Ngưỡng 0,5</p>
        <Legend />
        <div className="overflow-x-auto mt-3" role="region" aria-label="Biểu đồ cột chỉ số phân loại" tabIndex={0}>
          <svg viewBox="0 0 560 320" className="w-full min-w-[460px]" role="img" aria-label={`Accuracy, Precision, Recall và F1 của ba bộ học, ${label(method)}, cutoff ${pct(cutoff)}`}>
            <title>So sánh chỉ số phân loại trên validation</title>
            {[0, .2, .4, .6, .8, 1].map(tick => <g key={tick}>
              <line x1="48" x2="540" y1={250 - tick * 200} y2={250 - tick * 200} stroke="var(--border-subtle)" strokeDasharray="3 4" />
              <text x="40" y={254 - tick * 200} textAnchor="end" fill="var(--text-secondary)" fontSize="11">{tick * 100}%</text>
            </g>)}
            {metrics.map((metric, group) => <g key={metric.key}>
              {comparison.map((row, index) => {
                const value = row[metric.key]; const x = 65 + group * 122 + index * 29;
                return <g key={row.model}>
                  <rect x={x} y={250 - value * 200} width="22" height={value * 200} rx="3" fill={colors[row.model]}>
                    <title>{`${row.model} · ${metric.name}: ${pct(value)}`}</title>
                  </rect>
                  <text x={x + 11} y={242 - value * 200} textAnchor="middle" fill="var(--text-secondary)" fontSize="10">{(value * 100).toFixed(1)}</text>
                </g>;
              })}
              <text x={105 + group * 122} y="275" textAnchor="middle" fill="var(--text-secondary)" fontSize="12">{metric.name}</text>
            </g>)}
          </svg>
        </div>
      </ZoomableChart>

      <ZoomableChart title="Số đặc trưng và Average Precision">
        <h4 className="text-sm font-bold text-white mb-1">Số đặc trưng và Average Precision</h4>
        <p className="text-xs text-slate-400 mb-4">12 cấu hình tại cutoff {pct(cutoff)} · Trục AP phóng đại từ 0,80 đến 0,92</p>
        <Legend />
        <div className="overflow-x-auto mt-3" role="region" aria-label="Chọn cấu hình trên biểu đồ phân tán" tabIndex={0}>
          <svg viewBox="0 0 560 320" className="w-full min-w-[460px]" role="group" aria-label="Biểu đồ phân tán số đặc trưng và AP; các điểm là nút chọn cấu hình">
            <title>Đánh đổi số đặc trưng và AP</title>
            {[.80, .82, .84, .86, .88, .90, .92].map(tick => <g key={tick}>
              <line x1="60" x2="530" y1={250 - (tick - .8) / .12 * 200} y2={250 - (tick - .8) / .12 * 200} stroke="var(--border-subtle)" strokeDasharray="3 4" />
              <text x="50" y={254 - (tick - .8) / .12 * 200} fill="var(--text-secondary)" textAnchor="end" fontSize="11">{tick.toFixed(2)}</text>
            </g>)}
            {[0, 10, 20, 30, 40].map(tick => <g key={tick}>
              <text x={60 + tick / 40 * 470} y="273" fill="var(--text-secondary)" textAnchor="middle" fontSize="11">{tick}</text>
            </g>)}
            <text x="295" y="302" fill="var(--text-secondary)" textAnchor="middle" fontSize="12">Số đặc trưng gốc trước mã hóa</text>
            <text x="20" y="35" fill="var(--text-secondary)" fontSize="12">AP</text>
            {rows.filter(row => row !== selected).concat([selected]).map(row => {
              const active = row.model === model && row.method === method;
              const cx = 60 + row.features / 40 * 470; const cy = 250 - (row.average_precision_risk - .8) / .12 * 200;
              const description = `${row.model}, ${label(row.method)}, ${row.features} cột, AP ${decimal(row.average_precision_risk)}`;
              return <g key={`${row.model}-${row.method}`} role="button" tabIndex={0} aria-label={description} aria-pressed={active}
                onClick={() => selectPoint(row)} onKeyDown={event => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); selectPoint(row); } }}
                className="evaluation-chart-point cursor-pointer">
                <title>{description}</title>
                <circle cx={cx} cy={cy} r={active ? 9 : 6} fill={colors[row.model]} fillOpacity={active ? 1 : .85} stroke={active ? 'var(--text-primary)' : colors[row.model]} strokeWidth={active ? 2.5 : 1} />
                {active && <text x={cx} y={cy - 16} textAnchor={cx > 440 ? 'end' : 'middle'} fill="var(--text-primary)" fontSize="11" fontWeight="bold">{row.features} cột · {decimal(row.average_precision_risk)}</text>}
              </g>;
            })}
          </svg>
        </div>
        <p className="text-xs text-slate-300" aria-live="polite">Đang chọn: {model} · {label(method)} · {selected.features} cột · AP {decimal(selected.average_precision_risk)}.</p>
        <p className="text-xs text-slate-400 mt-2">Một số điểm ở gần nhau; có thể dùng bộ chọn phía trên hoặc phím Tab và Enter để chọn chính xác.</p>
      </ZoomableChart>

      <ZoomableChart title="Ma trận nhầm lẫn">
        <h4 className="text-sm font-bold text-white mb-1">Ma trận nhầm lẫn</h4>
        <p className="text-xs text-slate-400 mb-4">{model} · {label(method)} · Cutoff {pct(cutoff)} · Ngưỡng 0,5</p>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[310px] border-separate border-spacing-2 text-center">
            <caption className="text-xs text-slate-400 text-left mb-2">Hàng: nhãn thực tế · Cột: nhãn dự báo</caption>
            <thead><tr><th scope="col" className="text-xs text-slate-400">Thực tế / Dự báo</th><th scope="col" className="text-xs text-slate-300 py-2">Không nguy cơ</th><th scope="col" className="text-xs text-slate-300 py-2">Nguy cơ</th></tr></thead>
            <tbody>{[
              { label: 'Không nguy cơ', cells: [{ code: 'TN', value: selected.tn, good: true, text: 'Nhận đúng' }, { code: 'FP', value: selected.fp, good: false, text: 'Cảnh báo nhầm' }] },
              { label: 'Nguy cơ', cells: [{ code: 'FN', value: selected.fn, good: false, text: 'Bỏ sót' }, { code: 'TP', value: selected.tp, good: true, text: 'Phát hiện đúng' }] },
            ].map(row => <tr key={row.label}>
              <th scope="row" className="text-xs text-slate-300 font-medium">{row.label}</th>
              {row.cells.map(cell => <td key={cell.code} className={`rounded-xl border p-3 ${cell.good ? 'evaluation-matrix-good' : 'evaluation-matrix-error'}`}
                style={{ backgroundColor: cell.good ? `rgba(var(--chart-good-rgb),${.35 + cell.value / selected.n * .5})` : `rgba(var(--chart-error-rgb),${.35 + cell.value / selected.n * .5})` }}>
                <div className="text-[11px]">{cell.code} · {cell.text}</div>
                <div className="text-2xl font-bold font-mono my-1">{number(cell.value)}</div>
                <div className="text-[11px]">{pct(cell.value / selected.n)} tổng mẫu</div>
              </td>)}
            </tr>)}</tbody>
          </table>
        </div>
        <p className="text-xs text-slate-300 mt-4 leading-relaxed" aria-live="polite">
          {number(selected.n)} lượt đăng ký · {number(selected.alerts)} cảnh báo · Bỏ sót {number(selected.fn)}/{number(selected.fn + selected.tp)} trường hợp nguy cơ ({pct(selected.fn / (selected.fn + selected.tp))}).
        </p>
        <p className="text-xs text-slate-400 mt-2">Màu thể hiện loại kết quả và tỷ lệ trên tổng mẫu. Số lượt đăng ký không tương đương số sinh viên duy nhất.</p>
      </ZoomableChart>

      <ZoomableChart title="So sánh hai mốc quan sát">
        <div className="flex flex-col sm:flex-row justify-between gap-3 mb-4">
          <div><h4 className="text-sm font-bold text-white mb-1">So sánh hai mốc quan sát</h4><p className="text-xs text-slate-400">{label(method)} · Cùng thang đo 0–1</p></div>
          <label className="text-xs text-slate-300 space-y-1"><span className="block">Chỉ số so sánh</span>
            <select value={cutoffMetric} onChange={event => setCutoffMetric(event.target.value as typeof cutoffMetric)} className={controlClass}>
              <option value="average_precision_risk">Average Precision</option><option value="recall_risk">Recall nguy cơ</option>
            </select>
          </label>
        </div>
        <div className="flex flex-wrap gap-4 text-xs text-slate-300 mb-2"><span>▧ Cutoff 50% (màu nhạt)</span><span>■ Cutoff 75% (màu đậm)</span></div>
        <div className="overflow-x-auto" role="region" aria-label="Biểu đồ so sánh cutoff 50 và 75 phần trăm" tabIndex={0}>
          <svg viewBox="0 0 560 320" className="w-full min-w-[460px]" role="img" aria-label={`${activeMetricName} của ba bộ học tại cutoff 50% và 75%, ${label(method)}`}>
            <title>{`So sánh ${activeMetricName} theo cutoff`}</title>
            {[0, .2, .4, .6, .8, 1].map(tick => <g key={tick}><line x1="48" x2="540" y1={250 - tick * 200} y2={250 - tick * 200} stroke="var(--border-subtle)" strokeDasharray="3 4" /><text x="40" y={254 - tick * 200} textAnchor="end" fill="var(--text-secondary)" fontSize="11">{tick.toFixed(1)}</text></g>)}
            {models.map((name, group) => <g key={name}>
              {[.5, .75].map((fraction, index) => {
                const row = modelEvaluation.find(value => value.cutoff === fraction && value.model === name && value.method === method)!;
                const value = row[cutoffMetric]; const x = 90 + group * 160 + index * 39;
                return <g key={fraction}><rect x={x} y={250 - value * 200} width="30" height={value * 200} rx="3" fill={colors[name]} fillOpacity={index === 0 ? .6 : 1}><title>{`${name} · Cutoff ${pct(fraction)} · ${activeMetricName}: ${decimal(value)}`}</title></rect>
                  <text x={x + 15} y={241 - value * 200} textAnchor="middle" fill="var(--text-secondary)" fontSize="11">{value.toFixed(3)}</text>
                  <text x={x + 15} y="269" textAnchor="middle" fill="var(--text-secondary)" fontSize="10">{pct(fraction)}</text>
                </g>;
              })}
              <text x={124 + group * 160} y="295" textAnchor="middle" fill="var(--text-secondary)" fontSize="12">{name}</text>
            </g>)}
          </svg>
        </div>
        <p className="text-xs text-slate-400 leading-relaxed">Validation 50% có 3.638 lượt đăng ký, 75% có 3.415. Quần thể và tỷ lệ nguy cơ thay đổi; chênh lệch không đo riêng lợi ích của việc quan sát thêm thời gian.</p>
      </ZoomableChart>
    </div>
  </section>;
};
