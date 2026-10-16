import React from 'react';
import { Moon, Sun } from 'lucide-react';
import { useApp } from '../../state/AppContext';

export const ThemeToggle: React.FC = () => {
  const { theme, setTheme } = useApp();
  const dark = theme === 'dark';
  const label = dark ? 'Chuyển sang giao diện sáng' : 'Chuyển sang giao diện tối';

  return (
    <button
      type="button"
      onClick={() => setTheme(dark ? 'light' : 'dark')}
      aria-label={label}
      aria-pressed={dark}
      title={label}
      className="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-slate-700 bg-slate-900 text-sm font-medium text-slate-200 hover:bg-slate-800 transition-colors"
    >
      {dark ? <Sun className="h-4 w-4" aria-hidden="true" /> : <Moon className="h-4 w-4" aria-hidden="true" />}
    </button>
  );
};
