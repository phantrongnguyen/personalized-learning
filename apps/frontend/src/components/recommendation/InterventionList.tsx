import React from 'react';
import { InterventionStrategy } from '@shared/types';
import { useApp } from '../../state/AppContext';
import { Copy, Target, Sparkles, CheckCircle, Clock, HeartHandshake, BookOpen } from 'lucide-react';

interface InterventionListProps {
  strategies: InterventionStrategy[];
}

export const InterventionList: React.FC<InterventionListProps> = ({ strategies }) => {
  const { addToast } = useApp();

  if (strategies.length === 0) return null;

  const handleCopyAll = () => {
    const textContent =
      `[EduRisk — Gợi ý minh họa tại cutoff, chưa kiểm chứng; cần cố vấn xác minh]\n\n` +
      strategies
        .map(
          (s, idx) =>
            `${idx + 1}. [${s.priority}] ${s.title}\n` +
            `   - Chi tiết: ${s.description}\n` +
            (s.targetMetric ? `   - Chỉ số mục tiêu: ${s.targetMetric}\n` : '')
        )
        .join('\n');

    navigator.clipboard
      .writeText(textContent)
      .then(() => {
        addToast('Đã sao chép danh sách khuyến nghị vào Clipboard!', 'success');
      })
      .catch(() => {
        addToast('Không thể tự động sao chép, vui lòng thử lại.', 'warning');
      });
  };

  const getCategoryIcon = (cat: string) => {
    switch (cat) {
      case 'chuyen_can':
        return <Clock className="w-4 h-4 text-amber-400" />;
      case 'tam_ly':
        return <HeartHandshake className="w-4 h-4 text-purple-400" />;
      case 'tien_do':
        return <Target className="w-4 h-4 text-blue-400" />;
      default:
        return <BookOpen className="w-4 h-4 text-brand-400" />;
    }
  };

  return (
    <div className="bg-slate-900/90 rounded-2xl border border-slate-800 shadow-xl p-5 sm:p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className="p-2 rounded-xl bg-brand-500/10 text-brand-400">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white">Gợi ý minh họa để cố vấn xem xét</h3>
            <p className="text-xs text-slate-400">Quy tắc giả định trên dữ liệu nhập tại cutoff; chưa kiểm chứng hiệu quả. Cố vấn xác minh và điều chỉnh trước khi áp dụng.</p>
          </div>
        </div>

        <button
          onClick={handleCopyAll}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-colors"
          title="Sao chép toàn bộ khuyến nghị để gửi cho sinh viên hoặc lưu trữ"
        >
          <Copy className="w-3.5 h-3.5" />
          <span>Sao chép</span>
        </button>
      </div>

      <div className="space-y-3">
        {strategies.map((item) => {
          let priorityBadge = 'bg-slate-800 text-slate-400 border-slate-700';
          if (item.priority === 'HIGH') {
            priorityBadge = 'bg-rose-500/20 text-rose-300 border-rose-500/30';
          } else if (item.priority === 'MEDIUM') {
            priorityBadge = 'bg-amber-500/20 text-amber-300 border-amber-500/30';
          } else {
            priorityBadge = 'bg-brand-500/20 text-brand-300 border-brand-500/30';
          }

          return (
            <div
              key={item.id}
              className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 hover:border-slate-700 transition-colors"
            >
              <div className="flex items-start justify-between gap-3 mb-1.5">
                <div className="flex items-center gap-2">
                  {getCategoryIcon(item.category)}
                  <h4 className="text-sm font-bold text-slate-100">{item.title}</h4>
                </div>

                <span
                  className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-md border shrink-0 ${priorityBadge}`}
                >
                  {item.priority === 'HIGH'
                    ? 'Ưu tiên cao'
                    : item.priority === 'MEDIUM'
                    ? 'Ưu tiên vừa'
                    : 'Theo dõi'}
                </span>
              </div>

              <p className="text-xs text-slate-300 leading-relaxed pl-6">{item.description}</p>

              {item.targetMetric && (
                <div className="mt-2.5 ml-6 flex items-center gap-1.5 text-xs text-brand-400 font-medium">
                  <CheckCircle className="w-3.5 h-3.5 shrink-0" />
                  <span>
                    Chỉ số mục tiêu:{' '}
                    <strong className="text-brand-300">{item.targetMetric}</strong>
                  </span>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
