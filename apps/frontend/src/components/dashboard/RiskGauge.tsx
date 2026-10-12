import React from 'react';
import { ShieldCheck, AlertTriangle } from 'lucide-react';

interface RiskGaugeProps {
  atRisk: boolean;
  probability: number;
}

export const RiskGauge: React.FC<RiskGaugeProps> = ({ atRisk, probability }) => {
  const radius = 54;
  const circumference = 2 * Math.PI * radius;
  const strokeOffset = circumference * (1 - probability);

  const percentage = (probability * 100).toFixed(1);

  return (
    <div className="flex flex-col items-center text-center p-6 bg-slate-900/90 rounded-2xl border border-slate-800 shadow-xl relative overflow-hidden">
      {/* Background glow */}
      <div
        className={`absolute -top-12 -right-12 w-40 h-40 rounded-full blur-3xl pointer-events-none ${
          atRisk ? 'bg-rose-500/15' : 'bg-brand-500/15'
        }`}
      />

      {/* Header status badge */}
      <div
        className={`inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider mb-5 ${
          atRisk
            ? 'bg-rose-500/15 text-rose-400 border border-rose-500/30'
            : 'bg-brand-500/15 text-brand-400 border border-brand-500/30'
        }`}
      >
        {atRisk ? (
          <>
            <AlertTriangle className="w-4 h-4" />
            <span>CẢNH BÁO: NGUY CƠ CAO (AT RISK)</span>
          </>
        ) : (
          <>
            <ShieldCheck className="w-4 h-4" />
            <span>AN TOÀN: TIẾN ĐỘ TỐT (ON TRACK)</span>
          </>
        )}
      </div>

      {/* SVG Circular Gauge */}
      <div className="relative w-44 h-44 mb-4">
        <svg className="w-full h-full transform -rotate-90" viewBox="0 0 128 128">
          {/* Background circle track */}
          <circle
            cx="64"
            cy="64"
            r={radius}
            className="stroke-slate-800"
            strokeWidth="10"
            fill="transparent"
          />
          {/* Animated Value circle */}
          <circle
            cx="64"
            cy="64"
            r={radius}
            className={`transition-all duration-1000 ease-out ${
              atRisk ? 'stroke-rose-500' : 'stroke-brand-400'
            }`}
            strokeWidth="10"
            strokeDasharray={circumference}
            strokeDashoffset={strokeOffset}
            strokeLinecap="round"
            fill="transparent"
          />
        </svg>

        {/* Center label in circle */}
        <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
          <span className="text-3xl font-extrabold text-white tracking-tight font-mono">
            {percentage}%
          </span>
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mt-0.5">
            Xác suất rủi ro
          </span>
        </div>
      </div>

      {/* Summary statement */}
      <p className="text-sm text-slate-300 max-w-sm leading-relaxed mb-4">
        {atRisk ? (
          <span>
            Mô hình dự đoán sinh viên <strong className="text-rose-400">CÓ nguy cơ</strong> trượt hoặc
            bỏ học với xác suất <strong className="text-white">{percentage}%</strong> (vượt ngưỡng phân lớp tối ưu).
          </span>
        ) : (
          <span>
            Mô hình dự đoán sinh viên <strong className="text-brand-400">AN TOÀN</strong> — xác
            suất rủi ro chỉ ở mức <strong className="text-white">{percentage}%</strong>.
          </span>
        )}
      </p>

    </div>
  );
};
