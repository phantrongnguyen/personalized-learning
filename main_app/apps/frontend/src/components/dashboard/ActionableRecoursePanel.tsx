import React, { useEffect, useState } from 'react';
import {
  ActionableRecourseResponse,
  PredictionResponse,
  RecourseScenario,
  StudentFeatures,
} from '@shared/types';
import { fetchActionableRecourse } from '../../services/api';
import { useApp } from '../../state/AppContext';
import {
  AlertCircle,
  BookOpen,
  CalendarCheck,
  CheckCircle2,
  ChevronDown,
  Copy,
  GraduationCap,
  PlayCircle,
  RotateCcw,
  ShieldCheck,
  Sparkles,
  TrendingDown,
  Zap,
} from 'lucide-react';

interface ActionableRecoursePanelProps {
  features: StudentFeatures;
  prediction: PredictionResponse;
  onApplyScenario?: (scenarioFeatures: StudentFeatures) => void;
  onRestoreOriginal?: () => void;
  isSimulated?: boolean;
}

const percent = (val: number) => `${(val * 100).toFixed(1)}%`;

export const ActionableRecoursePanel: React.FC<ActionableRecoursePanelProps> = ({
  features,
  prediction,
  onApplyScenario,
  onRestoreOriginal,
  isSimulated = false,
}) => {
  const { apiBase, addToast } = useApp();
  const [data, setData] = useState<ActionableRecourseResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedScenarioId, setSelectedScenarioId] = useState<'quick_win' | 'sustainable'>('quick_win');

  const atRisk = prediction.prediction === 1;

  useEffect(() => {
    // Only fetch when at risk or when user wants actionable recourse
    let cancelled = false;
    const loadRecourse = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await fetchActionableRecourse(apiBase, features);
        if (!cancelled) {
          setData(res);
          if (res.scenarios.length > 0) {
            setSelectedScenarioId(res.scenarios[0].id);
          }
        }
      } catch (err: unknown) {
        if (!cancelled) {
          const e = err as Error;
          setError(e.message || 'Không thể tính toán mục tiêu can thiệp khả thi.');
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    loadRecourse();

    return () => {
      cancelled = true;
    };
  }, [apiBase, features]);

  if (!atRisk && data?.status === 'not_at_risk') {
    return (
      <section className="min-w-0 rounded-2xl border border-emerald-500/20 bg-emerald-950/20 p-5 sm:p-6 shadow-xl">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-emerald-500/10 p-2.5 text-emerald-400 border border-emerald-500/20">
              <ShieldCheck className="h-6 w-6" />
            </div>
            <div>
              <h2 className="text-base sm:text-lg font-bold text-foreground">
                Hồ Sơ An Toàn — Khuyến Nghị Duy Trì Nhịp Học
              </h2>
              <p className="mt-0.5 text-xs text-slate-400">
                Xác suất rủi ro hiện tại: <strong className="text-emerald-400">{percent(prediction.confidence)}</strong> (dưới ngưỡng cảnh báo {percent(prediction.threshold ?? 0.5)})
              </p>
            </div>
          </div>
          <span className="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-300">
            Trạng thái An toàn
          </span>
        </div>
        <p className="mt-4 text-xs leading-relaxed text-slate-300">
          Người học không cần lộ trình đảo ngược nguy cơ khẩn cấp. Khuyến nghị tiếp tục duy trì số ngày hoạt động đều đặn và nộp các bài đánh giá cuối kỳ đúng hạn để giữ vững kết quả.
        </p>
      </section>
    );
  }

  const activeScenario: RecourseScenario | undefined = data?.scenarios.find(
    (s) => s.id === selectedScenarioId
  ) || data?.scenarios[0];

  const handleCopyPlan = () => {
    if (!activeScenario) return;

    const lines: string[] = [
      `[EduRisk AI — Kế hoạch Can thiệp Sư phạm & Mục tiêu Khả thi]`,
      `Kịch bản: ${activeScenario.title}`,
      `Hiện trạng: Xác suất nguy cơ ${percent(data?.current_probability ?? prediction.confidence)}`,
      `Mục tiêu sau can thiệp: Giảm về ${percent(activeScenario.target_probability)} (giảm ${percent(activeScenario.probability_reduction)})`,
      ``,
      `--- CÁC CHỈ TIÊU HÀNH VI CẦN ĐẠT ---`,
      ...activeScenario.targets.map(
        (t) =>
          `* ${t.label}: Hiện tại ${t.current_value} -> Cần đạt ${t.target_value} (Thay đổi: ${t.delta > 0 ? '+' : ''}${t.delta} ${t.unit}) | ${t.pedagogical_rationale}`
      ),
      ``,
      `--- LỘ TRÌNH 3 GIAI ĐOẠN TỰ ĐIỀU CHỈNH (SRL) ---`,
      ...activeScenario.srl_plan.map(
        (p) =>
          `[${p.phase_name} - ${p.timeframe}]\n` +
          `Mục tiêu: ${p.objective}\n` +
          p.action_items.map((a) => ` - ${a}`).join('\n')
      ),
      ``,
      `Căn cứ khoa học: DiCE (Mothilal et al. 2020), Wachter et al. (2017), Pardo et al. (2019).`,
    ];

    navigator.clipboard
      .writeText(lines.join('\n'))
      .then(() => addToast('Đã sao chép kế hoạch can thiệp vào Clipboard!', 'success'))
      .catch(() => addToast('Không thể sao chép tự động, vui lòng thử lại.', 'warning'));
  };

  const handleApply = () => {
    if (!activeScenario || !onApplyScenario) return;
    onApplyScenario(activeScenario.features);
    addToast(
      `Đã áp dụng "${activeScenario.title}" vào bảng nhập liệu! Bạn có thể xem kết quả mô hình tính lại bên trên.`,
      'success',
      6000
    );
  };

  return (
    <section
      aria-labelledby="recourse-heading"
      className="min-w-0 rounded-2xl border border-sky-500/30 bg-slate-900/95 p-5 shadow-2xl sm:p-6"
    >
      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-3 border-b border-slate-800 pb-4">
        <div className="flex min-w-0 items-start gap-3">
          <div className="shrink-0 rounded-xl bg-sky-500/10 p-2.5 text-sky-400 border border-sky-500/20">
            <Zap className="h-6 w-6" />
          </div>
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <h2 id="recourse-heading" className="text-base sm:text-lg font-bold text-foreground">
                Kế Hoạch Đảo Ngược Nguy Cơ &amp; Mục Tiêu Khả Thi
              </h2>
              <span className="rounded-md border border-sky-500/30 bg-sky-500/10 px-2 py-0.5 text-[10px] font-mono font-semibold text-sky-300">
                Actionable Recourse + SRL
              </span>
            </div>
            <p className="mt-1 text-xs leading-relaxed text-slate-400">
              Thuật toán tối ưu hóa phản thực nghiệm (Counterfactual Recourse): Khóa biến nhân khẩu học, tính toán sự thay đổi hành vi tối thiểu để đưa mô hình về vùng an toàn.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {isSimulated && onRestoreOriginal && (
            <button
              onClick={onRestoreOriginal}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-amber-500/10 hover:bg-amber-500/20 text-amber-300 border border-amber-500/30 transition-colors"
            >
              <RotateCcw className="h-3.5 w-3.5" />
              <span>Khôi phục ban đầu</span>
            </button>
          )}

          <button
            onClick={handleCopyPlan}
            disabled={!activeScenario}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-colors disabled:opacity-50"
            title="Sao chép toàn bộ kế hoạch can thiệp để lưu hoặc gửi sinh viên"
          >
            <Copy className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">Sao chép kế hoạch</span>
            <span className="sm:hidden">Sao chép</span>
          </button>
        </div>
      </div>

      {/* Loading & Error States */}
      {loading && (
        <div className="py-8 text-center text-xs text-slate-400 flex items-center justify-center gap-2">
          <div className="h-4 w-4 animate-spin rounded-full border-2 border-sky-400 border-t-transparent" />
          <span>Đang tính toán các mục tiêu can thiệp khả thi từ mô hình LightGBM...</span>
        </div>
      )}

      {error && (
        <div className="mt-4 rounded-xl border border-rose-500/30 bg-rose-500/10 p-4 text-xs text-rose-300 flex items-center gap-2">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {data && activeScenario && (
        <div className="mt-5 space-y-6">
          {/* Scenario Tabs */}
          <div className="flex flex-wrap gap-2 border-b border-slate-800/80 pb-3">
            {data.scenarios.map((sc) => {
              const isSelected = sc.id === selectedScenarioId;
              return (
                <button
                  key={sc.id}
                  onClick={() => setSelectedScenarioId(sc.id)}
                  className={`flex flex-col sm:flex-row items-start sm:items-center gap-1.5 sm:gap-3 px-4 py-2.5 rounded-xl text-xs font-semibold transition-all border ${
                    isSelected
                      ? 'bg-sky-500/15 border-sky-500/40 text-sky-200 shadow-md shadow-sky-500/5'
                      : 'bg-slate-950/60 border-slate-800 text-slate-400 hover:text-slate-200 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-center gap-1.5">
                    {sc.id === 'quick_win' ? (
                      <Zap className="h-4 w-4 text-amber-400 shrink-0" />
                    ) : (
                      <GraduationCap className="h-4 w-4 text-emerald-400 shrink-0" />
                    )}
                    <span>{sc.title}</span>
                  </div>
                  <span
                    className={`text-[11px] font-mono px-2 py-0.5 rounded-md ${
                      isSelected
                        ? 'bg-sky-400/20 text-sky-300 font-bold'
                        : 'bg-slate-800 text-slate-400'
                    }`}
                  >
                    Nguy cơ: {percent(sc.target_probability)} (-{percent(sc.probability_reduction)})
                  </span>
                </button>
              );
            })}
          </div>

          {/* Scenario Highlight Box */}
          <div className="rounded-xl border border-sky-500/20 bg-sky-950/30 p-4 sm:p-5">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold uppercase tracking-wider text-sky-400">
                    {activeScenario.badge}
                  </span>
                  <span className="h-1 w-1 rounded-full bg-slate-600" />
                  <span className="text-xs text-slate-400">
                    Mô hình dự báo khi đạt các chỉ tiêu:
                  </span>
                </div>
                <p className="text-sm font-semibold text-slate-200 leading-relaxed">
                  {activeScenario.summary}
                </p>
              </div>

              {/* What-if Simulator CTA Button */}
              {onApplyScenario && (
                <button
                  onClick={handleApply}
                  className="inline-flex shrink-0 items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-sky-600 to-indigo-600 hover:from-sky-500 hover:to-indigo-500 px-4 py-2.5 text-xs font-bold text-white shadow-lg shadow-sky-500/20 transition-all hover:scale-[1.02] active:scale-[0.98]"
                >
                  <PlayCircle className="h-4 w-4 shrink-0" />
                  <span>Áp dụng vào Form (Thử nghiệm What-if)</span>
                </button>
              )}
            </div>

            {/* Probability Delta Comparison */}
            <div className="mt-4 grid grid-cols-1 sm:grid-cols-3 gap-3 pt-3 border-t border-slate-800/80">
              <div className="rounded-lg bg-slate-950/60 p-3 border border-slate-800">
                <p className="text-[11px] text-slate-400">Xác suất nguy cơ hiện tại</p>
                <p className="mt-1 text-xl font-bold text-rose-300">
                  {percent(data.current_probability)}
                </p>
                <p className="text-[10px] text-rose-400/80 mt-0.5">Vượt ngưỡng an toàn</p>
              </div>

              <div className="rounded-lg bg-slate-950/60 p-3 border border-slate-800">
                <p className="text-[11px] text-slate-400">Mức độ giảm dự kiến</p>
                <div className="mt-1 flex items-center gap-1.5 text-xl font-bold text-emerald-400">
                  <TrendingDown className="h-5 w-5" />
                  <span>-{percent(activeScenario.probability_reduction)}</span>
                </div>
                <p className="text-[10px] text-emerald-400/80 mt-0.5">Đảo chiều về an toàn</p>
              </div>

              <div className="rounded-lg bg-sky-950/40 p-3 border border-sky-500/30">
                <p className="text-[11px] text-sky-300 font-medium">Xác suất sau can thiệp</p>
                <p className="mt-1 text-xl font-bold text-sky-200">
                  {percent(activeScenario.target_probability)}
                </p>
                <p className="text-[10px] text-sky-400/80 mt-0.5">Vùng an toàn vững chắc</p>
              </div>
            </div>
          </div>

          {/* Actionable Metrics Table / Grid */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-sky-400" />
                <span>Bảng Chỉ Tiêu Hành Vi Cần Đạt (Actionable Recourse Targets)</span>
              </h3>
              <span className="text-[11px] text-slate-400">
                Bảo toàn nhân khẩu học · Chỉ thay đổi hành vi
              </span>
            </div>

            <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-950/50">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="border-b border-slate-800 bg-slate-900/80 text-[11px] uppercase tracking-wider text-slate-400 font-semibold">
                  <tr>
                    <th scope="col" className="px-4 py-3">Chỉ số hành vi</th>
                    <th scope="col" className="px-3 py-3">Hiện tại</th>
                    <th scope="col" className="px-3 py-3">Mục tiêu cần đạt</th>
                    <th scope="col" className="px-3 py-3">Thay đổi (Δ)</th>
                    <th scope="col" className="px-4 py-3">Ý nghĩa &amp; Hành động sư phạm</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {activeScenario.targets.map((target) => (
                    <tr key={target.feature} className="hover:bg-slate-900/40 transition-colors">
                      <td className="px-4 py-3 font-semibold text-slate-100">
                        {target.label}
                      </td>
                      <td className="px-3 py-3 text-slate-400 font-mono">
                        {target.current_value}
                      </td>
                      <td className="px-3 py-3 font-mono font-bold text-sky-300">
                        {target.target_value}
                      </td>
                      <td className="px-3 py-3">
                        <span
                          className={`inline-flex items-center gap-0.5 font-mono font-semibold px-2 py-0.5 rounded text-[11px] ${
                            target.delta > 0
                              ? 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/20'
                              : 'bg-blue-500/10 text-blue-300 border border-blue-500/20'
                          }`}
                        >
                          {target.delta > 0 ? '+' : ''}
                          {target.delta} {target.unit}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-slate-400 leading-relaxed text-[11px]">
                        {target.pedagogical_rationale}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* 3-Phase Self-Regulated Learning (SRL) Implementation Roadmap */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
                <CalendarCheck className="h-4 w-4 text-emerald-400" />
                <span>Kế Hoạch Tự Điều Chỉnh 3 Giai Đoạn (SRL Intervention Plan)</span>
              </h3>
              <span className="text-[11px] text-slate-400">
                Mô hình Zimmerman / Pardo et al. (Computers &amp; Education)
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {activeScenario.srl_plan.map((phase, idx) => (
                <div
                  key={phase.phase}
                  className="rounded-xl border border-slate-800 bg-slate-950/70 p-4 flex flex-col justify-between hover:border-slate-700 transition-colors"
                >
                  <div>
                    <div className="flex items-center justify-between gap-2 mb-2">
                      <span className="inline-flex items-center justify-center w-6 h-6 rounded-lg bg-sky-500/10 border border-sky-500/20 text-xs font-bold text-sky-400">
                        {idx + 1}
                      </span>
                      <span className="text-[10px] font-mono text-slate-400 bg-slate-800/80 px-2 py-0.5 rounded">
                        {phase.timeframe}
                      </span>
                    </div>

                    <h4 className="text-xs font-bold text-slate-100 leading-snug">
                      {phase.phase_name}
                    </h4>

                    <p className="mt-1.5 text-[11px] text-sky-300 font-medium">
                      Mục tiêu: {phase.objective}
                    </p>

                    <ul className="mt-3 space-y-2 text-[11px] text-slate-300">
                      {phase.action_items.map((action, aIdx) => (
                        <li key={aIdx} className="flex items-start gap-1.5 leading-relaxed">
                          <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400 shrink-0 mt-0.5" />
                          <span>{action}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div className="mt-4 pt-3 border-t border-slate-800/60 flex items-center justify-between text-[10px] text-slate-500">
                    <span>Chủ thể thực hiện:</span>
                    <span className="font-semibold text-slate-300 capitalize">
                      {phase.stakeholder === 'collaborative'
                        ? 'Sinh viên + Cố vấn'
                        : phase.stakeholder === 'student'
                        ? 'Sinh viên'
                        : 'Cố vấn học tập'}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Academic Grounding & Literature Details */}
          <details className="rounded-xl border border-slate-800 bg-slate-950/30 p-4">
            <summary className="cursor-pointer text-xs font-semibold text-slate-300 flex items-center justify-between">
              <span className="flex items-center gap-2">
                <BookOpen className="h-4 w-4 text-sky-400" />
                <span>Cơ sở Khoa học, Bài báo Nổi tiếng &amp; Giới hạn Học thuật</span>
              </span>
              <ChevronDown className="h-4 w-4 text-slate-400" />
            </summary>

            <div className="mt-4 space-y-4 text-xs leading-relaxed text-slate-400 border-t border-slate-800 pt-3">
              <div>
                <p className="font-semibold text-slate-200">1. Các khung lý thuyết nền tảng:</p>
                <ul className="mt-1 list-disc space-y-1.5 pl-5">
                  {data.theoretical_foundations.frameworks.map((fw, i) => (
                    <li key={i}>{fw}</li>
                  ))}
                </ul>
              </div>

              <div>
                <p className="font-semibold text-slate-200">2. Các bài báo quốc tế tiêu biểu:</p>
                <ul className="mt-1 list-disc space-y-1.5 pl-5 font-mono text-[11px]">
                  {data.theoretical_foundations.citations.map((cite, i) => (
                    <li key={i}>{cite}</li>
                  ))}
                </ul>
              </div>

              <div>
                <p className="font-semibold text-slate-200">3. Giới hạn &amp; Khuyến cáo học thuật:</p>
                <ul className="mt-1 list-disc space-y-1.5 pl-5 text-amber-300/80">
                  {data.theoretical_foundations.limitations.map((limit, i) => (
                    <li key={i}>{limit}</li>
                  ))}
                </ul>
              </div>
            </div>
          </details>
        </div>
      )}
    </section>
  );
};

