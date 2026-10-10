import React, { useState } from 'react';
import { useApp } from '../state/AppContext';
import {
  User,
  ShieldCheck,
  Building,
  Mail,
  Phone,
  Key,
  Bell,
  Activity,
  AlertTriangle,
  History,
  CheckCircle2,
  Copy,
  Save,
  LogIn,
  Sliders,
} from 'lucide-react';

export const ProfilePage: React.FC = () => {
  const { user, login, logout, updateUser, history, addToast } = useApp();

  // Form states
  const [name, setName] = useState(user?.name || 'Nguyễn Minh Khang');
  const [email, setEmail] = useState(user?.email || 'lead.advisor@edurisk.ai');
  const [role, setRole] = useState(user?.role || 'Trưởng ban Cố vấn Học tập');
  const [department, setDepartment] = useState(user?.department || 'Ban Quản lý & Cố vấn Đào tạo');
  const [phone, setPhone] = useState(user?.phone || '0908 123 456');
  const [organization, setOrganization] = useState(
    user?.organization || 'Học viện & Trường Đại học Đối tác'
  );

  // Preference toggles
  const [autoEmailAlert, setAutoEmailAlert] = useState(true);
  const [csvBomFormat, setCsvBomFormat] = useState(true);

  // Demo API Token for LMS
  const [lmsApiKey] = useState('edurisk_live_sec_99a8b7c6d5e4f3a2b1c0d9e8f7');

  const highRiskCount = history.filter((h) => h.prediction === 1).length;
  const safeCount = history.filter((h) => h.prediction === 0).length;

  const handleSaveProfile = (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) {
      login({
        name,
        email,
        role,
        initials: name
          .split(' ')
          .map((n) => n[0])
          .join('')
          .slice(0, 2)
          .toUpperCase(),
        department,
        phone,
        organization,
      });
    } else {
      updateUser({
        name,
        email,
        role,
        department,
        phone,
        organization,
      });
    }
  };

  const handleCopyApiKey = () => {
    navigator.clipboard
      .writeText(lmsApiKey)
      .then(() => {
        addToast('Đã sao chép LMS API Integration Key!', 'success');
      })
      .catch(() => {
        addToast('Không thể sao chép tự động, vui lòng chọn thủ công.', 'warning');
      });
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 space-y-8">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-extrabold text-white tracking-tight flex items-center gap-2.5">
          <User className="w-7 h-7 text-emerald-400" />
          <span>Hồ Sơ Chuyên Gia &amp; Cài Đặt Hệ Thống</span>
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Quản lý thông tin tài khoản chuyên gia cố vấn, phân quyền truy cập và cấu hình tích hợp EduRisk AI
        </p>
      </div>

      {/* Hero Profile Overview Card */}
      <div className="p-6 sm:p-8 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-80 h-80 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="flex flex-col sm:flex-row items-center sm:items-start gap-6 relative z-10">
          {/* Avatar circle */}
          <div className="w-20 h-20 rounded-2xl bg-gradient-to-tr from-emerald-600 to-teal-400 text-white font-extrabold text-2xl flex items-center justify-center shadow-lg shadow-emerald-500/20 shrink-0 border-2 border-emerald-400/40">
            {user ? user.initials : 'MK'}
          </div>

          {/* User Meta */}
          <div className="flex-1 text-center sm:text-left space-y-2">
            <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-3">
              <h2 className="text-2xl font-bold text-white">{user ? user.name : name}</h2>
              <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 w-fit mx-auto sm:mx-0">
                <ShieldCheck className="w-3.5 h-3.5" />
                <span>{user ? user.role : role}</span>
              </span>
            </div>

            <div className="flex flex-wrap items-center justify-center sm:justify-start gap-4 text-xs text-slate-300">
              <span className="flex items-center gap-1.5 text-slate-400">
                <Mail className="w-4 h-4 text-slate-500" />
                <span>{user ? user.email : email}</span>
              </span>
              <span className="flex items-center gap-1.5 text-slate-400">
                <Building className="w-4 h-4 text-slate-500" />
                <span>{department}</span>
              </span>
              <span className="flex items-center gap-1.5 text-slate-400">
                <Phone className="w-4 h-4 text-slate-500" />
                <span>{phone}</span>
              </span>
            </div>
          </div>

          {/* Quick Action Button */}
          <div className="shrink-0">
            {user ? (
              <button
                type="button"
                onClick={logout}
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-rose-950/40 text-slate-300 hover:text-rose-300 border border-slate-700 hover:border-rose-500/40 text-xs font-semibold transition-all"
              >
                Đăng xuất tài khoản
              </button>
            ) : (
              <button
                type="button"
                onClick={() =>
                  login({
                    name: 'Nguyễn Minh Khang',
                    email: 'lead.advisor@edurisk.ai',
                    role: 'Trưởng ban Cố vấn Học tập',
                    initials: 'MK',
                  })
                }
                className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold shadow-lg shadow-emerald-600/20 transition-all"
              >
                <LogIn className="w-4 h-4" />
                <span>Kích hoạt phiên làm việc</span>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Activity Statistics & Security Level */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-md">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold">Cấp độ bảo mật</span>
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-xl font-bold text-white">Tier 1: Toàn quyền</div>
          <p className="text-[11px] text-emerald-400 mt-1">Dự báo nguy cơ &amp; Kê đơn can thiệp</p>
        </div>

        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-md">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold">Phân tích phiên này</span>
            <Activity className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-xl font-bold text-white font-mono">{history.length} hồ sơ</div>
          <p className="text-[11px] text-slate-400 mt-1">Đã lưu trữ trong bộ nhớ đệm</p>
        </div>

        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-md">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold">Ca nguy cơ cao</span>
            <AlertTriangle className="w-4 h-4 text-rose-400" />
          </div>
          <div className="text-xl font-bold text-rose-400 font-mono">{highRiskCount} sinh viên</div>
          <p className="text-[11px] text-rose-400/80 mt-1">Cần triển khai can thiệp sớm</p>
        </div>

        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-md">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold">Ca an toàn / Khá giỏi</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-xl font-bold text-emerald-400 font-mono">{safeCount} sinh viên</div>
          <p className="text-[11px] text-emerald-400/80 mt-1">Tiến độ học tập ổn định</p>
        </div>
      </div>

      {/* Main 2-column Grid: Form (Left) & Configuration / Integration (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Column: Edit Profile Form */}
        <div className="lg:col-span-7 bg-slate-900/90 rounded-2xl border border-slate-800 shadow-xl p-6 space-y-5">
          <div className="flex items-center gap-2 pb-3 border-b border-slate-800">
            <User className="w-5 h-5 text-emerald-400" />
            <h3 className="text-base font-bold text-white">Chỉnh Sửa Thông Tin Cố Vấn</h3>
          </div>

          <form onSubmit={handleSaveProfile} className="space-y-4 text-xs">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block font-semibold text-slate-300 mb-1.5">Họ và tên chuyên gia:</label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-750 text-slate-100 text-sm focus:border-emerald-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-300 mb-1.5">Email cơ quan:</label>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-750 text-slate-100 text-sm focus:border-emerald-500 focus:outline-none"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block font-semibold text-slate-300 mb-1.5">Chức danh / Vai trò:</label>
                <select
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-750 text-slate-100 text-sm focus:border-emerald-500 focus:outline-none"
                >
                  <option value="Trưởng ban Cố vấn Học tập">Trưởng ban Cố vấn Học tập (Lead Advisor)</option>
                  <option value="Ban Giám đốc Đào tạo">Ban Giám đốc Đào tạo (Academic Director)</option>
                  <option value="Chuyên viên Phân tích Dữ liệu">Chuyên viên Phân tích Dữ liệu (Learning Data Analyst)</option>
                  <option value="Giảng viên Phụ trách Học phần">Giảng viên Phụ trách Học phần (Course Instructor)</option>
                  <option value="Quản trị viên Enterprise">Quản trị viên Enterprise (System Admin)</option>
                </select>
              </div>

              <div>
                <label className="block font-semibold text-slate-300 mb-1.5">Số điện thoại liên hệ:</label>
                <input
                  type="text"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-750 text-slate-100 text-sm font-mono focus:border-emerald-500 focus:outline-none"
                />
              </div>
            </div>

            <div>
              <label className="block font-semibold text-slate-300 mb-1.5">Phòng ban / Đơn vị trực thuộc:</label>
              <input
                type="text"
                value={department}
                onChange={(e) => setDepartment(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-750 text-slate-100 text-sm focus:border-emerald-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="block font-semibold text-slate-300 mb-1.5">Tổ chức giáo dục / Trường đại học:</label>
              <input
                type="text"
                value={organization}
                onChange={(e) => setOrganization(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-750 text-slate-100 text-sm focus:border-emerald-500 focus:outline-none"
              />
            </div>

            <div className="pt-2">
              <button
                type="submit"
                className="flex items-center justify-center gap-2 px-6 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-sm shadow-lg shadow-emerald-600/20 transition-all"
              >
                <Save className="w-4 h-4" />
                <span>Lưu thông tin hồ sơ</span>
              </button>
            </div>
          </form>
        </div>

        {/* Right Column: Preferences & Integration */}
        <div className="lg:col-span-5 space-y-6">
          {/* Preferences Box */}
          <div className="bg-slate-900/90 rounded-2xl border border-slate-800 shadow-xl p-6 space-y-4">
            <div className="flex items-center gap-2 pb-3 border-b border-slate-800">
              <Sliders className="w-5 h-5 text-cyan-400" />
              <h3 className="text-base font-bold text-white">Cấu Hình Vận Hành Phân Tích</h3>
            </div>

            <div className="space-y-3.5 text-xs">
              <div className="flex items-center justify-between p-3 rounded-xl bg-slate-950/60 border border-slate-800">
                <div className="flex items-start gap-2.5">
                  <Bell className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                  <div>
                    <div className="font-semibold text-slate-200">Thông báo ca Nguy cơ cao</div>
                    <div className="text-[11px] text-slate-400">Gửi cảnh báo tức thì khi xác suất trượt &gt; 50%</div>
                  </div>
                </div>
                <input
                  type="checkbox"
                  checked={autoEmailAlert}
                  onChange={(e) => setAutoEmailAlert(e.target.checked)}
                  className="w-4 h-4 rounded text-emerald-500 focus:ring-emerald-500 bg-slate-900 border-slate-700"
                />
              </div>

              <div className="flex items-center justify-between p-3 rounded-xl bg-slate-950/60 border border-slate-800">
                <div className="flex items-start gap-2.5">
                  <History className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
                  <div>
                    <div className="font-semibold text-slate-200">Định dạng xuất CSV có BOM</div>
                    <div className="text-[11px] text-slate-400">Tự động chèn UTF-8 BOM hiển thị chuẩn tiếng Việt trên Excel</div>
                  </div>
                </div>
                <input
                  type="checkbox"
                  checked={csvBomFormat}
                  onChange={(e) => setCsvBomFormat(e.target.checked)}
                  className="w-4 h-4 rounded text-emerald-500 focus:ring-emerald-500 bg-slate-900 border-slate-700"
                />
              </div>
            </div>
          </div>

          {/* LMS Integration API Key Card */}
          <div className="bg-slate-900/90 rounded-2xl border border-slate-800 shadow-xl p-6 space-y-3">
            <div className="flex items-center gap-2 pb-2 border-b border-slate-800">
              <Key className="w-5 h-5 text-purple-400" />
              <h3 className="text-base font-bold text-white">Khóa Tích Hợp LMS (API Key)</h3>
            </div>

            <p className="text-xs text-slate-400 leading-relaxed">
              Sử dụng mã bảo mật này để kết nối EduRisk AI với plugin Moodle, Canvas LMS hoặc webhook nội bộ của cơ sở đào tạo.
            </p>

            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between gap-2">
              <code className="text-xs text-emerald-300 font-mono truncate">{lmsApiKey}</code>
              <button
                type="button"
                onClick={handleCopyApiKey}
                className="p-1.5 rounded-lg bg-slate-850 hover:bg-slate-800 text-slate-300 hover:text-white transition-colors shrink-0"
                title="Sao chép API Key"
              >
                <Copy className="w-4 h-4" />
              </button>
            </div>

            <div className="text-[11px] text-slate-400">
              Chuẩn tương thích: <span className="text-slate-300 font-medium">IMS LTI 1.3 Advantage &bull; REST API v1</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
