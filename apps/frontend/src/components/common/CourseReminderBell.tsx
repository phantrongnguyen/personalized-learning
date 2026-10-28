import React, { useEffect, useId, useRef, useState } from 'react';
import { Bell, CheckCheck, ChevronRight, Loader2, RefreshCw } from 'lucide-react';
import { CourseReminder } from '@shared/types';
import { useApp } from '../../state/AppContext';
import { getCourseRemindersApi } from '../../services/api';

export const CourseReminderBell: React.FC = () => {
  const { user, apiBase, currentView, openStudentEnrollment } = useApp();
  const storageKey = `edurisk_reminders_read:${user?.email || ''}`;
  const [readIds, setReadIds] = useState<string[]>(() => {
    try {
      const value: unknown = JSON.parse(localStorage.getItem(storageKey) || '[]');
      return Array.isArray(value) ? value.filter((id): id is string => typeof id === 'string').slice(-500) : [];
    } catch { return []; }
  });
  const [reminders, setReminders] = useState<CourseReminder[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [open, setOpen] = useState(false);
  const [revision, setRevision] = useState(0);
  const root = useRef<HTMLDivElement>(null);
  const trigger = useRef<HTMLButtonElement>(null);
  const panel = useRef<HTMLDivElement>(null);
  const id = useId();
  const unread = reminders.filter(reminder => !readIds.includes(reminder.id)).length;

  useEffect(() => { setOpen(false); }, [currentView]);

  useEffect(() => {
    let cancelled = false;
    let running = false;
    const controller = new AbortController();
    const refresh = async () => {
      if (running || cancelled) return;
      running = true;
      try {
        const data = await getCourseRemindersApi(apiBase, controller.signal);
        if (!cancelled) { setReminders(data); setError(''); }
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Không thể tải thông báo.');
      } finally {
        running = false;
        if (!cancelled) setLoading(false);
      }
    };
    setLoading(true);
    setReminders([]);
    void refresh();
    const onVisible = () => { if (document.visibilityState === 'visible') void refresh(); };
    const timer = window.setInterval(onVisible, 60_000);
    window.addEventListener('course-reminders-updated', onVisible);
    document.addEventListener('visibilitychange', onVisible);
    return () => {
      cancelled = true;
      controller.abort();
      window.clearInterval(timer);
      window.removeEventListener('course-reminders-updated', onVisible);
      document.removeEventListener('visibilitychange', onVisible);
    };
  }, [apiBase, user?.email, revision]);

  useEffect(() => {
    if (!open) return;
    panel.current?.focus();
    const onOutside = (event: PointerEvent) => {
      if (!root.current?.contains(event.target as Node)) setOpen(false);
    };
    const onEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') { setOpen(false); trigger.current?.focus(); }
    };
    document.addEventListener('pointerdown', onOutside);
    document.addEventListener('keydown', onEscape);
    return () => {
      document.removeEventListener('pointerdown', onOutside);
      document.removeEventListener('keydown', onEscape);
    };
  }, [open]);

  const markRead = (ids: string[]) => {
    const next = [...new Set([...readIds, ...ids])].slice(-500);
    setReadIds(next);
    try { localStorage.setItem(storageKey, JSON.stringify(next)); } catch { /* Reading still works without storage. */ }
  };

  return (
    <div ref={root} className="relative" onBlur={event => {
      if (!event.currentTarget.contains(event.relatedTarget as Node | null)) setOpen(false);
    }}>
      <button ref={trigger} type="button" aria-label={`Thông báo môn học, ${unread} chưa đọc`}
        aria-expanded={open} aria-controls={open ? id : undefined} title="Thông báo môn học"
        onClick={() => setOpen(value => !value)}
        className="relative inline-flex h-9 w-9 items-center justify-center rounded-full border border-slate-700 bg-slate-900 text-slate-300 hover:bg-slate-800">
        <Bell aria-hidden="true" className="h-4 w-4" />
        {unread > 0 && <span className="absolute -right-1 -top-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-rose-600 px-1 text-[9px] font-bold text-white" aria-hidden="true">{unread > 9 ? '9+' : unread}</span>}
      </button>
      {open && (
        <div ref={panel} id={id} role="region" aria-label="Thông báo nhắc nhở môn học" tabIndex={-1}
          className="absolute right-0 top-full z-50 mt-3 w-96 max-w-[calc(100vw-2rem)] overflow-hidden rounded-2xl border border-slate-800 bg-slate-900 shadow-xl">
          <div className="flex items-center justify-between gap-2 border-b border-slate-800 px-4 py-3">
            <div><h2 className="text-sm font-bold text-slate-100">Nhắc nhở môn học</h2><p className="mt-1 text-[11px] text-slate-400">{unread} thông báo chưa đọc</p></div>
            <button type="button" disabled={!unread} onClick={() => markRead(reminders.map(reminder => reminder.id))}
              title="Đánh dấu tất cả đã đọc" aria-label="Đánh dấu tất cả đã đọc"
              className="rounded-lg p-2 text-brand-400 hover:bg-slate-800 disabled:opacity-30"><CheckCheck aria-hidden="true" className="h-4 w-4" /></button>
          </div>
          <div className="max-h-96 overflow-y-auto p-2">
            {loading ? <p className="flex items-center justify-center gap-2 p-6 text-xs text-slate-400"><Loader2 className="h-4 w-4 animate-spin" /> Đang tải thông báo…</p>
              : error ? <div className="space-y-3 p-4 text-xs"><p role="alert" className="text-rose-400">{error}</p><button type="button" onClick={() => setRevision(value => value + 1)} className="inline-flex items-center gap-1 text-brand-400"><RefreshCw className="h-3 w-3" /> Thử lại</button></div>
              : reminders.length === 0 ? <p className="p-6 text-center text-xs text-slate-400">Bạn chưa có nhiệm vụ môn học cần nhắc nhở.</p>
              : reminders.map(reminder => {
                const read = readIds.includes(reminder.id);
                const label = reminder.state === 'overdue' ? 'Quá hạn' : reminder.state === 'due_soon' ? (reminder.days_remaining === 0 ? 'Đến hạn hôm nay' : 'Sắp đến hạn') : 'Cần thực hiện';
                const color = reminder.level === 'danger' ? 'text-rose-400' : reminder.level === 'warning' ? 'text-amber-400' : 'text-brand-400';
                return <button type="button" key={reminder.id} onClick={() => {
                  markRead([reminder.id]); setOpen(false); openStudentEnrollment(reminder.enrollment_id);
                }} className={`mb-1 w-full rounded-xl p-3 text-left transition-colors hover:bg-slate-800 ${read ? '' : 'bg-slate-950'}`}>
                  <div className="flex items-center justify-between gap-2"><span className={`text-[10px] font-semibold ${color}`}>{label}</span>{!read && <span className="h-1.5 w-1.5 rounded-full bg-brand-400" aria-label="Chưa đọc" />}</div>
                  <p className="mt-1 flex items-center justify-between gap-2 text-xs font-semibold text-slate-100"><span>{reminder.code_module} — {reminder.course_name}</span><ChevronRight aria-hidden="true" className="h-3.5 w-3.5 shrink-0" /></p>
                  <p className="mt-1 text-[11px] text-slate-400">Học kỳ {reminder.code_presentation}</p>
                  <p className="mt-2 text-xs leading-relaxed text-slate-300">{reminder.message}</p>
                  {reminder.due_date && <p className="mt-1 text-[11px] text-slate-400">Hạn kế hoạch: {reminder.due_date.split('-').reverse().join('/')}</p>}
                </button>;
              })}
          </div>
          <p className="border-t border-slate-800 px-4 py-2 text-[10px] text-slate-400">Nhắc từ nhiệm vụ chưa hoàn thành. Tự cập nhật mỗi phút khi trang đang mở.</p>
        </div>
      )}
    </div>
  );
};
