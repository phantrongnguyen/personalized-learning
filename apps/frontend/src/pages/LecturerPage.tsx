import React, { useCallback, useEffect, useId, useRef, useState } from 'react';
import { SuggestionReview } from '../components/lecturer/SuggestionReview';
import { useApp } from '../state/AppContext';
import { CourseStudentRiskItem, CourseSuggestionResponse, LecturerCourseItem } from '@shared/types';
import {
  getLecturerCoursesApi,
  getCourseRiskBoardApi,
  getCourseSuggestionsApi,
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
  const [suggestionDetail, setSuggestionDetail] = useState<CourseSuggestionResponse | null>(null);
  const [loadingSuggestions, setLoadingSuggestions] = useState(false);
  const suggestionRequest = useRef(0);
  const [suggestionError, setSuggestionError] = useState('');
  const [verifiedBasis, setVerifiedBasis] = useState('');
  const [selectedRuleId, setSelectedRuleId] = useState<string | null>(null);
  const [learningLevel, setLearningLevel] = useState<'FOUNDATION' | 'GUIDED' | 'APPLICATION' | ''>('');

  // Cảnh báo GVCN
  const [alertTarget, setAlertTarget] = useState<CourseStudentRiskItem | null>(null);
  const [alertContent, setAlertContent] = useState('');
  const [sendingAlert, setSendingAlert] = useState(false);

  const loadCourses = useCallback(async () => {
    try {
      const data = await getLecturerCoursesApi(apiBase);
      setCourses(data);
      if (data.length > 0) {
        const largestCourse = data.reduce((largest, course) =>
          course.total_students > largest.total_students ? course : largest, data[0]);
        setSelectedPresentation(largestCourse.presentation_id);
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
        setRiskBoard([...data].sort((left, right) => {
          const leftRisk = left.risk_status === 'HIGH_RISK' ? 1 : 0;
          const rightRisk = right.risk_status === 'HIGH_RISK' ? 1 : 0;
          return rightRisk - leftRisk ||
            (right.risk_probability ?? -1) - (left.risk_probability ?? -1);
        }));
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
  const notPredictedCount = riskBoard.filter((r) => r.risk_status === 'NOT_PREDICTED').length;

  const openAssignment = async (student: CourseStudentRiskItem) => {
    const request = ++suggestionRequest.current;
    setAssignTarget(student);
    setSuggestionDetail(null);
    setSuggestionError('');
    setVerifiedBasis('');
    setSelectedRuleId(null);
    setLearningLevel('');
    setTaskForm({ student_id: student.student_id, title: '', description: '', priority: 'MEDIUM', target_metric: '' });
    setLoadingSuggestions(true);
    try {
      const detail = await getCourseSuggestionsApi(apiBase, selectedPresentation, student.student_id);
      if (request === suggestionRequest.current) setSuggestionDetail(detail);
    } catch (err) {
      if (request === suggestionRequest.current) setSuggestionError((err as Error).message);
    } finally {
      if (request === suggestionRequest.current) setLoadingSuggestions(false);
    }
  };

  const handleAssignTask = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!assignTarget || !selectedPresentation || !suggestionDetail?.assignment.can_assign) return;
    if ((suggestionDetail.status !== 'available' || !selectedRuleId) && !verifiedBasis.trim()) {
      addToast('Hãy ghi căn cứ đã tự xác minh trước khi giao nhiệm vụ.', 'error');
      return;
    }
    setSavingTask(true);
    try {
      const learningLabel = learningLevel === 'FOUNDATION' ? 'Củng cố nền tảng'
        : learningLevel === 'GUIDED' ? 'Luyện tập có hướng dẫn'
          : learningLevel === 'APPLICATION' ? 'Vận dụng mở rộng' : '';
      const description = [taskForm.description.trim(),
        learningLabel ? `Mức bài tập do giảng viên chọn: ${learningLabel}` : '',
        verifiedBasis.trim() ? `Căn cứ giảng viên đã xác minh: ${verifiedBasis.trim()}` : '',
      ].filter(Boolean).join('\n\n');
      await assignCourseTaskApi(apiBase, selectedPresentation, {
        ...taskForm,
        description,
        student_id: assignTarget.student_id,
      });
      addToast(`Đã giao bài tập bổ trợ cho ${assignTarget.full_name}.`, 'success');
      setAssignTarget(null);
      setTaskForm({ student_id: '', title: '', description: '', priority: 'MEDIUM', target_metric: '' });
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
        presentation_id: selectedPresentation,
        subject: `Trao đổi tình hình học tập môn ${selectedCourse?.code_module || ''}`,
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
              onClick={() => { suggestionRequest.current++; setAssignTarget(null); setSuggestionDetail(null); setSelectedPresentation(c.presentation_id); }}
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
                  : 'bg-brand-500/15 text-brand-300'
              }`}
            >
              {highRiskCount} nguy cơ cao · {notPredictedCount} chưa dự báo
            </span>
          </div>

          <p className="text-xs text-slate-400">Tổng click là số lượt tương tác được ghi trong dữ liệu gốc đến mốc đánh giá; không đo thời gian hay mức hiểu bài.</p>
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
                      Chưa có sinh viên đăng ký học phần này.
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
                        <td className="px-4 py-3 text-slate-300">{s.total_clicks ?? "—"}</td>
                        <td className="px-4 py-3 text-slate-300">{s.late_submissions ?? "—"}</td>
                        <td className="px-4 py-3 text-slate-300">
                          {s.submission_rate == null ? "—" : `${(s.submission_rate * 100).toFixed(0)}%`}
                        </td>
                        <td className="px-4 py-3">
                          <span
                            className={`px-2 py-0.5 rounded-md font-mono font-semibold ${
                              highRisk
                                ? 'bg-rose-500/15 text-rose-300'
                                : s.risk_status === 'NOT_PREDICTED'
                                  ? 'bg-slate-500/15 text-slate-400'
                                  : 'bg-brand-500/15 text-brand-300'
                            }`}
                          >
                            {s.risk_probability === null ? 'Chưa dự báo' : `${(s.risk_probability * 100).toFixed(1)}% — ${highRisk ? 'Cần theo dõi' : 'Dưới ngưỡng'}`}
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center justify-end gap-2">
                            <button
                              type="button"
                              onClick={() => { void openAssignment(s); }}
                              className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-purple-600 hover:bg-purple-500 text-white text-[11px] font-semibold"
                              title="Xem gợi ý và soạn nháp"
                            >
                              <ClipboardPlus className="w-3.5 h-3.5" />
                              Xem gợi ý
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
        <ModalShell title="Gợi ý hỗ trợ sinh viên" wide onClose={() => { suggestionRequest.current++; setAssignTarget(null); }}>
          <p className="text-sm text-slate-400 mb-4">
            {assignTarget.full_name} ({assignTarget.student_code}) — môn {selectedCourse?.code_module}
          </p>
          {loadingSuggestions && <p className="text-xs text-slate-400 mb-3">Đang tải căn cứ…</p>}
          {suggestionError && <p className="text-xs text-rose-300 mb-3">{suggestionError}</p>}
          {suggestionDetail && <SuggestionReview key={`${selectedPresentation}-${assignTarget.student_id}`} detail={suggestionDetail}
            student={assignTarget} selectedRuleId={selectedRuleId} onChoose={(suggestion) => {
            setSelectedRuleId(suggestion.rule_id);
            setTaskForm({
              ...taskForm, title: suggestion.title, description: suggestion.proposed_action,
              target_metric: 'Xác minh tiến độ cùng sinh viên',
            });
          }}>
          {suggestionDetail.assignment.can_assign && <form onSubmit={handleAssignTask} className="space-y-3.5 text-xs">
            {(suggestionDetail.status !== 'available' || !selectedRuleId) && <div>
              <label className="block font-semibold text-slate-300 mb-1" htmlFor="verified-basis">Điều giảng viên đã tự xác minh (bắt buộc):</label>
              <textarea id="verified-basis" required value={verifiedBasis} onChange={(e) => setVerifiedBasis(e.target.value)}
                placeholder="VD: Đã trao đổi với sinh viên về phần kiến thức cần ôn. Không suy đoán từ tỷ lệ dự báo."
                className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-700 text-slate-100" />
              <p className="text-slate-400 mt-1">Căn cứ này sẽ được lưu trong mô tả nhiệm vụ và sinh viên có thể đọc được.</p>
            </div>}
            <div>
              <label className="block font-semibold text-slate-300 mb-1">Tiêu đề nhiệm vụ:</label>
              <input
                type="text"
                required
                value={taskForm.title}
                onChange={(e) => setTaskForm({ ...taskForm, title: e.target.value })}
                placeholder="VD: Xác minh tiến độ học và đề xuất hỗ trợ"
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
                <label className="block font-semibold text-slate-300 mb-1" htmlFor="task-target-metric">Chỉ số mục tiêu:</label>
                <input
                  type="text"
                  id="task-target-metric"
                  value={taskForm.target_metric}
                  onChange={(e) => setTaskForm({ ...taskForm, target_metric: e.target.value })}
                  placeholder="Ví dụ: hoàn thành 2/3 bài ôn tập trước buổi học sau"
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-700 text-slate-100 focus:border-purple-500 focus:outline-none"
                />
              </div>
            </div>
            <p className="text-slate-400">Chỉ số mục tiêu là kết quả có thể kiểm tra sau khi giao (ví dụ: số bài hoàn thành), không phải điểm dự báo hay mức độ nghiêm trọng.</p>
            <details className="rounded-xl border border-slate-700 bg-slate-950/60 p-3 text-slate-200">
              <summary className="cursor-pointer font-semibold text-sm">Chọn mức bài tập phù hợp (tùy chọn)</summary>
              <section className="mt-3 space-y-2">
              <p>Đây là độ khó của nhiệm vụ giảng viên dự định giao, không phải xếp hạng năng lực sinh viên hay mức nghiêm trọng do mô hình quyết định.</p>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2" aria-label="Các chỉ số tổng hợp cần đối chiếu">
                <p>Lượt hoạt động: <strong>{assignTarget.total_clicks ?? 'Chưa có'}</strong></p>
                <p>Lượt nộp trễ: <strong>{assignTarget.late_submissions ?? 'Chưa có'}</strong></p>
                <p>Tỷ lệ nộp: <strong>{assignTarget.submission_rate == null ? 'Chưa có' : `${(assignTarget.submission_rate * 100).toFixed(0)}%`}</strong></p>
              </div>
              <p className="text-slate-400">Các số liệu này cần được đối chiếu với nguồn học tập; chúng không cho biết điểm số, bài nào trễ hay kiến thức nào còn thiếu.</p>
              <p>{suggestionDetail?.status === 'available'
                ? 'Có gợi ý hỗ trợ dựa trên căn cứ hiện có; vẫn cần đối chiếu kết quả học và trao đổi với sinh viên.'
                : 'Dữ liệu hiện chưa đủ để hệ thống đưa ra gợi ý hỗ trợ. Hãy xác minh kiến thức và nhu cầu hỗ trợ với sinh viên trước khi chọn.'}</p>
              <label className="block font-semibold" htmlFor="learning-level">Mức bài tập (giảng viên tự chọn, không bắt buộc):</label>
              <select id="learning-level" value={learningLevel} onChange={(e) => setLearningLevel(e.target.value as typeof learningLevel)}
                className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-slate-100">
                <option value="">Chưa xác định</option>
                <option value="FOUNDATION">Củng cố nền tảng</option>
                <option value="GUIDED">Luyện tập có hướng dẫn</option>
                <option value="APPLICATION">Vận dụng mở rộng</option>
              </select>
              {learningLevel && <p className="text-slate-300">{learningLevel === 'FOUNDATION'
                ? 'Nên bắt đầu bằng bài ngắn kiểm tra kiến thức nền và hướng dẫn từng bước.'
                : learningLevel === 'GUIDED'
                  ? 'Nên dùng ví dụ mẫu, bài luyện tập tương tự và phản hồi sau mỗi bước.'
                  : 'Nên dùng bài vận dụng tình huống và yêu cầu giải thích cách làm.'}</p>}
              <p className="text-slate-400">Mức đã chọn sẽ được ghi trong mô tả nhiệm vụ và sinh viên có thể xem. Nó không thay đổi độ ưu tiên hoặc dự báo model.</p>
              </section>
            </details>
            <div className="flex flex-wrap items-center justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => { suggestionRequest.current++; setAssignTarget(null); }}
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
          </form>}
          </SuggestionReview>}
        </ModalShell>
      )}

      {/* Alert Advisor Modal */}
      {alertTarget && (
        <ModalShell title="Gửi cảnh báo học vụ tới GVCN" onClose={() => setAlertTarget(null)}>
          <form onSubmit={handleAlertAdvisor} className="space-y-3.5 text-xs">
            <p className="text-slate-400">
              Nếu cần thêm thông tin, hãy trao đổi với cố vấn về sinh viên <strong className="text-white">{alertTarget.full_name}</strong>.
              Chỉ ghi điều đã xác minh; không kết luận từ số liệu tổng hợp.
            </p>
            <div>
              <label className="block font-semibold text-slate-300 mb-1">Nội dung cảnh báo:</label>
              <textarea
                required
                value={alertContent}
                onChange={(e) => setAlertContent(e.target.value)}
                placeholder="VD: Đề nghị xác minh tiến độ và nhu cầu hỗ trợ của sinh viên…"
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
  wide?: boolean;
}> = ({ title, onClose, children, wide = false }) => {
  const dialogRef = useRef<HTMLDivElement>(null);
  const titleId = useId();
  const closeRef = useRef(onClose);
  closeRef.current = onClose;

  useEffect(() => {
    const previousFocus = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    const dialog = dialogRef.current;
    const closeButton = dialog?.querySelector<HTMLButtonElement>('button[aria-label="Đóng"]');
    closeButton?.focus();

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        event.preventDefault();
        closeRef.current();
      }
      if (event.key !== 'Tab' || !dialog) return;
      const focusable = Array.from(dialog.querySelectorAll<HTMLElement>(
        'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
      )).filter((element) => element.getClientRects().length > 0);
      if (!focusable.length) {
        event.preventDefault();
        dialog.focus();
        return;
      }
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (event.shiftKey && (document.activeElement === first || !dialog.contains(document.activeElement))) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && (document.activeElement === last || !dialog.contains(document.activeElement))) {
        event.preventDefault();
        first.focus();
      }
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      previousFocus?.focus();
    };
  }, []);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
      <div ref={dialogRef} role="dialog" aria-modal="true" aria-labelledby={titleId} tabIndex={-1} className={`bg-slate-900 border border-slate-800 rounded-2xl ${wide ? 'max-w-2xl' : 'max-w-lg'} w-full max-h-[calc(100dvh-2rem)] overflow-y-auto p-6 shadow-2xl`}>
        <div className="flex items-center justify-between mb-1">
          <h3 id={titleId} className="text-lg font-bold text-white flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-purple-400" />
            {title}
          </h3>
          <button
            type="button"
            onClick={onClose}
            aria-label="Đóng"
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
