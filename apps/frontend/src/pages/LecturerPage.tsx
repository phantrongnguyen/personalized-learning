import React, { useCallback, useEffect, useState } from 'react';
import { useApp } from '../state/AppContext';
import { CourseStudentRiskItem, LecturerCourseItem } from '@shared/types';
import {
  getLecturerCoursesApi,
  getCourseRiskBoardApi,
  assignCourseTaskApi,
  alertAdvisorApi,
  AssignCourseTaskPayload,
} from '../services/api';
import {
  BookOpen,
  Loader2,
  AlertTriangle,
  ClipboardPlus,
  BellRing,
  X,
  Siren,
} from 'lucide-react';

export const LecturerPage: React.FC = () => {
  const { apiBase, addToast } = useApp();

  const [courses, setCourses] = useState<LecturerCourseItem[]>([]);
  const [selectedPresentation, setSelectedPresentation] = useState<string>('');
  const [riskBoard, setRiskBoard] = useState<CourseStudentRiskItem[]>([]);
  const [loadingCourses, setLoadingCourses] = useState(true);
  const [loadingBoard, setLoadingBoard] = useState(false);

  // Giao bài tập
  const [assignTarget, setAssignTarget] = useState<CourseStudentRiskItem | null>(null);
  const [taskForm, setTaskForm] = useState<AssignCourseTaskPayload>({
    student_id: '',
    title: '',
    description: '',
    priority: 'HIGH',
    target_metric: 'Hoàn thành bài tập ôn tập môn học',
  });
  const [savingTask, setSavingTask] = useState(false);

  // Cảnh báo GVCN
  const [alertTarget, setAlertTarget] = useState<CourseStudentRiskItem | null>(null);
  const [alertContent, setAlertContent] = useState('');
  const [sendingAlert, setSendingAlert] = useState(false);

  const loadCourses = useCallback(async () => {
    try {
      const data = await getLecturerCoursesApi(apiBase);
      setCourses(data);
      if (data.length > 0) {
        setSelectedPresentation(data[0].presentation_id);
      }
    } catch (err) {
      addToast((err as Error).message, 'error', 5000);
    } finally {
      setLoadingCourses(false);
    }
  }, [apiBase, addToast]);

  const loadRiskBoard = useCallback(
    async (presentationId: string) => {
      setLoadingBoard(true);
      try {
        const data = await getCourseRiskBoardApi(apiBase, presentationId);
        setRiskBoard(data);
      } catch (err) {
        addToast((err as Error).message, 'error', 5000);
      } finally {
        setLoadingBoard(false);
      }
    },
    [apiBase, addToast]
  );

  useEffect(() => {
    loadCourses();
  }, [loadCourses]);

  useEffect(() => {
    if (selectedPresentation) {
      loadRiskBoard(selectedPresentation);
    }
  }, [selectedPresentation, loadRiskBoard]);

  const selectedCourse = courses.find((c) => c.presentation_id === selectedPresentation);
  const highRiskCount = riskBoard.filter((r) => r.risk_status === 'HIGH_RISK').length;

  const handleAssignTask = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!assignTarget || !selectedPresentation) return;
    setSavingTask(true);
    try {
      await assignCourseTaskApi(apiBase, selectedPresentation, {
        ...taskForm,
        student_id: assignTarget.student_id,
      });
      addToast(`Đã giao bài tập bổ trợ cho ${assignTarget.full_name}.`, 'success');
      setAssignTarget(null);
      setTaskForm({ student_id: '', title: '', description: '', priority: 'HIGH', target_metric: '' });
      await loadRiskBoard(selectedPresentation);
    } catch (err) {
      addToast((err as Error).message, 'error', 6000);
    } finally {
      setSavingTask(false);
    }
  };

  const handleAlertAdvisor = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!alertTarget) return;
    setSendingAlert(true);
    try {
      await alertAdvisorApi(apiBase, alertTarget.student_id, {
        subject: `Cảnh báo học tập bất thường môn ${selectedCourse?.code_module || ''}`,
        content: alertContent,
      });
      addToast('Đã gửi cảnh báo học vụ tới Giáo viên chủ nhiệm.', 'success');
      setAlertTarget(null);
      setAlertContent('');
    } catch (err) {
      addToast((err as Error).message, 'error', 6000);
    } finally {
      setSendingAlert(false);
    }
  };

  return (
    <div className="space-y-8 py-4 max-w-7xl mx-auto px-4">
      {/* Header */}
      <div className="flex items-center justify-between gap-3 pb-4 border-b border-slate-800">
        <div>
          <h1 className="text-2xl font-extrabold text-white flex items-center gap-2">
            <BookOpen className="w-6 h-6 text-purple-400" />
            <span>Phân hệ Giảng viên Bộ môn</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Lớp học phần phụ trách &amp; bảng cảnh báo nguy cơ sinh viên
          </p>
        </div>
      </div>

      {/* Course selection */}
      {loadingCourses ? (
        <div className="flex items-center gap-2 text-slate-400 text-sm">
          <Loader2 className="w-4 h-4 animate-spin" />
          Đang tải danh sách học phần…
        </div>
      ) : courses.length === 0 ? (
        <div className="text-xs text-slate-400">
          Bạn chưa được phân công phụ trách học phần nào.
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {courses.map((c) => (
            <button
              key={c.presentation_id}
              type="button"
              onClick={() => setSelectedPresentation(c.presentation_id)}
              className={`p-4 rounded-2xl border text-left transition-all ${
                selectedPresentation === c.presentation_id
                  ? 'bg-purple-500/10 border-purple-500/40'
                  : 'bg-slate-900/70 border-slate-800 hover:border-slate-700'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="text-sm font-bold text-white">{c.code_module}</span>
                <span className="px-2 py-0.5 rounded-md bg-purple-500/15 text-purple-300 text-[10px] font-mono">
                  {c.code_presentation}
                </span>
              </div>
              <div className="text-[11px] text-slate-400 mt-1 truncate">{c.course_name}</div>
              <div className="mt-2 text-xs text-slate-300">
                {c.total_students} sinh viên &bull; {c.module_length} ngày
              </div>
            </button>
          ))}
        </div>
      )}

      {/* Risk board */}
      {selectedPresentation && (
        <div>
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-bold text-white uppercase tracking-wider">
              Bảng cảnh báo nguy cơ{' '}
              <span className="text-purple-400">
                {selectedCourse?.code_module} ({selectedCourse?.code_presentation})
              </span>
            </h2>
            <span
              className={`px-2.5 py-1 rounded-lg text-xs font-bold ${
                highRiskCount > 0
                  ? 'bg-rose-500/15 text-rose-300'
                  : 'bg-emerald-500/15 text-emerald-300'
              }`}
            >
              {highRiskCount} nguy cơ cao
            </span>
          </div>

          <div className="overflow-x-auto rounded-2xl border border-slate-800 bg-slate-900/70">
            <table className="w-full text-xs">
              <thead>
                <tr className="text-left text-slate-400 border-b border-slate-800">
                  <th className="px-4 py-3 font-semibold">MSSV</th>
                  <th className="px-4 py-3 font-semibold">Họ tên</th>
                  <th className="px-4 py-3 font-semibold">Tổng click</th>
                  <th className="px-4 py-3 font-semibold">Nộp trễ</th>
                  <th className="px-4 py-3 font-semibold">Tỷ lệ nộp</th>
                  <th className="px-4 py-3 font-semibold">Rủi ro</th>
                  <th className="px-4 py-3 font-semibold text-right">Hành động</th>
                </tr>
              </thead>
              <tbody>
                {loadingBoard && (
                  <tr>
                    <td colSpan={7} className="px-4 py-10 text-center text-slate-400">
                      <Loader2 className="w-5 h-5 inline animate-spin mr-2" />
                      Đang tải bảng cảnh báo…
                    </td>
                  </tr>
                )}
                {!loadingBoard && riskBoard.length === 0 && (
                  <tr>
                    <td colSpan={7} className="px-4 py-10 text-center text-slate-400">
                      Chưa có dữ liệu dự báo cho học phần này.
                    </td>
                  </tr>
                )}
                {!loadingBoard &&
                  riskBoard.map((s) => {
                    const highRisk = s.risk_status === 'HIGH_RISK';
                    return (
                      <tr key={s.student_id} className="border-b border-slate-800/60">
                        <td className="px-4 py-3 font-mono text-slate-300">{s.student_code}</td>
                        <td className="px-4 py-3 text-white">{s.full_name}</td>
                        <td className="px-4 py-3 text-slate-300">{s.total_clicks}</td>
                        <td className="px-4 py-3 text-slate-300">{s.late_submissions}</td>
                        <td className="px-4 py-3 text-slate-300">
                          {(s.submission_rate * 100).toFixed(0)}%
                        </td>
                        <td className="px-4 py-3">
                          <span
                            className={`px-2 py-0.5 rounded-md font-mono font-semibold ${
                              highRisk
                                ? 'bg-rose-500/15 text-rose-300'
                                : 'bg-emerald-500/15 text-emerald-300'
                            }`}
                          >
                            {(s.risk_probability * 100).toFixed(1)}% —{' '}
                            {highRisk ? 'HIGH' : 'SAFE'}
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center justify-end gap-2">
                            <button
                              type="button"
                              onClick={() => {
                                setAssignTarget(s);
                                setTaskForm({
                                  student_id: s.student_id,
                                  title: '',
                                  description: '',
                                  priority: 'HIGH',
                                  target_metric: 'Hoàn thành bài tập ôn tập môn học',
                                });
                              }}
                              className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-purple-600 hover:bg-purple-500 text-white text-[11px] font-semibold"
                              title="Giao bài tập bổ trợ"
                            >
                              <ClipboardPlus className="w-3.5 h-3.5" />
                              Giao bài
                            </button>
                            <button
                              type="button"
                              onClick={() => {
                                setAlertTarget(s);
                                setAlertContent('');
                              }}
                              className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-[11px] font-semibold"
                              title="Gửi cảnh báo tới GVCN"
                            >
                              <BellRing className="w-3.5 h-3.5" />
                              Báo GVCN
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Assign Task Modal */}
      {assignTarget && (
        <ModalShell title="Giao bài tập bổ trợ môn học" onClose={() => setAssignTarget(null)}>
          <p className="text-xs text-slate-400 mb-4">
            {assignTarget.full_name} ({assignTarget.student_code}) — môn{' '}
            {selectedCourse?.code_module}. Nhiệm vụ sẽ thuộc nhóm{' '}
            <strong className="text-slate-200">HOC_THUAT</strong> của kế hoạch can thiệp đang hoạt động.
          </p>
          <form onSubmit={handleAssignTask} className="space-y-3.5 text-xs">
            <div>
              <label className="block font-semibold text-slate-300 mb-1">Tiêu đề nhiệm vụ:</label>
              <input
                type="text"
                required
                value={taskForm.title}
                onChange={(e) => setTaskForm({ ...taskForm, title: e.target.value })}
                placeholder="VD: Ôn tập chương 4 & nộp bài quiz"
                className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-700 text-slate-100 focus:border-purple-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="block font-semibold text-slate-300 mb-1">Mô tả chi tiết:</label>
              <textarea
                required
                value={taskForm.description}
                onChange={(e) => setTaskForm({ ...taskForm, description: e.target.value })}
                placeholder="Nội dung hướng dẫn làm bài tập…"
                className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-700 text-slate-100 focus:border-purple-500 focus:outline-none"
              />
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="block font-semibold text-slate-300 mb-1">Ưu tiên:</label>
                <select
                  value={taskForm.priority}
                  onChange={(e) =>
                    setTaskForm({ ...taskForm, priority: e.target.value as AssignCourseTaskPayload['priority'] })
                  }
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-700 text-slate-100"
                >
                  <option value="HIGH">Cao</option>
                  <option value="MEDIUM">Vừa</option>
                  <option value="LOW">Thấp</option>
                </select>
              </div>
              <div>
                <label className="block font-semibold text-slate-300 mb-1">Chỉ số mục tiêu:</label>
                <input
                  type="text"
                  value={taskForm.target_metric}
                  onChange={(e) => setTaskForm({ ...taskForm, target_metric: e.target.value })}
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-700 text-slate-100 focus:border-purple-500 focus:outline-none"
                />
              </div>
            </div>
            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => setAssignTarget(null)}
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 font-semibold"
              >
                Hủy
              </button>
              <button
                type="submit"
                disabled={savingTask}
                className="inline-flex items-center gap-2 px-5 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-bold disabled:opacity-50"
              >
                {savingTask && <Loader2 className="w-4 h-4 animate-spin" />}
                <ClipboardPlus className="w-4 h-4" />
                Giao bài tập
              </button>
            </div>
          </form>
        </ModalShell>
      )}

      {/* Alert Advisor Modal */}
      {alertTarget && (
        <ModalShell title="Gửi cảnh báo học vụ tới GVCN" onClose={() => setAlertTarget(null)}>
          <form onSubmit={handleAlertAdvisor} className="space-y-3.5 text-xs">
            <p className="text-slate-400">
              Sinh viên <strong className="text-white">{alertTarget.full_name}</strong> có dấu hiệu
              nguy cơ bất thường khiến GVBM cần chủ nhiệm lớp trao đổi trực tiếp.
            </p>
            <div>
              <label className="block font-semibold text-slate-300 mb-1">Nội dung cảnh báo:</label>
              <textarea
                required
                value={alertContent}
                onChange={(e) => setAlertContent(e.target.value)}
                placeholder="VD: Sinh viên không nộp bài tập TMA đã quá hạn 2 tuần…"
                className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-700 text-slate-100 focus:border-purple-500 focus:outline-none"
              />
            </div>
            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => setAlertTarget(null)}
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 font-semibold"
              >
                Hủy
              </button>
              <button
                type="submit"
                disabled={sendingAlert}
                className="inline-flex items-center gap-2 px-5 py-2 rounded-xl bg-rose-600 hover:bg-rose-500 text-white font-bold disabled:opacity-50"
              >
                {sendingAlert && <Loader2 className="w-4 h-4 animate-spin" />}
                <Siren className="w-4 h-4" />
                Gửi cảnh báo
              </button>
            </div>
          </form>
        </ModalShell>
      )}
    </div>
  );
};

const ModalShell: React.FC<{
  title: string;
  onClose: () => void;
  children: React.ReactNode;
}> = ({ title, onClose, children }) => {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl">
        <div className="flex items-center justify-between mb-1">
          <h3 className="text-lg font-bold text-white flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-purple-400" />
            {title}
          </h3>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        <div className="mt-3">{children}</div>
      </div>
    </div>
  );
};