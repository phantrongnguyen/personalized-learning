import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useApp } from '../state/AppContext';
import {
  StudentCourseItem,
  StudentProfileDetail,
  StudentRiskPrediction,
  StudentRadarData,
  StudentTaskItem,
  StudentHelpRequestItem,
} from '@shared/types';
import {
  getStudentCoursesApi,
  getStudentProfileApi,
  getStudentRiskPredictionApi,
  getStudentRadarApi,
  getStudentTasksApi,
  completeStudentTaskApi,
  getStudentHelpRequestsApi,
  createHelpRequestApi,
} from '../services/api';
import { Avatar } from '../components/common/Avatar';
import {
  GraduationCap,
  Loader2,
  AlertTriangle,
  ShieldCheck,
  CheckCircle2,
  Lightbulb,
  Send,
  ClipboardList,
  HelpCircle,
  ArrowUpRight,
  Mail,
  Phone,
  User,
  CalendarDays,
} from 'lucide-react';

export const StudentPage: React.FC = () => {
  const { apiBase, addToast, user, setCurrentView, studentEnrollmentToOpen, clearStudentEnrollmentToOpen } = useApp();
  const [profile, setProfile] = useState<StudentProfileDetail | null>(null);
  const [profileLoading, setProfileLoading] = useState(true);
  const [profileError, setProfileError] = useState('');

  useEffect(() => {
    let cancelled = false;
    setProfile(null);
    setProfileError('');
    setProfileLoading(true);
    getStudentProfileApi(apiBase).then((data) => {
      if (!cancelled) setProfile(data);
    }).catch((error: Error) => {
      if (!cancelled) setProfileError(error.message);
    }).finally(() => { if (!cancelled) setProfileLoading(false); });
    return () => { cancelled = true; };
  }, [apiBase, user?.email]);

  const [courses, setCourses] = useState<StudentCourseItem[]>([]);
  const [selectedSemester, setSelectedSemester] = useState('');
  const [selectedEnrollment, setSelectedEnrollment] = useState<string>('');
  const selectionRef = useRef(selectedEnrollment);
  selectionRef.current = selectedEnrollment;
  const [prediction, setPrediction] = useState<StudentRiskPrediction | null>(null);
  const [radar, setRadar] = useState<StudentRadarData | null>(null);
  const [tasks, setTasks] = useState<StudentTaskItem[]>([]);
  const [helpRequests, setHelpRequests] = useState<StudentHelpRequestItem[]>([]);

  const [loading, setLoading] = useState(true);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [completingTaskId, setCompletingTaskId] = useState<string | null>(null);

  // Form tạo yêu cầu trợ giúp
  const [showHelpForm, setShowHelpForm] = useState(false);
  const [helpSubject, setHelpSubject] = useState('');
  const [helpContent, setHelpContent] = useState('');
  const [helpTarget, setHelpTarget] = useState<'ADVISOR' | 'LECTURER'>('ADVISOR');
  const [sendingHelp, setSendingHelp] = useState(false);

  const loadCourses = useCallback(async () => {
    try {
      const data = await getStudentCoursesApi(apiBase);
      setCourses(data);
      setSelectedSemester('');
      setSelectedEnrollment(data[0]?.enrollment_id || '');
    } catch (err) {
      addToast((err as Error).message, 'error', 5000);
    } finally {
      setLoading(false);
    }
  }, [apiBase, addToast]);

  const loadTasks = useCallback(async () => {
    try {
      const scope = selectedEnrollment;
      if (!scope) return;
      const data = await getStudentTasksApi(apiBase, scope);
      if (selectionRef.current === scope) setTasks(data);
    } catch (err) {
      addToast((err as Error).message, 'error', 5000);
    }
  }, [apiBase, addToast, selectedEnrollment]);

  const loadHelpRequests = useCallback(async () => {
    try {
      const scope = selectedEnrollment;
      if (!scope) return;
      const data = await getStudentHelpRequestsApi(apiBase, scope);
      if (selectionRef.current === scope) setHelpRequests(data);
    } catch (err) {
      addToast((err as Error).message, 'error', 5000);
    }
  }, [apiBase, addToast, selectedEnrollment]);

  useEffect(() => {
    loadCourses();
  }, [loadCourses]);

  useEffect(() => {
    let cancelled = false;
    setPrediction(null);
    setRadar(null);
    setTasks([]);
    setHelpRequests([]);
    setShowHelpForm(false);
    setHelpSubject('');
    setHelpContent('');
    if (!selectedEnrollment) { setLoadingDetail(false); return; }
    setLoadingDetail(true);
    Promise.allSettled([
      getStudentRiskPredictionApi(apiBase, selectedEnrollment),
      getStudentRadarApi(apiBase, selectedEnrollment),
      getStudentTasksApi(apiBase, selectedEnrollment),
      getStudentHelpRequestsApi(apiBase, selectedEnrollment),
    ]).then(([pred, radarData, courseTasks, courseHelp]) => {
      if (cancelled) return;
      if (pred.status === 'fulfilled') setPrediction(pred.value);
      else addToast((pred.reason as Error).message, 'error', 5000);
      if (radarData.status === 'fulfilled') setRadar(radarData.value);
      else addToast((radarData.reason as Error).message, 'error', 5000);
      if (courseTasks.status === 'fulfilled') setTasks(courseTasks.value);
      else addToast((courseTasks.reason as Error).message, 'error', 5000);
      if (courseHelp.status === 'fulfilled') setHelpRequests(courseHelp.value);
      else addToast((courseHelp.reason as Error).message, 'error', 5000);
      setLoadingDetail(false);
    });
    return () => { cancelled = true; };
  }, [selectedEnrollment, apiBase, addToast]);

  const semesters = useMemo(() => [...new Set(courses.map(course => course.code_presentation))]
    .sort((a, b) => b.localeCompare(a, 'vi', { numeric: true })), [courses]);
  const filteredCourses = useMemo(() => selectedSemester
    ? courses.filter(course => course.code_presentation === selectedSemester)
    : courses, [courses, selectedSemester]);
  const selectedCourse = filteredCourses.find((c) => c.enrollment_id === selectedEnrollment);
  useEffect(() => {
    if (!studentEnrollmentToOpen || loading) return;
    const course = courses.find(item => item.enrollment_id === studentEnrollmentToOpen);
    if (course) {
      setSelectedSemester(course.code_presentation);
      setSelectedEnrollment(course.enrollment_id);
    } else {
      addToast('Không tìm thấy học phần của thông báo.', 'warning');
    }
    clearStudentEnrollmentToOpen();
  }, [studentEnrollmentToOpen, loading, courses, addToast, clearStudentEnrollmentToOpen]);
  const changeSemester = (semester: string) => {
    const matching = semester ? courses.filter(course => course.code_presentation === semester) : courses;
    setSelectedSemester(semester);
    if (!matching.some(course => course.enrollment_id === selectedEnrollment)) {
      const next = matching[0]?.enrollment_id || '';
      setPrediction(null);
      setRadar(null);
      setTasks([]);
      setHelpRequests([]);
      setShowHelpForm(false);
      setLoadingDetail(Boolean(next));
      setSelectedEnrollment(next);
    }
  };
  const upcomingTasks = tasks.filter((t) => !t.is_completed);
  const doneTasks = tasks.filter((t) => t.is_completed);

  const handleCompleteTask = async (task: StudentTaskItem) => {
    setCompletingTaskId(task.id);
    try {
      await completeStudentTaskApi(apiBase, task.id, 'Hoàn thành từ phía sinh viên.', selectedEnrollment);
      window.dispatchEvent(new Event('course-reminders-updated'));
      addToast(`Đã hoàn thành nhiệm vụ: ${task.title}`, 'success');
      await loadTasks();
    } catch (err) {
      addToast((err as Error).message, 'error', 5000);
    } finally {
      setCompletingTaskId(null);
    }
  };

  const handleSendHelpRequest = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedEnrollment) return;
    setSendingHelp(true);
    try {
      await createHelpRequestApi(apiBase, {
        target_role: helpTarget,
        enrollment_id: selectedEnrollment,
        subject: helpSubject,
        content: helpContent,
      });
      addToast('Đã gửi yêu cầu trợ giúp. Giáo viên sẽ phản hồi sớm nhất.', 'success');
      setHelpSubject('');
      setHelpContent('');
      setShowHelpForm(false);
      await loadHelpRequests();
    } catch (err) {
      addToast((err as Error).message, 'error', 5000);
    } finally {
      setSendingHelp(false);
    }
  };

  return (
    <div className="space-y-8 py-4 max-w-7xl mx-auto px-4">
      {/* Header */}
      <div className="flex items-center justify-between gap-3 pb-4 border-b border-slate-800">
        <div>
          <h1 className="text-2xl font-extrabold text-white flex items-center gap-2">
            <GraduationCap className="w-6 h-6 text-cyan-400" />
            <span>Không gian học tập của Sinh viên</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            {user?.name} — theo dõi nguy cơ học tập, nhiệm vụ can thiệp và gửi yêu cầu trợ giúp
          </p>
        </div>
      </div>

      {user && (
        <section aria-labelledby="student-info-heading" aria-busy={profileLoading}
          className="overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/80 shadow-sm">
          <div className="flex flex-col gap-5 border-b border-slate-800 p-5 sm:flex-row sm:items-center sm:justify-between sm:p-6">
            <div className="flex min-w-0 items-center gap-4">
              <Avatar src={user.avatarUrl} initials={user.initials} alt="Ảnh đại diện sinh viên"
                className="h-16 w-16 rounded-full border border-brand-500/30 text-xl sm:h-20 sm:w-20" />
              <div className="min-w-0">
                <h2 id="student-info-heading" className="text-[11px] font-bold uppercase tracking-wider text-brand-400">Thông tin sinh viên</h2>
                <p className="mt-1 break-words text-xl font-bold text-slate-100">{profile?.full_name || user.name}</p>
                <div className="mt-2 flex flex-wrap items-center gap-2 text-xs">
                  <span className="rounded-lg border border-slate-700 bg-slate-950 px-2.5 py-1 font-mono text-slate-300">
                    MSSV: {profile?.student_code || user.studentCode || 'Chưa cập nhật'}
                  </span>
                  <span className="rounded-full bg-brand-500/10 px-2.5 py-1 font-medium text-brand-400">{user.role}</span>
                </div>
              </div>
            </div>
            <button type="button" onClick={() => setCurrentView('profile')}
              className="inline-flex shrink-0 items-center justify-center gap-2 self-start rounded-xl border border-slate-700 px-3 py-2 text-xs font-semibold text-slate-200 transition-colors hover:bg-slate-800 sm:self-center">
              Xem hồ sơ <ArrowUpRight aria-hidden="true" className="h-4 w-4" />
            </button>
          </div>
          <div className="grid gap-5 p-5 sm:p-6 lg:grid-cols-[1fr_auto]">
            <dl className="grid min-w-0 gap-4 sm:grid-cols-3">
              <div className="min-w-0">
                <dt className="flex items-center gap-1.5 text-xs text-slate-400"><Mail aria-hidden="true" className="h-3.5 w-3.5" /> Email</dt>
                <dd className="mt-1.5 break-all text-sm font-medium text-slate-200">{profile?.email || user.email}</dd>
              </div>
              <div>
                <dt className="flex items-center gap-1.5 text-xs text-slate-400"><Phone aria-hidden="true" className="h-3.5 w-3.5" /> Số điện thoại</dt>
                <dd className="mt-1.5 text-sm font-medium text-slate-200">{user.phone || 'Chưa cập nhật'}</dd>
              </div>
              <div>
                <dt className="flex items-center gap-1.5 text-xs text-slate-400"><User aria-hidden="true" className="h-3.5 w-3.5" /> Giới tính</dt>
                <dd className="mt-1.5 text-sm font-medium text-slate-200">
                  {profileLoading ? 'Đang tải…' : profile?.gender === 'M' ? 'Nam' : profile?.gender === 'F' ? 'Nữ' : 'Chưa cập nhật'}
                </dd>
              </div>
            </dl>
            <dl className="grid grid-cols-2 gap-3 lg:min-w-56">
              <div className="rounded-xl bg-slate-950 px-4 py-3">
                <dt className="text-[11px] text-slate-400">Học phần đăng ký</dt>
                <dd className="mt-1 text-2xl font-bold text-brand-400">{loading ? '—' : courses.length}</dd>
              </div>
              <div className="rounded-xl bg-slate-950 px-4 py-3">
                <dt className="text-[11px] text-slate-400">Tín chỉ đăng ký</dt>
                <dd className="mt-1 text-2xl font-bold text-cyan-400">{profileLoading || !profile ? '—' : profile.studied_credits_total}</dd>
              </div>
            </dl>
          </div>
          {profileError && <p role="alert" className="px-5 pb-4 text-xs text-rose-400 sm:px-6">{profileError}</p>}
        </section>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left: Course list */}
        <div className="lg:col-span-4 space-y-4">
          <div className="flex items-center justify-between gap-2">
            <h2 className="text-sm font-bold text-white uppercase tracking-wider">Môn học của tôi</h2>
          </div>
          <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
            <label htmlFor="student-semester" className="mb-2 flex items-center gap-2 text-xs font-semibold text-slate-300">
              <CalendarDays aria-hidden="true" className="h-4 w-4 text-cyan-400" /> Học kỳ
            </label>
            <select id="student-semester" value={selectedSemester} onChange={event => changeSemester(event.target.value)}
              disabled={loading || courses.length === 0 || sendingHelp || completingTaskId !== null}
              className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2.5 text-sm text-slate-100 focus:border-cyan-500 focus:outline-none disabled:cursor-not-allowed disabled:opacity-50">
              <option value="">{loading ? 'Đang tải học kỳ…' : 'Tất cả học kỳ'}</option>
              {semesters.map(semester => <option key={semester} value={semester}>{semester}</option>)}
            </select>
          </div>
          {loading ? (
            <div className="flex items-center gap-2 text-slate-400 text-sm">
              <Loader2 className="w-4 h-4 animate-spin" />
              Đang tải…
            </div>
          ) : filteredCourses.length === 0 ? (
            <div className="text-xs text-slate-400">{courses.length === 0 ? 'Chưa có môn học được đăng ký.' : 'Không có môn học trong học kỳ này.'}</div>
          ) : (
            <div className="space-y-2.5">
              {filteredCourses.map((c) => (
                <button
                  key={c.enrollment_id}
                  type="button"
                  disabled={sendingHelp || completingTaskId !== null}
                  onClick={() => setSelectedEnrollment(c.enrollment_id)}
                  className={`w-full p-4 rounded-2xl border text-left transition-all ${
                    selectedEnrollment === c.enrollment_id
                      ? 'bg-cyan-500/10 border-cyan-500/40'
                      : 'bg-slate-900/70 border-slate-800 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-bold text-white">{c.code_module}</span>
                    <span className="px-2 py-0.5 rounded-md bg-cyan-500/15 text-cyan-300 text-[10px] font-mono">
                      {c.code_presentation}
                    </span>
                  </div>
                  <div className="text-[11px] text-slate-400 mt-1 truncate">{c.course_name}</div>
                  <div className="mt-1 text-[11px] text-slate-300">
                    {c.studied_credits} tín chỉ
                    {c.final_result && <span className="text-brand-400"> — {c.final_result}</span>}
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Right: Risk details */}
        <div className="lg:col-span-8 space-y-6">
          {loadingDetail ? (
            <div className="flex items-center gap-2 text-slate-400 text-sm p-8">
              <Loader2 className="w-4 h-4 animate-spin" />
              Đang tải dự báo tại mốc Cutoff 75%…
            </div>
          ) : prediction ? (
            <>
              {/* Risk card */}
              <div
                className={`p-6 rounded-2xl border shadow-xl ${
                  prediction.risk_level === 'HIGH_RISK'
                    ? 'bg-rose-950/40 border-rose-500/40'
                    : 'bg-brand-950/40 border-brand-500/40'
                }`}
              >
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                  <div>
                    <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
                      Dự báo nguy cơ học tập —{' '}
                      {selectedCourse?.code_module} ({selectedCourse?.course_name})
                    </div>
                    <div className="mt-2 flex items-center gap-3">
                      {prediction.risk_level === 'HIGH_RISK' ? (
                        <AlertTriangle className="w-8 h-8 text-rose-400" />
                      ) : (
                        <ShieldCheck className="w-8 h-8 text-brand-400" />
                      )}
                      <div>
                        <div
                          className={`text-2xl font-extrabold ${
                            prediction.risk_level === 'HIGH_RISK'
                              ? 'text-rose-400'
                              : 'text-brand-400'
                          }`}
                        >
                          {(prediction.risk_probability * 100).toFixed(1)}%
                        </div>
                        <div className="text-[11px] text-slate-400">
                          Xác suất trượt / không đạt học phần
                        </div>
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <span
                      className={`px-3 py-1.5 rounded-lg text-xs font-bold ${
                        prediction.risk_level === 'HIGH_RISK'
                          ? 'bg-rose-500/20 text-rose-300'
                          : 'bg-brand-500/20 text-brand-300'
                      }`}
                    >
                      {prediction.risk_level === 'HIGH_RISK' ? 'NGUY CƠ CAO' : 'AN TOÀN'}
                    </span>
                    {prediction.data_source === 'synthetic_demo' && (
                      <p className="text-xs text-amber-300 mt-2">Dự báo từ dữ liệu minh họa</p>
                    )}
                    <div className="text-[10px] text-slate-500 mt-2 font-mono">
                      {prediction.cutoff_stage} &bull; {prediction.model_version}
                    </div>
                  </div>
                </div>
              </div>

              {/* Recommendations */}
              {prediction.pedagogical_recommendations.length > 0 && (
                <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800">
                  <h3 className="text-sm font-bold text-white flex items-center gap-2 mb-3">
                    <Lightbulb className="w-4 h-4 text-amber-400" />
                    Khuyến nghị theo nguy cơ và chỉ số học tập
                  </h3>
                  <ul className="space-y-2 text-xs">
                    {prediction.pedagogical_recommendations.map((rec, i) => (
                      <li key={i} className="flex items-start gap-2 text-slate-300">
                        <CheckCircle2 className="w-4 h-4 text-brand-400 shrink-0 mt-0.5" />
                        <span>{rec}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </>
          ) : (
            <div className="p-8 rounded-2xl bg-slate-900/60 border border-slate-800 border-dashed text-center text-slate-400 text-sm">
              {selectedEnrollment ? "Môn học chưa có kết quả dự báo." : "Chọn một môn học để xem dự báo và radar."}
            </div>
          )}
          {!loadingDetail && radar && <Radar6DCard radar={radar} />}
          {!loadingDetail && selectedEnrollment && !radar && (
            <p className="text-sm text-slate-400">Môn học chưa có dữ liệu radar.</p>
          )}
        </div>
      </div>

      {/* Tasks */}
      <div>
        <h2 className="text-sm font-bold text-white uppercase tracking-wider mb-3 flex items-center gap-2">
          <ClipboardList className="w-4 h-4 text-brand-400" />
          Nhiệm vụ can thiệp — {selectedCourse?.code_module || 'chưa chọn môn'}
        </h2>
        {loadingDetail && <p className="text-xs text-slate-400">Đang tải nhiệm vụ của môn học…</p>}
        {!loadingDetail && upcomingTasks.length === 0 && (
          <div className="text-xs text-slate-400">
            {selectedEnrollment ? 'Môn học này chưa có nhiệm vụ đang chờ.' : 'Chọn môn học để xem nhiệm vụ.'}
          </div>
        )}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {upcomingTasks.map((t) => (
            <div key={t.id} className="p-4 rounded-2xl bg-slate-900/70 border border-slate-800">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <span
                    className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded-md ${
                      t.priority === 'HIGH'
                        ? 'bg-rose-500/15 text-rose-300'
                        : t.priority === 'MEDIUM'
                        ? 'bg-amber-500/15 text-amber-300'
                        : 'bg-brand-500/15 text-brand-300'
                    }`}
                  >
                    {t.priority}
                  </span>
                  <h4 className="mt-2 text-sm font-bold text-white">{t.title}</h4>
                  <p className="text-xs text-slate-400 mt-1">{t.description}</p>
                  {t.target_metric && (
                    <div className="text-[11px] text-brand-400 mt-2">
                      Chỉ số mục tiêu: <strong>{t.target_metric}</strong>
                    </div>
                  )}
                </div>
              </div>
              <button
                type="button"
                disabled={completingTaskId === t.id}
                onClick={() => handleCompleteTask(t)}
                className="mt-3 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white text-xs font-semibold"
              >
                {completingTaskId === t.id ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <CheckCircle2 className="w-3.5 h-3.5" />
                )}
                Đánh dấu hoàn thành
              </button>
            </div>
          ))}
        </div>

        {doneTasks.length > 0 && (
          <>
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mt-6 mb-2">
              Đã hoàn thành ({doneTasks.length})
            </h3>
            <div className="flex flex-wrap gap-2">
              {doneTasks.map((t) => (
                <span
                  key={t.id}
                  className="px-3 py-1.5 rounded-lg bg-slate-900/60 border border-slate-800 text-xs text-slate-400 line-through"
                >
                  {t.title}
                </span>
              ))}
            </div>
          </>
        )}
      </div>

      {/* Help requests */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
            <HelpCircle className="w-4 h-4 text-cyan-400" />
            Yêu cầu trợ giúp — {selectedCourse?.code_module || 'chưa chọn môn'}
          </h2>
          <button
            type="button"
            disabled={!selectedEnrollment || loadingDetail || sendingHelp}
            onClick={() => setShowHelpForm((v) => !v)}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold"
          >
            <Send className="w-3.5 h-3.5" />
            Gửi yêu cầu mới
          </button>
        </div>

        {showHelpForm && (
          <form
            onSubmit={handleSendHelpRequest}
            className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-3 mb-4 text-xs"
          >
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="block font-semibold text-slate-300 mb-1">Gửi tới:</label>
                <select
                  value={helpTarget}
                  onChange={(e) => setHelpTarget(e.target.value as 'ADVISOR' | 'LECTURER')}
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-700 text-slate-100"
                >
                  <option value="ADVISOR">Giáo viên chủ nhiệm (GVCN)</option>
                  <option value="LECTURER">Giảng viên bộ môn (GVBM)</option>
                </select>
              </div>
              <div>
                <label className="block font-semibold text-slate-300 mb-1">Tiêu đề:</label>
                <input
                  type="text"
                  required
                  value={helpSubject}
                  onChange={(e) => setHelpSubject(e.target.value)}
                  placeholder="VD: Xin lịch tư vấn phương pháp ôn thi"
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-700 text-slate-100 focus:border-cyan-500 focus:outline-none"
                />
              </div>
            </div>
            <div>
              <label className="block font-semibold text-slate-300 mb-1">Nội dung:</label>
              <textarea
                required
                value={helpContent}
                onChange={(e) => setHelpContent(e.target.value)}
                placeholder="Mô tả vấn đề bạn đang gặp phải…"
                className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-700 text-slate-100 focus:border-cyan-500 focus:outline-none"
              />
            </div>
            <div className="flex justify-end">
              <button
                type="submit"
                disabled={sendingHelp}
                className="inline-flex items-center gap-2 px-5 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-bold disabled:opacity-50"
              >
                {sendingHelp && <Loader2 className="w-4 h-4 animate-spin" />}
                Gửi yêu cầu
              </button>
            </div>
          </form>
        )}

        {loadingDetail ? (
          <p className="text-xs text-slate-400">Đang tải yêu cầu trợ giúp của môn học…</p>
        ) : helpRequests.length === 0 ? (
          <div className="text-xs text-slate-400">Môn học này chưa có yêu cầu trợ giúp.</div>
        ) : (
          <div className="space-y-2.5">
            {helpRequests.map((r) => (
              <div key={r.id} className="p-4 rounded-2xl bg-slate-900/70 border border-slate-800">
                <div className="flex items-center justify-between gap-3">
                  <div className="text-xs font-bold text-white">{r.subject}</div>
                  <span
                    className={`px-2 py-0.5 rounded-md text-[10px] font-semibold ${
                      r.status === 'RESOLVED'
                        ? 'bg-brand-500/15 text-brand-300'
                        : r.status === 'IN_PROGRESS'
                        ? 'bg-amber-500/15 text-amber-300'
                        : 'bg-slate-800 text-slate-300'
                    }`}
                  >
                    {r.status}
                  </span>
                </div>
                <p className="text-xs text-slate-400 mt-1">{r.content}</p>
                <div className="text-[10px] text-slate-500 mt-1.5">
                  Gửi tới {r.target_role} &bull;{' '}
                  {new Date(r.created_at).toLocaleString('vi-VN')}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

/**
 * Biểu đồ Radar đối sánh năng lực 6D lấy trực tiếp từ dữ liệu
 * /api/v1/student/courses/{id}/radar của Backend.
 */
const Radar6DCard: React.FC<{ radar: StudentRadarData }> = ({ radar }) => {
  const dims = radar.dimensions;

  const chart = useMemo(() => {
    const n = dims.length;
    const maxR = 100;
    const cx = 120;
    const cy = 110;
    const pt = (value: number, index: number): [number, number] => {
      const angle = (2 * Math.PI * index) / n - Math.PI / 2;
      const r = Math.max(4, Math.min(maxR, value));
      return [cx + r * Math.cos(angle), cy + r * Math.sin(angle)];
    };
    const poly = (values: number[]) =>
      values.map((v, i) => pt(v, i).join(',')).join(' ');
    return { pt, poly, cx, cy, maxR };
  }, [dims]);

  if (dims.length === 0) return null;

  return (
    <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800">
      <h3 className="text-sm font-bold text-white mb-1">
        Đối sánh năng lực 6D{' '}
        <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-400">
          Radar
        </span>
      </h3>
      <p className="text-xs text-slate-400 mb-3">
        {radar.code_module} so với mức chuẩn của nhóm sinh viên Khá/Giỏi
      </p>

      {radar.data_source === 'synthetic_demo' && (
        <p className="text-xs text-amber-300 mb-3">Dữ liệu học tập minh họa</p>
      )}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-center">
        <svg viewBox="0 0 240 220" className="w-full max-w-xs mx-auto">
          <g>
            {[25, 50, 75, 100].map((lvl) => (
              <polygon
                key={lvl}
                points={dims.map((_, i) => chart.pt(lvl, i).join(',')).join(' ')}
                fill={lvl === 100 ? 'rgba(15,23,42,0.4)' : 'none'}
                stroke="#1e293b"
                strokeWidth="1"
                strokeDasharray={lvl === 100 ? 'none' : '3,3'}
              />
            ))}
            {dims.map((_, i) => {
              const [x, y] = chart.pt(100, i);
              return (
                <line key={i} x1={chart.cx} y1={chart.cy} x2={x} y2={y} stroke="#334155" strokeWidth="1" />
              );
            })}
            <polygon
              points={dims.map((_, i) => chart.pt(100, i).join(',')).join(' ')}
              fill="rgba(59,130,246,0.12)"
              stroke="#60a5fa"
              strokeWidth="2"
              strokeDasharray="5,4"
            />
            <polygon
              points={dims.map((_, i) => chart.pt(dims[i].percentile, i).join(',')).join(' ')}
              fill="rgba(34,211,238,0.2)"
              stroke="#22d3ee"
              strokeWidth="2"
            />
            {dims.map((d, i) => {
              const [x, y] = chart.pt(d.percentile, i);
              return <circle key={i} cx={x} cy={y} r="4" fill="#22d3ee" stroke="#0f172a" strokeWidth="1.5" />;
            })}
          </g>
        </svg>

        <div className="space-y-2.5">
          {dims.map((d) => (
            <div key={d.metric} className="space-y-1">
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-300 font-medium">{d.metric}</span>
                <span className="text-slate-400 font-mono">
                  {d.percentile.toFixed(0)}%
                </span>
              </div>
              <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full ${d.percentile < 50 ? 'bg-rose-500' : 'bg-cyan-400'}`}
                  style={{ width: `${Math.min(100, d.percentile)}%` }}
                />
              </div>
            </div>
          ))}
          <div className="flex items-center gap-4 pt-1 text-[11px] text-slate-400">
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-cyan-400" /> Tôi
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full border border-blue-400 border-dashed bg-blue-400/30" /> Chuẩn giỏi
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
