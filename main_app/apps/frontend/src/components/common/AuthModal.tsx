import React, { useState } from 'react';
import { useApp } from '../../state/AppContext';
import { UserCheck, ShieldCheck, Mail, Lock, User, X } from 'lucide-react';

export const AuthModal: React.FC = () => {
  const { isAuthModalOpen, setIsAuthModalOpen, login } = useApp();
  const [tab, setTab] = useState<'login' | 'register'>('login');

  // Form states
  const [email, setEmail] = useState('');
  const [name, setName] = useState('');
  const [role, setRole] = useState('Cố vấn học tập');

  if (!isAuthModalOpen) return null;

  const handleDemoAdvisor = () => {
    login({
      name: 'Nguyễn Minh Khang',
      email: 'lead.advisor@edurisk.ai',
      role: 'Trưởng ban Cố vấn Học tập',
      initials: 'MK',
    });
  };

  const handleDemoAdmin = () => {
    login({
      name: 'Quản Trị Viên Hệ Thống',
      email: 'admin@edurisk.ai',
      role: 'Quản trị viên Enterprise',
      initials: 'AD',
    });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (tab === 'login') {
      const displayName = email.split('@')[0].toUpperCase();
      login({
        name: displayName,
        email: email || 'user@edurisk.ai',
        role: 'Cố vấn học tập',
        initials: displayName.slice(0, 2),
      });
    } else {
      const initials = name
        .trim()
        .split(' ')
        .map((p) => p[0])
        .join('')
        .slice(0, 2)
        .toUpperCase() || 'SV';
      login({
        name: name || 'Người dùng mới',
        email: email || 'student@edurisk.ai',
        role: role,
        initials: initials,
      });
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[rgb(var(--color-overlay)/0.8)] backdrop-blur-sm animate-fade-in">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 shadow-2xl relative">
        <button
          onClick={() => setIsAuthModalOpen(false)}
          className="absolute top-4 right-4 text-slate-400 hover:text-foreground"
        >
          <X className="w-5 h-5" />
        </button>

        <h3 className="text-xl font-bold text-foreground mb-1">Xác thực hệ thống</h3>
        <p className="text-xs text-slate-400 mb-5">
          Truy cập hệ thống phân tích & theo dõi nguy cơ học tập sinh viên
        </p>

        {/* 1-Click Demo Accounts */}
        <div className="mb-5 p-3.5 rounded-xl bg-slate-950/70 border border-slate-800 space-y-2">
          <div className="text-[11px] font-semibold text-emerald-400 uppercase tracking-wider">
            ⚡ Tài khoản thử nghiệm (1-Click Demo)
          </div>
          <div className="grid grid-cols-2 gap-2">
            <button
              type="button"
              onClick={handleDemoAdvisor}
              className="flex items-center gap-2 p-2 rounded-lg bg-slate-850 hover:bg-slate-800 border border-slate-700/80 text-left transition-colors"
            >
              <UserCheck className="w-4 h-4 text-emerald-400 shrink-0" />
              <div className="truncate">
                <div className="text-xs font-semibold text-slate-200 truncate">Trưởng ban Cố vấn</div>
                <div className="text-[10px] text-slate-400 truncate">Nguyễn Minh Khang</div>
              </div>
            </button>

            <button
              type="button"
              onClick={handleDemoAdmin}
              className="flex items-center gap-2 p-2 rounded-lg bg-slate-855 hover:bg-slate-800 border border-slate-700/80 text-left transition-colors"
            >
              <ShieldCheck className="w-4 h-4 text-teal-400 shrink-0" />
              <div className="truncate">
                <div className="text-xs font-semibold text-slate-200 truncate">Quản trị viên</div>
                <div className="text-[10px] text-slate-400 truncate">Admin Enterprise</div>
              </div>
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-slate-800 mb-4">
          <button
            onClick={() => setTab('login')}
            className={`flex-1 pb-2.5 text-sm font-semibold border-b-2 transition-colors ${
              tab === 'login'
                ? 'border-emerald-500 text-emerald-400'
                : 'border-transparent text-slate-400 hover:text-slate-300'
            }`}
          >
            Đăng nhập
          </button>
          <button
            onClick={() => setTab('register')}
            className={`flex-1 pb-2.5 text-sm font-semibold border-b-2 transition-colors ${
              tab === 'register'
                ? 'border-emerald-500 text-emerald-400'
                : 'border-transparent text-slate-400 hover:text-slate-300'
            }`}
          >
            Đăng ký tài khoản
          </button>
        </div>

        {/* Auth form */}
        <form onSubmit={handleSubmit} className="space-y-3.5">
          {tab === 'register' && (
            <>
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Họ và tên:</label>
                <div className="relative">
                  <User className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
                  <input
                    type="text"
                    required
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Nguyễn Văn A"
                    className="w-full pl-9 pr-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-700 text-slate-100 text-sm focus:border-brand-500 focus:outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Vai trò:</label>
                <select
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-700 text-slate-100 text-sm focus:border-brand-500 focus:outline-none"
                >
                  <option value="Trưởng ban Cố vấn Học tập">Trưởng ban Cố vấn Học tập (Lead Advisor)</option>
                  <option value="Ban Giám đốc Đào tạo">Ban Giám đốc Đào tạo (Academic Director)</option>
                  <option value="Chuyên viên Phân tích Dữ liệu">Chuyên viên Phân tích Dữ liệu (Learning Data Analyst)</option>
                  <option value="Giảng viên Phụ trách Học phần">Giảng viên Phụ trách Học phần (Course Instructor)</option>
                </select>
              </div>
            </>
          )}

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Email:</label>
            <div className="relative">
              <Mail className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@university.edu.vn"
                className="w-full pl-9 pr-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-700 text-slate-100 text-sm focus:border-brand-500 focus:outline-none"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Mật khẩu:</label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
              <input
                type="password"
                required
                defaultValue="password123"
                placeholder="••••••••"
                className="w-full pl-9 pr-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-700 text-slate-100 text-sm focus:border-brand-500 focus:outline-none"
              />
            </div>
          </div>

          <button
            type="submit"
            className="w-full py-2.5 px-4 mt-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-semibold text-sm shadow-lg shadow-emerald-600/20 transition-all"
          >
            {tab === 'login' ? 'Đăng nhập ngay' : 'Tạo tài khoản'}
          </button>
        </form>
      </div>
    </div>
  );
};
