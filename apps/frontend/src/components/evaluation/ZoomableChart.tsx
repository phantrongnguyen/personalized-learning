import React, { useEffect, useId, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { X } from 'lucide-react';

export const ZoomableChart: React.FC<{ title: string; children: React.ReactNode; variant?: 'chart' | 'table' }> = ({ title, children, variant = 'chart' }) => {
  const contentLabel = variant === 'table' ? 'bảng' : 'biểu đồ';
  const [expanded, setExpanded] = useState(false);
  const dialogRef = useRef<HTMLDialogElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const titleId = useId();

  useEffect(() => {
    if (!expanded || !dialogRef.current) return;
    const dialog = dialogRef.current;
    const previousOverflow = document.body.style.overflow;
    dialog.showModal();
    document.body.style.overflow = 'hidden';
    return () => {
      dialog.close();
      document.body.style.overflow = previousOverflow;
      triggerRef.current?.focus({ preventScroll: true });
    };
  }, [expanded]);

  const expandFromCard = (event: React.MouseEvent<HTMLElement>) => {
    const target = event.target;
    if (!(target instanceof Element) || target.closest('button, select, input, a, label, summary, [role="button"]')) return;
    // Selecting text or dragging a chart scrollbar should not open the viewer.
    if (window.getSelection()?.toString()) return;
    setExpanded(true);
  };

  return <article className={variant === 'table' ? 'evaluation-table-zoom min-w-0 cursor-zoom-in' : 'rounded-2xl border evaluation-chart-card p-4 sm:p-5 min-w-0 cursor-zoom-in'} onClick={expandFromCard}>
    <button ref={triggerRef} type="button" aria-label={`Mở ${contentLabel} lớn: ${title}`} aria-haspopup="dialog"
      onClick={() => setExpanded(true)}
      className="sr-only focus:not-sr-only focus:mb-3 focus:rounded-lg focus:border focus:border-slate-700 focus:px-3 focus:py-2 focus:text-sm">
      Xem {contentLabel} lớn
    </button>
    {children}
    {expanded && createPortal(
      <dialog ref={dialogRef} aria-labelledby={titleId} className={`evaluation-charts evaluation-chart-dialog ${variant === 'table' ? 'evaluation-table-dialog' : ''} rounded-2xl border p-0`}
        onCancel={event => { event.preventDefault(); setExpanded(false); }}
        onClose={() => setExpanded(false)}
        onClick={event => {
          event.stopPropagation();
          if (event.target !== event.currentTarget) return;
          const bounds = event.currentTarget.getBoundingClientRect();
          if (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom) setExpanded(false);
        }}>
        <div className="evaluation-chart-dialog-header flex items-center justify-between gap-4 border-b px-5 py-4">
          <div><h2 id={titleId} className="text-base sm:text-lg font-bold">{title}</h2><p className="text-xs text-slate-400 mt-1">Chế độ phóng to · Nhấn Esc hoặc nhấp bên ngoài để đóng</p></div>
          <button type="button" autoFocus onClick={() => setExpanded(false)} aria-label={`Đóng ${contentLabel} phóng to`}
            className="shrink-0 rounded-lg border border-slate-700 p-2 text-slate-300 hover:bg-slate-800 transition-colors">
            <X className="w-5 h-5" aria-hidden="true" />
          </button>
        </div>
        <div className="evaluation-chart-dialog-content p-4 sm:p-6 space-y-3">{children}</div>
      </dialog>, document.body)}
  </article>;
};
