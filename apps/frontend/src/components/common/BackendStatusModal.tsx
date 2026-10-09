import React, { useState } from 'react';
import { useApp } from '../../state/AppContext';
import { Server, RefreshCw, CheckCircle, AlertOctagon, X } from 'lucide-react';

export const BackendStatusModal: React.FC = () => {
  const {
    apiBase,
    setApiBase,
    backendStatus,
    modelLoaded,
    latency,
    refreshHealth,
    isBackendModalOpen,
    setIsBackendModalOpen,
  } = useApp();

  const [inputUrl, setInputUrl] = useState(apiBase);
  const [checking, setChecking] = useState(false);

  if (!isBackendModalOpen) return null;

  const handleTestAndSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setChecking(true);
    setApiBase(inputUrl);
    await refreshHealth();
    setChecking(false);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fade-in">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 shadow-2xl relative">
        <button
          onClick={() => setIsBackendModalOpen(false)}
          className="absolute top-4 right-4 text-slate-400 hover:text-white"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-3 mb-4">
          <div className="p-2.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
            <Server className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-white">Cấu hình kết nối Backend</h3>
            <p className="text-xs text-slate-400">FastAPI ML Prediction Service</p>
          </div>
        </div>

        {/* Current status overview card */}
        <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 mb-5 space-y-2.5">
          <div className="flex items-center justify-between text-xs">
            <span className="text-slate-400">Trạng thái API:</span>
            <span
              className={`font-semibold flex items-center gap-1.5 ${
                backendStatus === 'ok'
                  ? 'text-emerald-400'
                  : backendStatus === 'checking'
                  ? 'text-amber-400'
                  : 'text-rose-400'
              }`}
            >
              {backendStatus === 'ok' ? (
                <>
                  <CheckCircle className="w-3.5 h-3.5" /> Hoạt động bình thường
                </>
              ) : backendStatus === 'checking' ? (
                'Đang kiểm tra...'
              ) : (
                <>
                  <AlertOctagon className="w-3.5 h-3.5" /> Không thể kết nối
                </>
              )}
            </span>
          </div>

          <div className="flex items-center justify-between text-xs">
            <span className="text-slate-400">Mô hình HCO-VNLS + LightGBM:</span>
            <span className="font-semibold text-slate-200">
              {modelLoaded === true
                ? 'Đã nạp sẵn trong bộ nhớ'
                : modelLoaded === false
                ? 'Chưa nạp hoặc lỗi'
                : 'Đang kiểm tra'}
            </span>
          </div>

          <div className="flex items-center justify-between text-xs">
            <span className="text-slate-400">Độ trễ mạng (Ping):</span>
            <span className="font-mono text-emerald-300 font-semibold">
              {latency !== null ? `${latency} ms` : '—'}
            </span>
          </div>
        </div>

        {/* Update URL form */}
        <form onSubmit={handleTestAndSave} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Đường dẫn Backend Host URL:
            </label>
            <input
              type="text"
              value={inputUrl}
              onChange={(e) => setInputUrl(e.target.value)}
              placeholder="http://127.0.0.1:8000"
              className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-700 text-slate-100 text-sm font-mono focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
            />
            <p className="text-[11px] text-slate-500 mt-1">
              Mặc định cục bộ: <code className="text-slate-400">http://127.0.0.1:8000</code>
            </p>
          </div>

          <div className="flex items-center gap-2 pt-2">
            <button
              type="button"
              disabled={checking}
              onClick={async () => {
                setChecking(true);
                await refreshHealth();
                setChecking(false);
              }}
              className="flex-1 flex items-center justify-center gap-1.5 px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-semibold transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${checking ? 'animate-spin' : ''}`} />
              <span>Kiểm tra lại</span>
            </button>

            <button
              type="submit"
              disabled={checking}
              className="flex-1 flex items-center justify-center gap-1.5 px-4 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-semibold shadow-lg shadow-emerald-600/20 transition-all disabled:opacity-50"
            >
              <span>Lưu cấu hình</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
