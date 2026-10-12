import React, { useState } from 'react';
import { useApp } from '../state/AppContext';
import { StudentFeatures, PredictionResponse } from '@shared/types';
import { DEFAULT_FEATURES } from '@shared/constants';
import { predictStudentRisk } from '../services/api';
import { generateInterventions } from '../utils/recommendations';

import { FeatureForm } from '../components/dashboard/FeatureForm';
import { RiskGauge } from '../components/dashboard/RiskGauge';
import { HistoryTable } from '../components/dashboard/HistoryTable';
import { RadarCompetencyChart } from '../components/recommendation/RadarCompetencyChart';
import { InterventionList } from '../components/recommendation/InterventionList';
import { ArrowDown, Sparkles } from 'lucide-react';

export const DashboardPage: React.FC = () => {
  const { apiBase, addHistory, addToast } = useApp();

  const [features, setFeatures] = useState<StudentFeatures>(DEFAULT_FEATURES);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<PredictionResponse | null>(null);

  const handlePredict = async () => {
    setLoading(true);
    try {
      const data = await predictStudentRisk(apiBase, features);
      setResult(data);

      const now = new Date();
      addHistory({
        id: Math.random().toString(36).slice(2, 9),
        time: now.toLocaleTimeString('vi-VN'),
        date: now.toLocaleDateString('vi-VN'),
        module: features.code_module,
        age: features.age_band,
        credits: features.studied_credits,
        clicks: features.total_clicks_to_t,
        prediction: data.prediction,
        confidence: data.confidence,
        features: { ...features },
      });

      addToast('Phân tích hoàn tất! Đã cập nhật kết quả và kế hoạch can thiệp.', 'success');
    } catch (err: unknown) {
      const error = err as Error;
      addToast(error.message || 'Không thể thực hiện dự đoán.', 'error', 5000);
    } finally {
      setLoading(false);
    }
  };

  const atRisk = result ? result.prediction === 1 : false;
  const probability = result ? result.confidence : 0.42;
  const strategies = generateInterventions(features, atRisk, probability);

  return (
    <div className="space-y-8 py-4">
      {/* Page Header */}
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-4 border-b border-slate-800">
          <div>
            <h1 className="text-2xl font-extrabold text-white tracking-tight flex items-center gap-2">
              <span>Bảng Điều Khiển Dự Đoán &amp; Can Thiệp</span>
              <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-brand-500/20 text-brand-400 border border-brand-500/30">
                LightGBM
              </span>
            </h1>
            <p className="text-xs text-slate-400 mt-1">
              Phân tích đa chiều trên 17 chỉ số hành vi học tập OULAD tại mốc Cutoff 75%
            </p>
          </div>

        </div>
      </div>

      {/* Main Grid: Form (Left) & Results (Right) */}
      <div className="max-w-7xl mx-auto px-4 grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left column: 17-feature input form */}
        <div className="lg:col-span-7 space-y-6">
          <FeatureForm
            features={features}
            onChange={setFeatures}
            onSubmit={handlePredict}
            loading={loading}
          />
        </div>

        {/* Right column: Risk Gauge & Results */}
        <div className="lg:col-span-5 space-y-6">
          {result ? (
            <>
              <RiskGauge atRisk={atRisk} probability={probability} />
              <InterventionList strategies={strategies} />
            </>
          ) : (
            <div className="p-8 rounded-2xl bg-slate-900/60 border border-slate-800 border-dashed text-center flex flex-col items-center justify-center min-h-[380px]">
              <div className="w-14 h-14 rounded-2xl bg-brand-500/10 border border-brand-500/20 text-brand-400 flex items-center justify-center mb-4">
                <Sparkles className="w-7 h-7" />
              </div>
              <h3 className="text-lg font-bold text-white mb-2">Chờ phân tích hồ sơ</h3>
              <p className="text-xs text-slate-400 max-w-xs leading-relaxed mb-6">
                Nhấn nút <strong className="text-brand-400">"Phân tích nguy cơ học tập"</strong> ở form bên
                trái hoặc nạp mẫu thử nghiệm để xem kết quả đánh giá nguy cơ và đề xuất giải pháp.
              </p>
              <button
                onClick={handlePredict}
                disabled={loading}
                className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-750 text-slate-200 text-xs font-semibold border border-slate-700 transition-colors"
              >
                <span>Chạy thử với dữ liệu hiện tại</span>
                <ArrowDown className="w-3.5 h-3.5" />
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Full-width Section: Radar Competency Chart */}
      <div className="max-w-7xl mx-auto px-4">
        <RadarCompetencyChart features={features} />
      </div>

      {/* Full-width Section: Session History */}
      <div className="max-w-7xl mx-auto px-4">
        <HistoryTable />
      </div>
    </div>
  );
};
