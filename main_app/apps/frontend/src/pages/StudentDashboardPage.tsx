import React, { useEffect, useState } from 'react';
import { useApp } from '../state/AppContext';
import { ActionableRecourseResponse, PredictionResponse, StudentFeatures } from '@shared/types';
import { WEAK_PRESETS, GOOD_PRESETS } from '@shared/constants';
import { fetchActionableRecourse, predictStudentRisk } from '../services/api';
import {
  AlertTriangle,
  ArrowRight,
  Calendar,
  CheckCircle2,
  Compass,
  GraduationCap,
  HeartHandshake,
  MessageSquare,
  RotateCcw,
  Send,
  ShieldCheck,
  Sparkles,
  Zap,
} from 'lucide-react';

interface StudentScenarioPreset {
  id: string;
  name: string;
  subtitle: string;
  features: StudentFeatures;
}

const PRESET_SCENARIOS: StudentScenarioPreset[] = [
  {
    id: 'case_late_submissions',
    name: 'TH 1: Bạn Nam (Nợ bài kiểm tra)',
    subtitle: 'Môn BBB · Đã nộp 7/9 bài, nhiều bài nộp trễ hạn',
    features: WEAK_PRESETS[0],
  },
  {
    id: 'case_inactivity',
    name: 'TH 2: Bạn Mai (Gián đoạn học tập)',
    subtitle: 'Môn CCC · 8 ngày chưa vào học, tỷ lệ nộp bài 33%',
    features: WEAK_PRESETS[1],
  },
  {
    id: 'case_low_clicks',
    name: 'TH 3: Bạn Tuấn (Ít tương tác tài liệu)',
    subtitle: 'Môn FFF · Lượt click học liệu rất ít, nguy cơ cao',
    features: WEAK_PRESETS[4],
  },
  {
    id: 'case_good_standing',
    name: 'TH 4: Bạn Lan (Học lực vững vàng)',
    subtitle: 'Môn AAA · Chuyên cần cao, nộp bài đầy đủ 100%',
    features: GOOD_PRESETS[0],
  },
];

export const StudentDashboardPage: React.FC = () => {
  const { apiBase, setCurrentView, addToast } = useApp();

  const [selectedCaseId, setSelectedCaseId] = useState<string>('case_late_submissions');
  const [loading, setLoading] = useState(false);
  const [prediction, setPrediction] = useState<PredictionResponse | null>(null);
  const [recourse, setRecourse] = useState<ActionableRecourseResponse | null>(null);

  // Checklist state: key is action index, value is boolean
  const [checkedTasks, setCheckedTasks] = useState<Record<number, boolean>>({});

  // Advisor message modal state
  const [isMessageModalOpen, setIsMessageModalOpen] = useState(false);
  const [advisorMessage, setAdvisorMessage] = useState(
    'Em chào Thầy/Cô cố vấn học tập, em vừa kiểm tra lộ trình học tập và thấy môn học hiện tại đang cần nỗ lực thêm. Em mong Thầy/Cô hướng dẫn thêm cho em về kế hoạch bù đắp các bài tập còn thiếu ạ.'
  );

  const activeCase = PRESET_SCENARIOS.find((c) => c.id === selectedCaseId) || PRESET_SCENARIOS[0];

  useEffect(() => {
    let cancelled = false;
    const runInference = async () => {
      setLoading(true);
      setCheckedTasks({});
      try {
        const [predRes, recRes] = await Promise.all([
          predictStudentRisk(apiBase, activeCase.features),
          fetchActionableRecourse(apiBase, activeCase.features),
        ]);
        if (!cancelled) {
          setPrediction(predRes);
          setRecourse(recRes);
        }
      } catch (err: unknown) {
        if (!cancelled) {
          const e = err as Error;
          addToast(e.message || 'Không thể tải lộ trình sinh viên.', 'error');
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    runInference();
    return () => {
      cancelled = true;
    };
  }, [activeCase, apiBase, addToast]);

  const atRisk = prediction ? prediction.prediction === 1 : true;
  const safetyScore = prediction ? Math.round((1 - prediction.confidence) * 100) : 40;

  const quickWinScenario = recourse?.scenarios.find((s) => s.id === 'quick_win') || recourse?.scenarios[0];
  const srlActions = quickWinScenario?.srl_plan.flatMap((p) => p.action_items) || [
    'Đăng nhập vào hệ thống LMS ngay hôm nay để xóa bỏ chuỗi ngày gián đoạn.',
    'Hoàn thành bài tập đánh giá nợ để tích lũy điểm quá trình.',
    'Dành ít nhất 3 buổi trong tuần này để xem lại tài liệu cốt lõi.',
  ];

  const handleToggleTask = (idx: number) => {
    setCheckedTasks((prev) => {
      const next = { ...prev, [idx]: !prev[idx] };
      const totalChecked = Object.values(next).filter(Boolean).length;
      if (totalChecked === srlActions.length) {
        addToast('🎉 Tuyệt vời! Bạn đã hoàn thành toàn bộ mục tiêu tuần này!', 'success', 5000);
      }
      return next;
    });
  };

  const completedCount = Object.values(checkedTasks).filter(Boolean).length;
  const progressPercent = Math.round((completedCount / (srlActions.length || 1)) * 100);

  const handleSendMessage = () => {
    setIsMessageModalOpen(false);
    addToast('Đã gửi tin nhắn đến Cố vấn học tập thành công! Cố vấn sẽ phản hồi trong 24 giờ.', 'success');
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6 py-4 px-3 sm:px-6">
      {/* Top Banner / Switch to Advisor View */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 rounded-2xl bg-gradient-to-r from-sky-950/60 via-slate-900 to-indigo-950/60 border border-sky-500/20 shadow-lg">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-sky-500/20 border border-sky-500/30 text-sky-400 flex items-center justify-center shrink-0">
            <GraduationCap className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-base sm:text-lg font-bold text-foreground">
              Góc Nhìn Học Tập Cá Nhân Hóa (Dành cho Sinh viên)
            </h1>
            <p className="text-xs text-slate-400">
              Giao diện tối giản, tập trung vào hành động thực tế — không chứa thuật ngữ kỹ thuật phức tạp
            </p>
          </div>
        </div>

        <button
          onClick={() => setCurrentView('dashboard')}
          className="inline-flex items-center justify-center gap-2 px-3.5 py-2 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-sky-300 border border-slate-700 transition-all shrink-0"
        >
          <span>Chuyển sang Dashboard Cố vấn</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Case Selector Tabs */}
      <div className="space-y-2">
        <label className="text-xs font-semibold text-slate-400 flex items-center gap-1.5">
          <Compass className="w-4 h-4 text-sky-400" />
          <span>Thử nghiệm nhanh các trường hợp sinh viên khác nhau:</span>
        </label>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2.5">
          {PRESET_SCENARIOS.map((c) => {
            const isSelected = c.id === selectedCaseId;
            return (
              <button
                key={c.id}
                onClick={() => setSelectedCaseId(c.id)}
                disabled={loading}
                className={`p-3 rounded-xl text-left transition-all border ${
                  isSelected
                    ? 'bg-sky-500/15 border-sky-500/50 shadow-md shadow-sky-500/5'
                    : 'bg-slate-950/60 border-slate-800 hover:border-slate-700'
                }`}
              >
                <div className="text-xs font-bold text-slate-100">{c.name}</div>
                <div className="text-[11px] text-slate-400 mt-1 leading-snug">{c.subtitle}</div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Loading Skeleton */}
      {loading && (
        <div className="p-8 rounded-2xl bg-slate-900/60 border border-slate-800 text-center flex items-center justify-center gap-3 text-xs text-slate-400">
          <div className="w-4 h-4 rounded-full border-2 border-sky-400 border-t-transparent animate-spin" />
          <span>Hệ thống đang chuẩn bị lộ trình học tập cá nhân của bạn...</span>
        </div>
      )}

      {!loading && prediction && (
        <>
          {/* Main Status Hero Card */}
          <div
            className={`p-6 rounded-2xl border shadow-xl transition-all ${
              !atRisk
                ? 'bg-gradient-to-br from-emerald-950/40 via-slate-900 to-slate-950 border-emerald-500/30'
                : 'bg-gradient-to-br from-amber-950/30 via-slate-900 to-slate-950 border-amber-500/30'
            }`}
          >
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="space-y-1.5">
                <div className="flex items-center gap-2">
                  <span
                    className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-bold border ${
                      !atRisk
                        ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30'
                        : 'bg-amber-500/20 text-amber-300 border-amber-500/30'
                    }`}
                  >
                    {!atRisk ? <ShieldCheck className="w-3.5 h-3.5" /> : <AlertTriangle className="w-3.5 h-3.5" />}
                    <span>{!atRisk ? 'Đang Học Tốt & An Tâm' : 'Cần Tăng Tốc Nhẹ'}</span>
                  </span>
                  <span className="text-xs text-slate-400">
                    Học phần {activeCase.features.code_module}
                  </span>
                </div>

                <h2 className="text-xl sm:text-2xl font-extrabold text-foreground tracking-tight">
                  {!atRisk
                    ? 'Bạn đang duy trì phong độ học tập rất vững vàng! 🌟'
                    : 'Đừng lo lắng! Chỉ cần một vài bước điều chỉnh là bạn sẽ an tâm qua môn. 💪'}
                </h2>
                <p className="text-xs sm:text-sm text-slate-300 leading-relaxed max-w-2xl">
                  {!atRisk
                    ? 'Tỷ lệ nộp bài và tương tác của bạn đều ở mức an toàn. Hãy tiếp tục duy trì lịch học này cho kỳ thi kết thúc học phần.'
                    : 'Hệ thống đã nhận diện điểm nghẽn học tập hiện tại và tính toán sẵn lộ trình tối thiểu khả thi nhất để giúp bạn thoát khỏi vùng nguy hiểm.'}
                </p>
              </div>

              {/* Readiness Score Gauge */}
              <div className="shrink-0 flex flex-col items-center justify-center p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 min-w-[140px]">
                <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                  Độ Sẵn Sàng Qua Môn
                </div>
                <div
                  className={`text-3xl font-extrabold mt-1 ${
                    !atRisk ? 'text-emerald-400' : 'text-amber-400'
                  }`}
                >
                  {safetyScore}%
                </div>
                <div className="w-full bg-slate-800 h-1.5 rounded-full mt-2 overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-700 ${
                      !atRisk ? 'bg-emerald-400' : 'bg-amber-400'
                    }`}
                    style={{ width: `${safetyScore}%` }}
                  />
                </div>
              </div>
            </div>
          </div>

          {/* 2-Column Core Action Area */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            {/* Left Column: Weekly Action Checklist */}
            <div className="lg:col-span-7 bg-slate-900/90 rounded-2xl border border-slate-800 shadow-xl p-5 sm:p-6 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div className="flex items-center gap-2">
                  <Calendar className="w-5 h-5 text-sky-400" />
                  <h3 className="text-sm font-bold text-slate-100">
                    Kế Hoạch Hành Động Tuần Này (Tick để đánh dấu)
                  </h3>
                </div>
                <span className="text-xs font-mono font-semibold text-slate-400">
                  {completedCount}/{srlActions.length} hoàn thành
                </span>
              </div>

              {/* Progress bar */}
              <div className="w-full bg-slate-950 h-2 rounded-full overflow-hidden border border-slate-800">
                <div
                  className="h-full bg-gradient-to-r from-sky-500 to-emerald-400 transition-all duration-300 rounded-full"
                  style={{ width: `${progressPercent}%` }}
                />
              </div>

              {/* Interactive task list */}
              <div className="space-y-2.5 pt-1">
                {srlActions.map((action, idx) => {
                  const isDone = Boolean(checkedTasks[idx]);
                  return (
                    <div
                      key={idx}
                      onClick={() => handleToggleTask(idx)}
                      className={`p-3.5 rounded-xl border flex items-start gap-3 cursor-pointer transition-all ${
                        isDone
                          ? 'bg-emerald-950/20 border-emerald-500/30 text-slate-300'
                          : 'bg-slate-950/60 border-slate-800 hover:border-slate-700 text-slate-200'
                      }`}
                    >
                      <button
                        type="button"
                        className={`w-5 h-5 rounded-md flex items-center justify-center shrink-0 mt-0.5 border transition-all ${
                          isDone
                            ? 'bg-emerald-500 border-emerald-500 text-slate-950'
                            : 'border-slate-600 bg-slate-900'
                        }`}
                      >
                        {isDone && <CheckCircle2 className="w-4 h-4 text-white" />}
                      </button>

                      <div className="min-w-0 flex-1 text-xs sm:text-sm leading-relaxed">
                        <span className={isDone ? 'line-through text-slate-400' : ''}>
                          {action}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>

              <div className="pt-2 flex items-center justify-between text-xs text-slate-400">
                <span className="flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-amber-400" />
                  <span>Hoàn thành các mục này để nâng xác suất qua môn</span>
                </span>
                {completedCount > 0 && (
                  <button
                    onClick={() => setCheckedTasks({})}
                    className="text-slate-400 hover:text-slate-200 flex items-center gap-1 text-[11px]"
                  >
                    <RotateCcw className="w-3 h-3" />
                    <span>Làm lại</span>
                  </button>
                )}
              </div>
            </div>

            {/* Right Column: Goal & Support Cards */}
            <div className="lg:col-span-5 space-y-4">
              {/* Minimal Goals Target Card (Derived from DiCE) */}
              <div className="bg-slate-900/90 rounded-2xl border border-sky-500/20 shadow-xl p-5 space-y-3.5">
                <div className="flex items-center gap-2 text-sky-400">
                  <Zap className="w-4 h-4" />
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200">
                    Mục Tiêu Tối Thiểu Khả Thi
                  </h3>
                </div>

                <p className="text-xs text-slate-300 leading-relaxed">
                  {quickWinScenario?.summary ||
                    'Duy trì vào học đều đặn và nộp bài đánh giá đúng hạn để giữ vững kết quả an toàn.'}
                </p>

                {quickWinScenario?.targets && quickWinScenario.targets.length > 0 && (
                  <div className="space-y-2 pt-2 border-t border-slate-800">
                    {quickWinScenario.targets.slice(0, 3).map((target) => (
                      <div
                        key={target.feature}
                        className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800 flex items-center justify-between text-xs"
                      >
                        <span className="text-slate-300 font-medium">{target.label}</span>
                        <span className="font-bold font-mono text-sky-300">
                          {target.target_value}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Advisor Support Card */}
              <div className="bg-slate-900/90 rounded-2xl border border-slate-800 shadow-xl p-5 space-y-3">
                <div className="flex items-center gap-2 text-purple-400">
                  <HeartHandshake className="w-4 h-4" />
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200">
                    Đồng Hành Cùng Thầy Cô
                  </h3>
                </div>

                <p className="text-xs text-slate-400 leading-relaxed">
                  Nếu bạn đang gặp khó khăn trong học tập hoặc cần gia hạn nộp bài, đừng ngần ngại gửi tin nhắn cho Cố vấn học tập của khoa.
                </p>

                <button
                  onClick={() => setIsMessageModalOpen(true)}
                  className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-purple-600/20 hover:bg-purple-600/30 text-purple-200 border border-purple-500/30 text-xs font-bold transition-all"
                >
                  <MessageSquare className="w-4 h-4" />
                  <span>Gửi tin nhắn cho Cố vấn</span>
                </button>
              </div>
            </div>
          </div>
        </>
      )}

      {/* Message Modal */}
      {isMessageModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in">
          <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl p-6 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-purple-400">
                <MessageSquare className="w-5 h-5" />
                <h3 className="text-base font-bold text-foreground">Gửi Yêu Cầu Hỗ Trợ</h3>
              </div>
              <button
                onClick={() => setIsMessageModalOpen(false)}
                className="text-slate-400 hover:text-slate-200 text-sm"
              >
                ✕
              </button>
            </div>

            <p className="text-xs text-slate-400 leading-relaxed">
              Tin nhắn này sẽ được gửi trực tiếp đến hệ thống tư vấn của Khoa / Trường.
            </p>

            <textarea
              rows={4}
              value={advisorMessage}
              onChange={(e) => setAdvisorMessage(e.target.value)}
              className="w-full p-3 rounded-xl bg-slate-950 border border-slate-750 text-xs sm:text-sm text-slate-200 focus:border-purple-500 focus:outline-none"
            />

            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                onClick={() => setIsMessageModalOpen(false)}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:bg-slate-800"
              >
                Hủy bỏ
              </button>
              <button
                onClick={handleSendMessage}
                className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold bg-purple-600 hover:bg-purple-500 text-white shadow-lg shadow-purple-600/25 transition-all"
              >
                <Send className="w-3.5 h-3.5" />
                <span>Gửi ngay</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
