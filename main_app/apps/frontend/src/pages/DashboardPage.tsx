import React, { useState } from 'react';
import { useApp } from '../state/AppContext';
import { StudentFeatures, PredictionResponse } from '@shared/types';
import { DEFAULT_FEATURES } from '@shared/constants';
import { predictStudentRisk } from '../services/api';
import { generateExplainedInterventions } from '../utils/explanationRecommendations';
import { PredictionExplanation } from '../components/dashboard/PredictionExplanation';
import { ActionableRecoursePanel } from '../components/dashboard/ActionableRecoursePanel';
import { HistoricalCasesPanel } from '../components/dashboard/HistoricalCasesPanel';

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
  const [analyzedFeatures, setAnalyzedFeatures] = useState<StudentFeatures | null>(null);
  const [originalFeaturesBackup, setOriginalFeaturesBackup] = useState<StudentFeatures | null>(null);
  const [isSimulated, setIsSimulated] = useState<boolean>(false);

  const handlePredict = async () => {
    if (loading) return;
    const snapshot = { ...features };
    setLoading(true);
    try {
      const data = await predictStudentRisk(apiBase, snapshot);
      setResult(data);
      setAnalyzedFeatures(snapshot);
      setIsSimulated(false);
      setOriginalFeaturesBackup(null);

      const now = new Date();
      addHistory({
        id: Math.random().toString(36).slice(2, 9),
        time: now.toLocaleTimeString('vi-VN'),
        date: now.toLocaleDateString('vi-VN'),
        module: snapshot.code_module,
        age: snapshot.age_band,
        credits: snapshot.studied_credits,
        clicks: snapshot.total_clicks_to_t,
        prediction: data.prediction,
        confidence: data.confidence,
        features: snapshot,
      });

      addToast('Phân tích hoàn tất! Đã cập nhật kết quả và kế hoạch can thiệp.', 'success');
    } catch (err: unknown) {
      const error = err as Error;
      addToast(error.message || 'Không thể thực hiện dự đoán.', 'error', 5000);
    } finally {
      setLoading(false);
    }
  };

  const handleApplyPresetAndPredict = async (presetFeatures: StudentFeatures, label: string) => {
    if (loading) return;
    setFeatures(presetFeatures);
    setLoading(true);
    setIsSimulated(false);
    setOriginalFeaturesBackup(null);
    try {
      const data = await predictStudentRisk(apiBase, presetFeatures);
      setResult(data);
      setAnalyzedFeatures(presetFeatures);

      const now = new Date();
      addHistory({
        id: Math.random().toString(36).slice(2, 9),
        time: now.toLocaleTimeString('vi-VN'),
        date: now.toLocaleDateString('vi-VN'),
        module: presetFeatures.code_module,
        age: presetFeatures.age_band,
        credits: presetFeatures.studied_credits,
        clicks: presetFeatures.total_clicks_to_t,
        prediction: data.prediction,
        confidence: data.confidence,
        features: presetFeatures,
      });

      addToast(`Đã nạp ${label} và hoàn tất phân tích!`, 'success', 4000);
    } catch (err: unknown) {
      const error = err as Error;
      addToast(error.message || 'Không thể thực hiện dự đoán cho mẫu.', 'error', 5000);
    } finally {
      setLoading(false);
    }
  };

  const handleApplyScenario = async (scenarioFeatures: StudentFeatures) => {
    if (loading) return;
    if (!originalFeaturesBackup && analyzedFeatures) {
      setOriginalFeaturesBackup(analyzedFeatures);
    }
    setFeatures(scenarioFeatures);
    setLoading(true);
    try {
      const data = await predictStudentRisk(apiBase, scenarioFeatures);
      setResult(data);
      setAnalyzedFeatures(scenarioFeatures);
      setIsSimulated(true);

      const now = new Date();
      addHistory({
        id: Math.random().toString(36).slice(2, 9),
        time: now.toLocaleTimeString('vi-VN'),
        date: now.toLocaleDateString('vi-VN'),
        module: scenarioFeatures.code_module,
        age: scenarioFeatures.age_band,
        credits: scenarioFeatures.studied_credits,
        clicks: scenarioFeatures.total_clicks_to_t,
        prediction: data.prediction,
        confidence: data.confidence,
        features: scenarioFeatures,
      });

      addToast('Mô phỏng What-if thành công! Mô hình LightGBM đã tính lại xác suất cho kịch bản can thiệp.', 'success');
    } catch (err: unknown) {
      const error = err as Error;
      addToast(error.message || 'Không thể chạy mô phỏng kịch bản.', 'error', 5000);
    } finally {
      setLoading(false);
    }
  };

  const handleRestoreOriginal = async () => {
    if (!originalFeaturesBackup || loading) return;
    const backup = { ...originalFeaturesBackup };
    setFeatures(backup);
    setLoading(true);
    try {
      const data = await predictStudentRisk(apiBase, backup);
      setResult(data);
      setAnalyzedFeatures(backup);
      setIsSimulated(false);
      setOriginalFeaturesBackup(null);
      addToast('Đã khôi phục hồ sơ phân tích ban đầu.', 'info');
    } catch (err: unknown) {
      const error = err as Error;
      addToast(error.message || 'Không thể khôi phục hồ sơ ban đầu.', 'error', 5000);
    } finally {
      setLoading(false);
    }
  };

  const atRisk = result ? result.prediction === 1 : false;
  const probability = result ? result.confidence : 0.42;
  const strategies = generateExplainedInterventions(result?.explanation, atRisk);
  const hasUnanalyzedChanges = analyzedFeatures !== null &&
    (Object.keys(analyzedFeatures) as (keyof StudentFeatures)[]).some(key => features[key] !== analyzedFeatures[key]);

  return (
    <div className="space-y-8 py-4">
      {/* Page Header */}
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-4 border-b border-slate-800">
          <div>
            <h1 className="text-2xl font-extrabold text-foreground tracking-tight flex flex-wrap items-center gap-2">
              <span>Bảng Điều Khiển Dự Đoán &amp; Can Thiệp</span>
              <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                LightGBM
              </span>
              {isSimulated && (
                <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-sky-500/20 text-sky-300 border border-sky-500/30 animate-pulse">
                  Chế độ Mô phỏng What-if
                </span>
              )}
            </h1>
            <p className="text-xs text-slate-400 mt-1">
              Phân tích đa chiều trên 17 chỉ số hành vi học tập OULAD tại mốc Cutoff 75%
            </p>
          </div>

          <div className="break-all text-xs text-slate-500 font-mono">
            Trạng thái máy chủ: <span className="text-emerald-400 font-semibold">{apiBase}</span>
          </div>
        </div>
      </div>

      {isSimulated && (
        <div className="max-w-7xl mx-auto px-4" role="status">
          <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-sky-500/30 bg-sky-500/10 p-4 text-xs text-sky-200">
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 shrink-0 text-sky-400" />
              <span>
                Bạn đang xem kết quả mô phỏng kịch bản can thiệp (What-if Scenario). Các chỉ số trên bảng điều khiển đã được tính toán lại trực tiếp bởi mô hình LightGBM.
              </span>
            </div>
            <button
              onClick={handleRestoreOriginal}
              className="shrink-0 px-3 py-1.5 rounded-lg bg-sky-600 hover:bg-sky-500 text-white font-semibold transition-colors"
            >
              Khôi phục hồ sơ gốc
            </button>
          </div>
        </div>
      )}

      {hasUnanalyzedChanges && !isSimulated && (
        <div className="max-w-7xl mx-auto px-4" role="status">
          <p className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-4 text-sm leading-relaxed text-amber-200">
            Hồ sơ nhập đã thay đổi. Kết quả, giải thích, đối chiếu lịch sử, khuyến nghị và biểu đồ bên dưới vẫn thuộc hồ sơ đã phân tích trước đó. Nhấn phân tích lại để cập nhật.
          </p>
        </div>
      )}

      {/* Main Grid: Form (Left) & Results (Right) */}
      <div className="max-w-7xl mx-auto px-4 grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left column: 17-feature input form */}
        <div className="min-w-0 lg:col-span-7 space-y-6">
          <FeatureForm
            features={features}
            onChange={setFeatures}
            onSubmit={handlePredict}
            loading={loading}
            onApplyPresetAndPredict={handleApplyPresetAndPredict}
          />
        </div>

        {/* Right column: Risk Gauge & Results */}
        <div className="min-w-0 lg:col-span-5 space-y-6">
          {result ? (
            <>
              <RiskGauge atRisk={atRisk} probability={probability} apiBase={apiBase} />
            </>
          ) : (
            <div className="p-8 rounded-2xl bg-slate-900/60 border border-slate-800 border-dashed text-center flex flex-col items-center justify-center min-h-[380px]">
              <div className="w-14 h-14 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center mb-4">
                <Sparkles className="w-7 h-7" />
              </div>
              <h3 className="text-lg font-bold text-foreground mb-2">Chờ phân tích hồ sơ</h3>
              <p className="text-xs text-slate-400 max-w-xs leading-relaxed mb-6">
                Nhấn nút <strong className="text-emerald-400">"Mẫu SV Yếu"</strong> hoặc <strong className="text-emerald-400">"Phân tích nguy cơ học tập"</strong> ở form bên
                trái để nạp mẫu thực tế và xem kết quả đánh giá nguy cơ kèm đề xuất giải pháp.
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

      {result && (
        <div className="max-w-7xl mx-auto px-4 space-y-6">
          <PredictionExplanation result={result} />

          {analyzedFeatures && (
            <ActionableRecoursePanel
              features={analyzedFeatures}
              prediction={result}
              onApplyScenario={handleApplyScenario}
              onRestoreOriginal={handleRestoreOriginal}
              isSimulated={isSimulated}
            />
          )}

          {analyzedFeatures && <HistoricalCasesPanel features={analyzedFeatures} prediction={result} busy={loading} />}

          {strategies.length > 0 && <InterventionList strategies={strategies} />}
        </div>
      )}

      {/* Full-width Section: Radar Competency Chart */}
      <div className="max-w-7xl mx-auto px-4">
        <RadarCompetencyChart features={analyzedFeatures ?? features} />
      </div>

      {/* Full-width Section: Session History */}
      <div className="max-w-7xl mx-auto px-4">
        <HistoryTable />
      </div>
    </div>
  );
};
