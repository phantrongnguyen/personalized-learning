import React, { useState } from 'react';
import { useApp } from '../../state/AppContext';
import { UserCheck, ShieldCheck, Mail, Lock, User, X, Eye, EyeOff, GraduationCap, Loader2 } from 'lucide-react';
import { loginApi, mapBackendUser } from '../../services/api';

export const AuthModal: React.FC = () => {
  const { isAuthModalOpen, setIsAuthModalOpen, login, apiBase, addToast } = useApp();
  const [tab, setTab] = useState<'login' | 'register'>('login');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  // Form states
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('123');

  if (!isAuthModalOpen) return null;

  const handleQuickLogin = async (loginEmail: string, loginPass = '123') => {
    setIsLoading(true);
    try {
      const { user } = await loginApi(apiBase, loginEmail, loginPass);
      login(mapBackendUser(user));
      setIsAuthModalOpen(false);
    } catch (err: any) {
      addToast(err.message || 'Không thể đăng nhập vào hệ thống', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDemoAdvisor = () => handleQuickLogin('advisor@huit.edu.vn', '123');
  const handleDemoAdmin = () => handleQuickLogin('admin@huit.edu.vn', '123');
  const handleDemoLecturer = () => handleQuickLogin('lecturer@huit.edu.vn', '123');
  const handleDemoStudent = () => handleQuickLogin('student@huit.edu.vn', '123');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (tab === 'login') {
      await handleQuickLogin(email, password);
    } else {
      addToast('Chức năng đăng ký công khai tạm khóa, vui lòng liên hệ Admin!', 'info');
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fade-in">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 shadow-2xl relative">
        <button
          onClick={() => setIsAuthModalOpen(false)}
          className="absolute top-4 right-4 text-slate-400 hover:text-white"
        >
          <X className="w-5 h-5" />
        </button>

        <h3 className="text-xl font-bold text-white mb-1">Xác thực hệ thống KLTN 13</h3>
        <p className="text-xs text-slate-400 mb-5">
          Đăng nhập thực tế vào Backend FastAPI với phân quyền 4 vai trò
        </p>

        {/* 1-Click Demo Accounts */}
        <div className="mb-5 p-3.5 rounded-xl bg-slate-950/70 border border-slate-800 space-y-2">
          <div className="text-[11px] font-semibold text-brand-400 uppercase tracking-wider">
            ⚡ Đăng nhập mẫu 4 vai trò (1-Click Login)
          </div>
          <div className="grid grid-cols-2 gap-2">
            <button
              type="button"
              disabled={isLoading}
              onClick={handleDemoAdvisor}
              className="flex items-center gap-2 p-2 rounded-lg bg-slate-850 hover:bg-slate-800 border border-slate-700/80 text-left transition-colors"
            >
              <UserCheck className="w-4 h-4 text-brand-400 shrink-0" />
              <div className="truncate">
                <div className="text-xs font-semibold text-slate-200">Cố vấn học tập</div>
                <div className="text-[10px] text-slate-400">advisor@huit.edu.vn</div>
              </div>
            </button>

            <button
              type="button"
              disabled={isLoading}
              onClick={handleDemoLecturer}
              className="flex items-center gap-2 p-2 rounded-lg bg-slate-850 hover:bg-slate-800 border border-slate-700/80 text-left transition-colors"
            >
              <User className="w-4 h-4 text-purple-400 shrink-0" />
              <div className="truncate">
                <div className="text-xs font-semibold text-slate-200">Giảng viên bộ môn</div>
                <div className="text-[10px] text-slate-400">lecturer@huit.edu.vn</div>
              </div>
            </button>

            <button
              type="button"
              disabled={isLoading}
              onClick={handleDemoAdmin}
              className="flex items-center gap-2 p-2 rounded-lg bg-slate-850 hover:bg-slate-800 border border-slate-700/80 text-left transition-colors"
            >
              <ShieldCheck className="w-4 h-4 text-brand-400 shrink-0" />
              <div className="truncate">
                <div className="text-xs font-semibold text-slate-200">Quản trị viên</div>
                <div className="text-[10px] text-slate-400">admin@huit.edu.vn</div>
              </div>
            </button>

            <button
              type="button"
              disabled={isLoading}
              onClick={handleDemoStudent}
              className="flex items-center gap-2 p-2 rounded-lg bg-slate-850 hover:bg-slate-800 border border-slate-700/80 text-left transition-colors"
            >
              <GraduationCap className="w-4 h-4 text-cyan-400 shrink-0" />
              <div className="truncate">
                <div className="text-xs font-semibold text-slate-200">Sinh viên</div>
                <div className="text-[10px] text-slate-400">student@huit.edu.vn</div>
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
                ? 'border-brand-500 text-brand-400'
                : 'border-transparent text-slate-400 hover:text-slate-300'
            }`}
          >
            Đăng nhập tài khoản
          </button>
        </div>

        {/* Auth form */}
        <form onSubmit={handleSubmit} className="space-y-3.5">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Email đăng nhập:</label>
            <div className="relative">
              <Mail className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="admin@huit.edu.vn"
                className="w-full pl-9 pr-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-700 text-slate-100 text-sm focus:border-brand-500 focus:outline-none"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Mật khẩu:</label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
              <input
                type={showPassword ? 'text' : 'password'}
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full pl-9 pr-10 py-2.5 rounded-xl bg-slate-950 border border-slate-700 text-slate-100 text-sm focus:border-brand-500 focus:outline-none"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-3 text-slate-500 hover:text-slate-300"
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-2.5 px-4 mt-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-semibold text-sm shadow-lg shadow-brand-600/20 transition-all flex items-center justify-center gap-2"
          >
            {isLoading && <Loader2 className="w-4 h-4 animate-spin" />}
            {isLoading ? 'Đang xác thực...' : 'Đăng nhập ngay'}
          </button>
        </form>
      </div>
    </div>
  );
};
