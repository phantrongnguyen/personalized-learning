import React from 'react';
import { modelEvaluation } from '../../data/modelEvaluation';
import { ZoomableChart } from './ZoomableChart';

const models = ['LightGBM', 'XGBoost', 'CatBoost'] as const;
const methods = ['Full features', 'HCO', 'VNLS', 'HCO-VNLS'] as const;
const colors = { LightGBM: 'var(--chart-lightgbm)', XGBoost: 'var(--chart-xgboost)', CatBoost: 'var(--chart-catboost)' };
const score = (value: number) => value.toLocaleString('vi-VN', { minimumFractionDigits: 6, maximumFractionDigits: 6 });
const methodLabel = (value: string) => value === 'Full features' ? 'Đủ đặc trưng' : value;

export const RocAucChart: React.FC<{ cutoff: number }> = ({ cutoff }) => {
  const rows = modelEvaluation.filter(row => row.cutoff === cutoff);
  const best = rows.reduce((left, right) => left.roc_auc > right.roc_auc ? left : right);

  return <section className="evaluation-charts" aria-label="So sánh ROC-AUC">
    <ZoomableChart title="So sánh ROC-AUC giữa các cấu hình">
      <h3 className="text-lg font-bold text-white">So sánh ROC-AUC</h3>
      <p className="text-xs text-slate-400 mt-2 mb-4 leading-relaxed">
        12 cấu hình tại cutoff {(cutoff * 100).toLocaleString('vi-VN')}% · Validation lịch sử · Thang đo 0–1, cao hơn tốt hơn.
        Cột thể hiện khả năng phân biệt hai lớp trên xác suất dự báo, không phải Accuracy.
      </p>
      <div className="flex flex-wrap gap-5 text-xs text-slate-300 mb-3">
        {models.map(model => <span key={model} className="inline-flex items-center gap-2"><span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: colors[model] }} />{model}</span>)}
      </div>
      <div className="overflow-x-auto" role="region" tabIndex={0} aria-label="Biểu đồ cột ROC-AUC; cuộn ngang để xem đầy đủ">
        <svg viewBox="0 0 940 530" className="w-full min-w-[680px]" role="img" aria-label={`ROC-AUC của LightGBM, XGBoost và CatBoost theo bốn phương pháp chọn đặc trưng, cutoff ${cutoff * 100}%`}>
          <title>ROC-AUC tổng hợp theo cấu hình</title>
          <desc>Biểu đồ cột ngang dùng thang đo 0 đến 1. Giá trị chính xác của từng cấu hình được ghi bên cạnh cột và trong bảng chỉ số phía trên.</desc>
          {[0, .2, .4, .6, .8, 1].map(tick => <g key={tick}>
            <line x1={190 + tick * 640} x2={190 + tick * 640} y1="45" y2="455" stroke="var(--border-subtle)" strokeDasharray="3 4" />
            <text x={190 + tick * 640} y="30" textAnchor="middle" fill="var(--text-secondary)" fontSize="12">{tick.toLocaleString('vi-VN')}</text>
          </g>)}
          {methods.map((method, group) => <g key={method}>
            <text x="8" y={92 + group * 100} fill="var(--text-primary)" fontSize="14" fontWeight="600">{methodLabel(method)}</text>
            {models.map((model, index) => {
              const row = rows.find(value => value.model === model && value.method === method)!;
              const y = 65 + group * 100 + index * 24;
              return <g key={model}>
                <rect x="190" y={y} width={row.roc_auc * 640} height="17" rx="4" fill={colors[model]}>
                  <title>{`${model} · ${methodLabel(method)} · ROC-AUC ${score(row.roc_auc)}`}</title>
                </rect>
                <text x={198 + row.roc_auc * 640} y={y + 13} fill="var(--text-primary)" fontSize="12">{score(row.roc_auc)}</text>
              </g>;
            })}
          </g>)}
          <line x1="510" x2="510" y1="45" y2="455" stroke="var(--text-secondary)" strokeDasharray="6 5" strokeOpacity="0.7" />
          <text x="510" y="480" textAnchor="middle" fill="var(--text-secondary)" fontSize="12">Mốc tham chiếu ROC-AUC = 0,5</text>
          <text x="830" y="510" textAnchor="end" fill="var(--text-secondary)" fontSize="12">ROC-AUC</text>
        </svg>
      </div>
      <p className="text-sm text-slate-300 mt-3">
        Cao nhất tại mốc đang xem: <strong>{best.model} · {methodLabel(best.method)}</strong> với ROC-AUC <strong>{score(best.roc_auc)}</strong>.
      </p>
      <p className="text-xs text-slate-400 mt-2 leading-relaxed">
        Đây là so sánh ROC-AUC tổng hợp, không phải đường cong ROC. Chưa có nhãn và xác suất từng mẫu trong bảng báo cáo để dựng đường TPR–FPR theo ngưỡng.
        Chênh lệch nhỏ chưa chứng minh ưu thế có ý nghĩa thống kê; các bộ học có thể dùng mask và tiền xử lý khác nhau.
      </p>
    </ZoomableChart>
  </section>;
};
