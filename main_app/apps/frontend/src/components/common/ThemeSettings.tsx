import React, { useId } from 'react';
import { Monitor, Moon, Sun, Palette } from 'lucide-react';
import { useApp } from '../../state/AppContext';
import { ThemePreference } from '../../utils/theme';

const themeOptions: { value: ThemePreference; label: string; description: string; icon: React.ReactNode }[] = [
  { value: 'dark', label: 'Tối', description: 'Giao diện hiện tại', icon: <Moon className="h-5 w-5" /> },
  { value: 'light', label: 'Sáng', description: 'Xanh dương và trắng', icon: <Sun className="h-5 w-5" /> },
  { value: 'system', label: 'Theo thiết bị', description: 'Theo chế độ sáng/tối của máy', icon: <Monitor className="h-5 w-5" /> },
];

export const ThemeSettings: React.FC = () => {
  const { themePreference, setThemePreference, resolvedTheme } = useApp();
  const groupId = useId();
  return (
    <section aria-labelledby={groupId} className="min-w-0 rounded-2xl border border-slate-800 bg-slate-900/90 p-6 shadow-xl">
      <h3 id={groupId} className="flex items-center gap-2 text-base font-bold text-foreground">
        <Palette className="h-5 w-5 shrink-0 text-brand-400" />Giao diện hệ thống
      </h3>
      <fieldset className="mt-4 min-w-0">
        <legend className="text-xs font-semibold text-slate-300">Chế độ hiển thị</legend>
        <div className="mt-3 grid grid-cols-1 gap-2 sm:grid-cols-3 lg:grid-cols-1 xl:grid-cols-3">
          {themeOptions.map(option => (
            <label key={option.value} className={"min-w-0 cursor-pointer rounded-xl border p-3 focus-within:ring-2 focus-within:ring-brand-400 focus-within:ring-offset-2 focus-within:ring-offset-slate-900 " + (themePreference === option.value ? 'border-brand-400 bg-brand-500/10' : 'border-slate-800 bg-slate-950/50 hover:border-slate-600')}>
              <span className="flex items-center justify-between gap-2 text-brand-400">
                {option.icon}
                <input type="radio" name={groupId} value={option.value} checked={themePreference === option.value} onChange={() => setThemePreference(option.value)} className="h-4 w-4 shrink-0 accent-brand-600" />
              </span>
              <span className="mt-2 block text-xs font-semibold text-slate-200">{option.label}</span>
              <span className="mt-1 block text-[11px] leading-relaxed text-slate-400">{option.description}</span>
            </label>
          ))}
        </div>
      </fieldset>
      <p className="mt-3 text-xs leading-relaxed text-slate-400" role="status">Đang dùng giao diện {resolvedTheme === 'dark' ? 'tối' : 'sáng'}. Áp dụng ngay và ghi nhớ trên trình duyệt này; không thay đổi dữ liệu hay kết quả dự đoán.</p>
    </section>
  );
};
