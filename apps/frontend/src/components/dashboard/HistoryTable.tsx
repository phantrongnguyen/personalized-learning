import React, { useState } from 'react';
import { useApp } from '../../state/AppContext';
import { exportHistoryToCsvFile } from '../../utils/csv';
import { History, Download, Trash2, Search, AlertTriangle, ShieldCheck, X } from 'lucide-react';

export const HistoryTable: React.FC = () => {
  const { history, removeHistoryItem, clearHistory, addToast } = useApp();
  const [filterText, setFilterText] = useState('');

  const filtered = history.filter((h) => {
    if (!filterText.trim()) return true;
    const q = filterText.toLowerCase();
    return (
      h.module.toLowerCase().includes(q) ||
      h.age.toLowerCase().includes(q) ||
      (h.prediction === 1 ? 'nguy co' : 'an toan').includes(q)
    );
  });

  const handleExport = () => {
    if (history.length === 0) {
      addToast('Chưa có dữ liệu lịch sử để xuất file CSV.', 'warning');
      return;
    }
    exportHistoryToCsvFile(history);
    addToast('Đã xuất file báo cáo CSV thành công!', 'success');
  };

  const handleClear = () => {
    if (history.length === 0) return;
    if (window.confirm('Bạn có chắc chắn muốn xóa toàn bộ lịch sử dự đoán trong phiên này?')) {
      clearHistory();
    }
  };

  return (
    <div className="bg-slate-900/90 rounded-2xl border border-slate-800 shadow-xl p-5 sm:p-6">
      {/* Table Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <div className="p-2 rounded-xl bg-blue-500/10 text-blue-400">
            <History className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white">Lịch sử Đánh giá trong phiên</h3>
            <p className="text-xs text-slate-400">
              Lưu trữ tối đa 50 bản ghi gần nhất (lưu cục bộ trong LocalStorage)
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Search box */}
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-slate-500 absolute left-2.5 top-2.5" />
            <input
              type="text"
              placeholder="Lọc môn học / kết quả..."
              value={filterText}
              onChange={(e) => setFilterText(e.target.value)}
              className="pl-8 pr-3 py-1.5 rounded-lg bg-slate-950 border border-slate-750 text-slate-200 text-xs focus:border-brand-500 focus:outline-none w-44"
            />
            {filterText && (
              <button
                onClick={() => setFilterText('')}
                className="absolute right-2 top-2 text-slate-500 hover:text-slate-300"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>

          <button
            onClick={handleExport}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-brand-600/20 hover:bg-brand-600/30 text-brand-300 border border-brand-500/30 transition-colors"
            title="Xuất lịch sử phân tích sang định dạng CSV tương thích Excel"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Xuất CSV</span>
          </button>

          <button
            onClick={handleClear}
            className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-rose-950/30 transition-colors"
            title="Xóa toàn bộ lịch sử"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Table content */}
      <div className="overflow-x-auto mt-4">
        <table className="w-full text-left text-xs">
          <thead className="bg-slate-950/70 text-slate-400 font-semibold border-b border-slate-800">
            <tr>
              <th className="py-2.5 px-3">Thời gian</th>
              <th className="py-2.5 px-3">Mã học phần</th>
              <th className="py-2.5 px-3">Độ tuổi</th>
              <th className="py-2.5 px-3">Tín chỉ</th>
              <th className="py-2.5 px-3">Tổng click</th>
              <th className="py-2.5 px-3">Kết luận mô hình</th>
              <th className="py-2.5 px-3">Xác suất rủi ro</th>
              <th className="py-2.5 px-3 text-right">Tác vụ</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={8} className="py-8 text-center text-slate-500">
                  Chưa có bản ghi phân tích nào phù hợp.
                </td>
              </tr>
            ) : (
              filtered.map((item) => {
                const atRisk = item.prediction === 1;

                return (
                  <tr key={item.id} className="hover:bg-slate-850/50 transition-colors">
                    <td className="py-2.5 px-3 text-slate-300">
                      <div>{item.time}</div>
                      <div className="text-[10px] text-slate-500">{item.date}</div>
                    </td>
                    <td className="py-2.5 px-3 font-bold text-white">{item.module}</td>
                    <td className="py-2.5 px-3 text-slate-400">{item.age}</td>
                    <td className="py-2.5 px-3 text-slate-300 font-mono">{item.credits} TC</td>
                    <td className="py-2.5 px-3 text-slate-300 font-mono">
                      {item.clicks.toLocaleString('vi-VN')}
                    </td>
                    <td className="py-2.5 px-3">
                      <span
                        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md font-semibold text-[11px] ${
                          atRisk
                            ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                            : 'bg-brand-500/20 text-brand-300 border border-brand-500/30'
                        }`}
                      >
                        {atRisk ? (
                          <>
                            <AlertTriangle className="w-3 h-3" />
                            <span>Nguy cơ cao</span>
                          </>
                        ) : (
                          <>
                            <ShieldCheck className="w-3 h-3" />
                            <span>An toàn</span>
                          </>
                        )}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 font-mono font-bold text-slate-200">
                      {(item.confidence * 100).toFixed(1)}%
                    </td>
                    <td className="py-2.5 px-3 text-right">
                      <button
                        onClick={() => removeHistoryItem(item.id)}
                        className="text-slate-500 hover:text-rose-400 transition-colors p-1"
                        title="Xóa dòng này"
                      >
                        <X className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
