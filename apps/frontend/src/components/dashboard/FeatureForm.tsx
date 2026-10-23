import React, { useState } from 'react';
import { StudentFeatures, FeatureGroup } from '@shared/types';
import { FIELDS, PRESETS, DEFAULT_FEATURES } from '@shared/constants';
import { UserX, UserCheck, RotateCcw, Search, Loader2 } from 'lucide-react';
import { DashboardGuide } from './DashboardGuide';

interface FeatureFormProps {
  features: StudentFeatures;
  onChange: (features: StudentFeatures) => void;
  onSubmit: () => Promise<void>;
  loading: boolean;
}

export const FeatureForm: React.FC<FeatureFormProps> = ({
  features,
  onChange,
  onSubmit,
  loading,
}) => {
  const [activeGroup, setActiveGroup] = useState<FeatureGroup>('activity');

  const handleInputChange = (key: keyof StudentFeatures, val: string | number) => {
    onChange({
      ...features,
      [key]: val,
    });
  };

  const handleApplyPreset = (type: 'weak' | 'good' | 'reset') => {
    if (type === 'reset') {
      onChange(DEFAULT_FEATURES);
    } else {
      onChange(PRESETS[type]);
    }
  };

  const groupTabs: { id: FeatureGroup; label: string; count: number }[] = [
    { id: 'info', label: '1. Nhân khẩu & Đăng ký', count: 6 },
    { id: 'activity', label: '2. Tương tác LMS/VLE', count: 8 },
    { id: 'assessment', label: '3. Bài nộp & Đánh giá', count: 3 },
  ];

  const currentFields = FIELDS.filter((f) => f.group === activeGroup);

  return (
    <div className="bg-slate-900/90 rounded-2xl border border-slate-800 shadow-xl p-5 sm:p-6">
      {/* Preset Action Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-5 border-b border-slate-800">
        <div>
          <h2 className="text-base font-bold text-white">Hồ sơ 17 Đặc trưng Sinh viên</h2>
          <p className="text-xs text-slate-400">Nhập đầy đủ chỉ số học tập tại mốc đánh giá để phân tích nguy cơ.</p>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => handleApplyPreset('weak')}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-rose-500/15 hover:bg-rose-500/25 text-rose-300 border border-rose-500/30 transition-all"
            title="Nạp mẫu sinh viên có nguy cơ cao để thử nghiệm"
          >
            <UserX className="w-3.5 h-3.5" />
            <span>Mẫu SV Yếu</span>
          </button>

          <button
            type="button"
            onClick={() => handleApplyPreset('good')}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-brand-500/15 hover:bg-brand-500/25 text-brand-300 border border-brand-500/30 transition-all"
            title="Nạp mẫu sinh viên an toàn, học lực tốt"
          >
            <UserCheck className="w-3.5 h-3.5" />
            <span>Mẫu SV Tốt</span>
          </button>

          <button
            type="button"
            onClick={() => handleApplyPreset('reset')}
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
            title="Đặt lại các trường về giá trị mặc định"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Tabs navigation */}
      <div className="flex border-b border-slate-800 mt-4 mb-5 overflow-x-auto">
        {groupTabs.map((tab) => {
          const isActive = activeGroup === tab.id;
          return (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveGroup(tab.id)}
              className={`flex items-center gap-2 pb-3 px-3 text-xs sm:text-sm font-semibold border-b-2 whitespace-nowrap transition-colors ${
                isActive
                  ? 'border-brand-500 text-brand-400'
                  : 'border-transparent text-slate-400 hover:text-slate-300'
              }`}
            >
              <span>{tab.label}</span>
              <span
                className={`text-[10px] px-1.5 py-0.5 rounded-full ${
                  isActive ? 'bg-brand-500/20 text-brand-300' : 'bg-slate-800 text-slate-500'
                }`}
              >
                {tab.count}
              </span>
            </button>
          );
        })}
      </div>

      {/* Fields Grid */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          onSubmit();
        }}
      >
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
          {currentFields.map((field) => {
            const val = features[field.key];

            return (
              <div
                key={field.key}
                className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 hover:border-slate-700/80 transition-colors"
              >
                <div className="flex items-baseline justify-between mb-1">
                  <label htmlFor={field.key} className="text-xs font-semibold text-slate-200">
                    {field.label}
                  </label>
                  <span className="text-[10px] font-mono text-slate-500">{field.hint}</span>
                </div>

                {field.type === 'select' ? (
                  <select
                    id={field.key}
                    value={String(val)}
                    onChange={(e) => handleInputChange(field.key, e.target.value)}
                    className="w-full mt-1 px-3 py-2 rounded-lg bg-slate-900 border border-slate-750 text-slate-100 text-xs sm:text-sm focus:border-brand-500 focus:outline-none"
                  >
                    {field.options?.map((opt) => (
                      <option key={opt} value={opt}>
                        {opt}
                      </option>
                    ))}
                  </select>
                ) : (
                  <input
                    id={field.key}
                    type="number"
                    step={field.step ?? 1}
                    min={field.min}
                    max={field.max}
                    value={val as number}
                    onChange={(e) => handleInputChange(field.key, parseFloat(e.target.value) || 0)}
                    className="w-full mt-1 px-3 py-2 rounded-lg bg-slate-900 border border-slate-750 text-slate-100 text-xs sm:text-sm font-mono focus:border-brand-500 focus:outline-none"
                  />
                )}
              </div>
            );
          })}
        </div>

        {/* Submit Button */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-4 border-t border-slate-800">
          <DashboardGuide />

          <button
            type="submit"
            disabled={loading}
            className="w-full sm:w-auto flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-brand-600 to-brand-600 hover:from-brand-500 hover:to-brand-500 text-white font-bold text-sm shadow-lg shadow-brand-600/25 transition-all disabled:opacity-50"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Mô hình đang phân tích...</span>
              </>
            ) : (
              <>
                <Search className="w-4 h-4" />
                <span>Phân tích nguy cơ học tập</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};
