import React, { useCallback, useEffect, useState } from 'react';
import { useApp } from '../state/AppContext';
import {
  AdvisorClassSummary,
  AdvisorStudentItem,
  CreateInterventionTaskPayload,
} from '@shared/types';
import {
  getAdvisorClassesApi,
  getAdvisorStudentsApi,
  createInterventionPlanApi,
} from '../services/api';
import {
  UserCheck,
  Users,
  AlertTriangle,
  ShieldCheck,
  Target,
  Loader2,
  ClipboardPlus,
  X,
  Plus,
} from 'lucide-react';

const EMPTY_TASK: CreateInterventionTaskPayload = {
  category: 'CHUYEN_CAN',
  priority: 'HIGH',
  title: '',
  description: '',
  target_metric: '',
};

export const AdvisorPage: React.FC = () => {
  const { apiBase, addToast } = useApp();

  const [classes, setClasses] = useState<AdvisorClassSummary[]>([]);
  const [students, setStudents] = useState<AdvisorStudentItem[]>([]);
  const [selectedClass, setSelectedClass] = useState<string>('');
  const [loading, setLoading] = useState(true);

  // Tạo kế hoạch can thiệp
  const [planTarget, setPlanTarget] = useState<AdvisorStudentItem | null>(null);
  const [planNote, setPlanNote] = useState('');
  const [planDate, setPlanDate] = useState('');
  const [planTasks, setPlanTasks] = useState<CreateInterventionTaskPayload[]>([{ ...EMPTY_TASK }]);
  const [saving, setSaving] = useState(false);

  const loadClasses = useCallback(async () => {
    try {
      const data = await getAdvisorClassesApi(apiBase);
      setClasses(data);
    } catch (err) {
      addToast((err as Error).message, 'error', 5000);
    }
  }, [apiBase, addToast]);

  const loadStudents = useCallback(
    async (className?: string) => {
      setLoading(true);
      try {
        const data = await getAdvisorStudentsApi(apiBase, className || undefined);
        setStudents(data);
      } catch (err) {
        addToast((err as Error).message, 'error', 5000);
      } finally {
        setLoading(false);
      }
    },
    [apiBase, addToast]
  );

  useEffect(() => {
    loadClasses();
    loadStudents();
  }, [loadClasses, loadStudents]);

  useEffect(() => {
    loadStudents(selectedClass || undefined);
  }, [selectedClass, loadStudents]);

  const totalStudents = classes.reduce((acc, c) => acc + c.total_students, 0);
  const highRiskTotal = classes.reduce((acc, c) => acc + c.high_risk_count, 0);
  const safeTotal = classes.reduce((acc, c) => acc + c.safe_count, 0);

  const updateTask = (index: number, field: keyof CreateInterventionTaskPayload, value: string) => {
    setPlanTasks((prev) => prev.map((t, i) => (i === index ? { ...t, [field]: value } : t)));
  };

  const handleCreatePlan = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!planTarget) return;
    const validTasks = planTasks.filter((t) => t.title.trim());
    if (validTasks.length === 0) {
      addToast('Vui lòng nhập ít nhất một nhiệm vụ can thiệp.', 'warning');
      return;
    }

    setSaving(true);
    try {
      await createInterventionPlanApi(apiBase, {
        student_id: planTarget.student_id,
        target_completion_date: planDate || undefined,
        advisor_note_summary: planNote || undefined,
        tasks: validTasks,
      });
      addToast(
        `Đã lập kế hoạch can thiệp cho ${planTarget.full_name} (${planTarget.student_code})!`,
        'success'
      );
      setPlanTarget(null);
      setPlanNote('');
      setPlanDate('');
      setPlanTasks([{ ...EMPTY_TASK }]);
      await loadStudents(selectedClass || undefined);
    } catch (err) {
      addToast((err as Error).message, 'error', 6000);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-8 py-4 max-w-7xl mx-auto px-4">
      {/* Header */}
      <div className="flex items-center justify-between gap-3 pb-4 border-b border-slate-800">
        <div>
          <h1 className="text-2xl font-extrabold text-white flex items-center gap-2">
            <UserCheck className="w-6 h-6 text-emerald-400" />
            <span>Phân hệ Cố vấn Học tập</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Lớp sinh hoạt phụ trách &amp; lập kế hoạch can thiệp học tập cho sinh viên
          </p>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold">Sinh viên phụ trách</span>
            <Users className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-white font-mono">{totalStudents}</div>
          <div className="text-[11px] text-slate-400">{classes.length} lớp sinh hoạt</div>
        </div>
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold">Nguy cơ cao</span>
            <AlertTriangle className="w-4 h-4 text-rose-400" />
          </div>
          <div className="text-2xl font-bold text-rose-400 font-mono">{highRiskTotal}</div>
          <div className="text-[11px] text-rose-400/80">Cần can thiệp sớm</div>
        </div>
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold">An toàn</span>
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-emerald-400 font-mono">{safeTotal}</div>
          <div className="text-[11px] text-slate-400">Tiến độ ổn định</div>
        </div>
      </div>

      {/* Classes Overview */}
      <div>
        <h2 className="text-sm font-bold text-white uppercase tracking-wider mb-3">Lớp sinh hoạt</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {classes.length === 0 && !loading && (
            <div className="text-xs text-slate-400">Không có lớp sinh hoạt nào được phân công.</div>
          )}
          {classes.map((cls) => (
            <button
              key={`${cls.class_name}-${cls.academic_year}`}
              type="button"
              onClick={() => setSelectedClass(cls.class_name)}
              className={`p-4 rounded-2xl border text-left transition-all ${
                selectedClass === cls.class_name
                  ? 'bg-emerald-500/10 border-emerald-500/40'
                  : 'bg-slate-900/70 border-slate-800 hover:border-slate-700'
              }`}
            >
              <div className="text-sm font-bold text-white">{cls.class_name}</div>
              <div className="text-[11px] text-slate-400">{cls.academic_year}</div>
              <div className="mt-2 flex items-center gap-3 text-xs">
                <span className="text-slate-300">{cls.total_students} SV</span>
                <span
                  className={`px-2 py-0.5 rounded-md font-semibold ${
                    cls.high_risk_count > 0
                      ? 'bg-rose-500/15 text-rose-300'
                      : 'bg-emerald-500/15 text-emerald-300'
                  }`}
                >
                  {cls.high_risk_count} rủi ro
                </span>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Student Table */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-bold text-white uppercase tracking-wider">
            Danh sách sinh viên {selectedClass && (
              <span className="text-emerald-400">— {selectedClass}</span>
            )}
          </h2>
          <button
            type="button"
            onClick={() => {
              setSelectedClass('');
              loadStudents();
            }}
            className="text-xs text-emerald-400 hover:underline"
          >
            Xem tất cả
          </button>
        </div>

        <div className="overflow-x-auto rounded-2xl border border-slate-800 bg-slate-900/70">
          <table className="w-full text-xs">
            <thead>
              <tr className="text-left text-slate-400 border-b border-slate-800">
                <th className="px-4 py-3 font-semibold">MSSV</th>
                <th className="px-4 py-3 font-semibold">Họ tên</th>
                <th className="px-4 py-3 font-semibold">Lớp</th>
                <th className="px-4 py-3 font-semibold">Xác suất rủi ro</th>
                <th className="px-4 py-3 font-semibold">Trạng thái</th>
                <th className="px-4 py-3 font-semibold">Kế hoạch</th>
                <th className="px-4 py-3 font-semibold text-right">Hành động</th>
              </tr>
            </thead>
            <tbody>
              {loading && (
                <tr>
                  <td colSpan={7} className="px-4 py-10 text-center text-slate-400">
                    <Loader2 className="w-5 h-5 inline animate-spin mr-2" />
                    Đang tải dữ liệu từ máy chủ…
                  </td>
                </tr>
              )}
              {!loading && students.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-4 py-10 text-center text-slate-400">
                    Không có sinh viên nào.
                  </td>
                </tr>
              )}
              {!loading &&
                students.map((s) => {
                  const riskPct = (s.risk_probability * 100).toFixed(1);
                  const highRisk = s.risk_level === 'HIGH_RISK';
                  return (
                    <tr key={s.student_id} className="border-b border-slate-800/60">
                      <td className="px-4 py-3 font-mono text-slate-300">{s.student_code}</td>
                      <td className="px-4 py-3 text-white">{s.full_name}</td>
                      <td className="px-4 py-3 text-slate-400">{s.class_name}</td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <div className="h-1.5 w-16 bg-slate-800 rounded-full overflow-hidden">
                            <div
                              className={`h-full ${highRisk ? 'bg-rose-500' : 'bg-emerald-500'}`}
                              style={{ width: `${Math.min(100, Number(riskPct))}%` }}
                            />
                          </div>
                          <span className={`font-mono ${highRisk ? 'text-rose-400' : 'text-emerald-400'}`}>
                            {riskPct}%
                          </span>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={`px-2 py-0.5 rounded-md font-semibold ${
                            highRisk
                              ? 'bg-rose-500/15 text-rose-300'
                              : 'bg-emerald-500/15 text-emerald-300'
                          }`}
                        >
                          {highRisk ? 'HIGH RISK' : 'SAFE'}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-slate-400">
                        {s.has_active_plan ? (
                          <span className="text-emerald-400">Đang hoạt động</span>
                        ) : (
                          'Chưa có'
                        )}
                        {s.uncompleted_tasks_count > 0 && (
                          <span className="block text-[10px] text-slate-500">
                            {s.uncompleted_tasks_count} việc chưa hoàn thành
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <button
                          type="button"
                          disabled={!highRisk}
                          onClick={() => {
                            setPlanTarget(s);
                            setPlanNote('');
                            setPlanDate('');
                            setPlanTasks([{ ...EMPTY_TASK }]);
                          }}
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 disabled:cursor-not-allowed text-white text-xs font-semibold transition-colors"
                          title={
                            highRisk
                              ? 'Lập kế hoạch can thiệp'
                              : 'Chỉ lập kế hoạch cho sinh viên nguy cơ cao'
                          }
                        >
                          <ClipboardPlus className="w-3.5 h-3.5" />
                          Can thiệp
                        </button>
                      </td>
                    </tr>
                  );
                })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Intervention Plan Modal */}
      {planTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto p-6 shadow-2xl">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="text-lg font-bold text-white">Lập kế hoạch can thiệp</h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  {planTarget.full_name} ({planTarget.student_code}) —{' '}
                  <span className="text-rose-400">
                    nguy cơ {((planTarget.risk_probability || 0) * 100).toFixed(1)}%
                  </span>
                </p>
              </div>
              <button
                type="button"
                onClick={() => setPlanTarget(null)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreatePlan} className="space-y-4 text-xs">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block font-semibold text-slate-300 mb-1">
                    Hạn hoàn thành (ngày):
                  </label>
                  <input
                    type="date"
                    value={planDate}
                    onChange={(e) => setPlanDate(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-700 text-slate-100 focus:border-emerald-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-300 mb-1">
                    Tóm tắt nhận định (Ghi chú):
                  </label>
                  <input
                    type="text"
                    value={planNote}
                    onChange={(e) => setPlanNote(e.target.value)}
                    placeholder="Ví dụ: Sinh viên thụ động trong 2 tuần gần nhất…"
                    className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-700 text-slate-100 focus:border-emerald-500 focus:outline-none"
                  />
                </div>
              </div>

              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-slate-300">Nhiệm vụ can thiệp</span>
                  <button
                    type="button"
                    onClick={() =>
                      setPlanTasks((prev) => [...prev, { ...EMPTY_TASK, priority: 'MEDIUM' }])
                    }
                    className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold border border-slate-700"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    Thêm nhiệm vụ
                  </button>
                </div>

                {planTasks.map((task, idx) => (
                  <div key={idx} className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 space-y-2">
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                      <div>
                        <label className="block text-slate-400 mb-1">Danh mục</label>
                        <select
                          value={task.category}
                          onChange={(e) => updateTask(idx, 'category', e.target.value)}
                          className="w-full px-2.5 py-2 rounded-lg bg-slate-950 border border-slate-700 text-slate-100"
                        >
                          <option value="CHUYEN_CAN">Chuyên cần</option>
                          <option value="HOC_THUAT">Học thuật</option>
                          <option value="TIEN_DO">Tiến độ</option>
                          <option value="TAM_LY">Tâm lý</option>
                        </select>
                      </div>
                      <div>
                        <label className="block text-slate-400 mb-1">Ưu tiên</label>
                        <select
                          value={task.priority}
                          onChange={(e) => updateTask(idx, 'priority', e.target.value)}
                          className="w-full px-2.5 py-2 rounded-lg bg-slate-950 border border-slate-700 text-slate-100"
                        >
                          <option value="HIGH">Cao</option>
                          <option value="MEDIUM">Vừa</option>
                          <option value="LOW">Thấp</option>
                        </select>
                      </div>
                      <div>
                        <label className="block text-slate-400 mb-1">Tiêu đề</label>
                        <input
                          type="text"
                          required
                          value={task.title}
                          onChange={(e) => updateTask(idx, 'title', e.target.value)}
                          placeholder="Tên nhiệm vụ"
                          className="w-full px-2.5 py-2 rounded-lg bg-slate-950 border border-slate-700 text-slate-100 focus:border-emerald-500 focus:outline-none"
                        />
                      </div>
                    </div>
                    <div>
                      <label className="block text-slate-400 mb-1">Mô tả chi tiết</label>
                      <input
                        type="text"
                        value={task.description}
                        onChange={(e) => updateTask(idx, 'description', e.target.value)}
                        placeholder="Mô tả nhiệm vụ"
                        className="w-full px-2.5 py-2 rounded-lg bg-slate-950 border border-slate-700 text-slate-100 focus:border-emerald-500 focus:outline-none"
                      />
                    </div>
                    <div>
                      <label className="block text-slate-400 mb-1">Chỉ số mục tiêu</label>
                      <input
                        type="text"
                        value={task.target_metric}
                        onChange={(e) => updateTask(idx, 'target_metric', e.target.value)}
                        placeholder="VD: Đăng nhập LMS tối thiểu 3 ngày/tuần"
                        className="w-full px-2.5 py-2 rounded-lg bg-slate-950 border border-slate-700 text-slate-100 focus:border-emerald-500 focus:outline-none"
                      />
                    </div>
                  </div>
                ))}
              </div>

              <div className="flex items-center justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setPlanTarget(null)}
                  className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 font-semibold"
                >
                  Hủy bỏ
                </button>
                <button
                  type="submit"
                  disabled={saving}
                  className="inline-flex items-center gap-2 px-5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold shadow-lg shadow-emerald-600/20 disabled:opacity-50"
                >
                  {saving && <Loader2 className="w-4 h-4 animate-spin" />}
                  <Target className="w-4 h-4" />
                  Lưu kế hoạch can thiệp
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};