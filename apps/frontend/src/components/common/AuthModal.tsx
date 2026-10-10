import React, { useState } from 'react';
import { useApp } from '../../state/AppContext';
import { UserCheck, ShieldCheck, Mail, Lock, User, X, Eye, EyeOff, GraduationCap } from 'lucide-react';

export const AuthModal: React.FC = () => {
  const { isAuthModalOpen, setIsAuthModalOpen, login } = useApp();
  const [tab, setTab] = useState<'login' | 'register'>('login');
  const [showPassword, setShowPassword] = useState(false);

  // Form states
  const [email, setEmail] = useState('');
  const [name, setName] = useState('');
  const [role, setRole] = useState('Trưởng ban Cố vấn Học tập');

  if (!isAuthModalOpen) return null;

  const handleDemoAdvisor = () => {
    login({
      name: 'TS. Nguyễn Minh Khang',
      email: 'lead.advisor@edurisk.ai',
      role: 'Trưởng ban Cố vấn Học tập',
      initials: 'MK',
      department: 'Ban Quản trị & Cố vấn Đào tạo',
    });
  };

  const handleDemoAdmin = () => {
    login({
      name: 'Trần Hoàng Nam',
      email: 'admin@edurisk.ai',
      role: 'Quản trị viên Enterprise',
      initials: 'AD',
      department: 'Phòng CNTT & Đảm bảo Chất lượng',
    });
  };

  const handleDemoStudent = () => {
    login({
      name: 'Lê Thu Hà',
      email: 'thuha.le@edurisk.ai',
      role: 'Sinh viên',
      initials: 'TH',
      department: 'Khoa Công nghệ Thông tin (K65)',
    });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (tab === 'login') {
      const emailPrefix = email.split('@')[0] || 'User';
      const displayName =
        emailPrefix.charAt(0).toUpperCase() + emailPrefix.slice(1).replace(/[._]/g, ' ');
      login({
        name: displayName,
        email: email || 'user@edurisk.ai',
        role: email.includes('admin')
          ? 'Quản trị viên Enterprise'
          : email.includes('student')
          ? 'Sinh viên'
          : 'Cố vấn học tập',
        initials: displayName.slice(0, 2).toUpperCase(),
        department: 'Ban Quản lý Đào tạo',
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
        department: 'Khoa Đào tạo Đối tác',
      });
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

        <h3 className="text-xl font-bold text-white mb-1">Xác thực hệ thống EduRisk AI</h3>
        <p className="text-xs text-slate-400 mb-5">
          Chuyển đổi tài khoản hoặc đăng nhập với vai trò chuyên môn khác
        </p>

        {/* 1-Click Demo Accounts */}
        <div className="mb-5 p-3.5 rounded-xl bg-slate-950/70 border border-slate-800 space-y-2">
          <div className="text-[11px] font-semibold text-emerald-400 uppercase tracking-wider">
            ⚡ Khởi chạy nhanh (1-Click Demo)
          </div>
          <div className="grid grid-cols-3 gap-2">
            <button
              type="button"
              onClick={handleDemoAdvisor}
              className="flex flex-col p-2 rounded-lg bg-slate-850 hover:bg-slate-800 border border-slate-700/80 text-left transition-colors"
            >
              <div className="flex items-center gap-1 text-xs font-semibold text-slate-200">
                <UserCheck className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                <span>Cố vấn</span>
              </div>
              <div className="text-[10px] text-slate-400 truncate mt-0.5">TS. Minh Khang</div>
            </button>

            <button
              type="button"
              onClick={handleDemoAdmin}
              className="flex flex-col p-2 rounded-lg bg-slate-850 hover:bg-slate-800 border border-slate-700/80 text-left transition-colors"
            >
              <div className="flex items-center gap-1 text-xs font-semibold text-slate-200">
                <ShieldCheck className="w-3.5 h-3.5 text-teal-400 shrink-0" />
                <span>Admin</span>
              </div>
              <div className="text-[10px] text-slate-400 truncate mt-0.5">Trần H. Nam</div>
            </button>

            <button
              type="button"
              onClick={handleDemoStudent}
              className="flex flex-col p-2 rounded-lg bg-slate-850 hover:bg-slate-800 border border-slate-700/80 text-left transition-colors"
            >
              <div className="flex items-center gap-1 text-xs font-semibold text-slate-200">
                <GraduationCap className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
                <span>Sinh viên</span>
              </div>
              <div className="text-[10px] text-slate-400 truncate mt-0.5">Lê Thu Hà</div>
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
                    className="w-full pl-9 pr-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-700 text-slate-100 text-sm focus:border-emerald-500 focus:outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Vai trò:</label>
                <select
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-700 text-slate-100 text-sm focus:border-emerald-500 focus:outline-none"
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
                className="w-full pl-9 pr-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-700 text-slate-100 text-sm focus:border-emerald-500 focus:outline-none"
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
                defaultValue="password123"
                placeholder="••••••••"
                className="w-full pl-9 pr-10 py-2.5 rounded-xl bg-slate-950 border border-slate-700 text-slate-100 text-sm focus:border-emerald-500 focus:outline-none"
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
            className="w-full py-2.5 px-4 mt-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-sm shadow-lg shadow-emerald-600/20 transition-all"
          >
            {tab === 'login' ? 'Đăng nhập ngay' : 'Tạo tài khoản'}
          </button>
        </form>
      </div>
    </div>
  );
};
