import React, { useState } from 'react';
import { useApp } from '../state/AppContext';
import {
  GraduationCap,
  ShieldCheck,
  UserCheck,
  User,
  Mail,
  Lock,
  Eye,
  EyeOff,
  Building,
  ArrowRight,
  Sparkles,
  BrainCircuit,
  TrendingUp,
  Cpu,
  Layers,
  CheckCircle2,
  AlertCircle,
  Compass,
} from 'lucide-react';

export const AuthPage: React.FC = () => {
  const { login, addToast } = useApp();

  const [activeTab, setActiveTab] = useState<'login' | 'register'>('login');
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Login form state
  const [loginEmail, setLoginEmail] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [showLoginPassword, setShowLoginPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);

  // Register form state
  const [regName, setRegName] = useState('');
  const [regStudentId, setRegStudentId] = useState('');
  const [regEmail, setRegEmail] = useState('');
  const [regRole, setRegRole] = useState('Trưởng ban Cố vấn Học tập');
  const [regDepartment, setRegDepartment] = useState('Khoa Công nghệ Thông tin');
  const [regPassword, setRegPassword] = useState('');
  const [regConfirmPassword, setRegConfirmPassword] = useState('');
  const [showRegPassword, setShowRegPassword] = useState(false);
  const [regAgreeTerms, setRegAgreeTerms] = useState(true);

  // 1-Click Demo Accounts
  const handleQuickLogin = (
    name: string,
    email: string,
    role: string,
    initials: string,
    department: string
  ) => {
    setLoading(true);
    setTimeout(() => {
      login({
        name,
        email,
        role,
        initials,
        department,
        organization: 'Đại học Quốc gia & Viện Công nghệ Đào tạo',
        phone: '0908 686 888',
      });
      setLoading(false);
    }, 400);
  };

  const handleLoginSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);

    if (!loginEmail.trim()) {
      setErrorMsg('Vui lòng nhập địa chỉ Email hoặc Mã tài khoản.');
      return;
    }
    if (!loginPassword) {
      setErrorMsg('Vui lòng nhập mật khẩu xác thực.');
      return;
    }

    setLoading(true);
    setTimeout(() => {
      const emailPrefix = loginEmail.split('@')[0] || 'User';
      const formattedName =
        emailPrefix.charAt(0).toUpperCase() + emailPrefix.slice(1).replace(/[._]/g, ' ');
      const initials = formattedName
        .split(' ')
        .map((w) => w[0])
        .join('')
        .slice(0, 2)
        .toUpperCase() || 'US';

      login({
        name: formattedName,
        email: loginEmail,
        role: loginEmail.includes('admin')
          ? 'Quản trị viên Enterprise'
          : loginEmail.includes('student')
          ? 'Sinh viên'
          : 'Cố vấn học tập',
        initials,
        department: 'Ban Đào tạo & Công tác Sinh viên',
        organization: 'Học viện & Trường Đại học Đối tác',
      });
      setLoading(false);
    }, 600);
  };

  const handleRegisterSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);

    if (!regName.trim()) {
      setErrorMsg('Vui lòng nhập họ và tên của bạn.');
      return;
    }
    if (!regEmail.trim()) {
      setErrorMsg('Vui lòng nhập địa chỉ Email trường học.');
      return;
    }
    if (regPassword.length < 6) {
      setErrorMsg('Mật khẩu cần tối thiểu 6 ký tự để đảm bảo an toàn.');
      return;
    }
    if (regPassword !== regConfirmPassword) {
      setErrorMsg('Mật khẩu và xác nhận mật khẩu không khớp.');
      return;
    }
    if (!regAgreeTerms) {
      setErrorMsg('Vui lòng đồng ý với Điều khoản bảo mật & cam kết dữ liệu học thuật.');
      return;
    }

    setLoading(true);
    setTimeout(() => {
      const initials =
        regName
          .trim()
          .split(' ')
          .map((p) => p[0])
          .join('')
          .slice(0, 2)
          .toUpperCase() || 'SV';

      login({
        name: regName.trim(),
        email: regEmail.trim(),
        role: regRole,
        initials,
        department: regDepartment,
        organization: 'Cơ sở Giáo dục Đại học Đối tác',
      });
      setLoading(false);
      addToast('Đăng ký tài khoản thành công! Chào mừng bạn gia nhập EduRisk AI.', 'success');
    }, 700);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-between relative overflow-hidden selection:bg-emerald-500/30">
      {/* Background Glow Orbs */}
      <div className="absolute top-[-10%] left-[-10%] w-[45vw] h-[45vw] rounded-full bg-emerald-600/10 blur-[130px] pointer-events-none" />
      <div className="absolute bottom-[-15%] right-[-10%] w-[50vw] h-[50vw] rounded-full bg-teal-600/10 blur-[140px] pointer-events-none" />
      <div className="absolute top-[30%] right-[20%] w-[30vw] h-[30vw] rounded-full bg-cyan-600/5 blur-[120px] pointer-events-none" />

      {/* Top Bar / Brand header */}
      <header className="relative z-10 w-full border-b border-slate-800/80 bg-slate-950/70 backdrop-blur-md px-4 sm:px-8 py-3.5 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-400 p-[1px] shadow-lg shadow-emerald-500/20">
            <div className="w-full h-full bg-slate-950 rounded-[11px] flex items-center justify-center">
              <GraduationCap className="w-5 h-5 text-emerald-400" />
            </div>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-extrabold text-base tracking-tight text-white">
                EduRisk <span className="text-emerald-400">AI</span>
              </span>
              <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 font-semibold">
                Enterprise
              </span>
            </div>
            <p className="text-[11px] text-slate-400 hidden sm:block">
              Nền tảng Quản trị Rủi ro Đào tạo &amp; Cá nhân hóa Học tập
            </p>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="relative z-10 flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 lg:py-12 flex items-center justify-center">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-12 items-center w-full">
          
          {/* Left Column: Solution Highlights & Scientific Metrics (7 cols on lg) */}
          <div className="lg:col-span-6 space-y-6 text-left">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-semibold">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Hệ thống Khuyến nghị Học tập Thông minh &bull; KLTN 2026</span>
            </div>

            <h1 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold text-white tracking-tight leading-tight">
              Phát Hiện Sớm Rủi Ro &amp;{' '}
              <span className="bg-gradient-to-r from-emerald-400 via-teal-300 to-cyan-400 bg-clip-text text-transparent">
                Can Thiệp Cá Nhân Hóa
              </span>
            </h1>

            <p className="text-slate-300 text-sm sm:text-base leading-relaxed">
              Giải pháp kết hợp mô hình phân lớp <strong className="text-white">LightGBM</strong> tại mốc Cutoff 75% thời lượng môn học và thuật toán tối ưu hóa siêu tham số lai <strong className="text-emerald-400">HCO-VNLS</strong>, giúp ban cố vấn học tập chủ động ngăn chặn nguy cơ trượt/bỏ học của sinh viên.
            </p>

            {/* KPI Performance Metrics */}
            <div className="grid grid-cols-3 gap-3 pt-2">
              <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 shadow-sm">
                <div className="text-[11px] text-slate-400 font-semibold flex items-center justify-between mb-1">
                  <span>Accuracy</span>
                  <TrendingUp className="w-3.5 h-3.5 text-emerald-400" />
                </div>
                <div className="text-xl sm:text-2xl font-bold font-mono text-emerald-400">93.04%</div>
                <div className="text-[10px] text-slate-400">Kiểm thử OULAD</div>
              </div>

              <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 shadow-sm">
                <div className="text-[11px] text-slate-400 font-semibold flex items-center justify-between mb-1">
                  <span>ROC-AUC</span>
                  <BrainCircuit className="w-3.5 h-3.5 text-cyan-400" />
                </div>
                <div className="text-xl sm:text-2xl font-bold font-mono text-cyan-400">0.9785</div>
                <div className="text-[10px] text-slate-400">Phân tách nhãn rủi ro</div>
              </div>

              <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 shadow-sm">
                <div className="text-[11px] text-slate-400 font-semibold flex items-center justify-between mb-1">
                  <span>Tối ưu hóa</span>
                  <Cpu className="w-3.5 h-3.5 text-amber-400" />
                </div>
                <div className="text-xl sm:text-2xl font-bold font-mono text-amber-400">HCO-VNLS</div>
                <div className="text-[10px] text-slate-400">Rút gọn 86.7% chiều</div>
              </div>
            </div>

            {/* 4 Pillars Feature List */}
            <div className="space-y-3 pt-2">
              <div className="flex items-start gap-3">
                <div className="p-1.5 rounded-lg bg-emerald-500/10 text-emerald-400 mt-0.5 shrink-0">
                  <CheckCircle2 className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-xs font-semibold text-slate-200">
                    Dự báo chính xác tại Cutoff 75% thời lượng học phần
                  </div>
                  <div className="text-[11px] text-slate-400">
                    Phân tích toàn diện chỉ số click VLE, bài tập nộp trễ và tương tác học tập trực tuyến.
                  </div>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <div className="p-1.5 rounded-lg bg-teal-500/10 text-teal-400 mt-0.5 shrink-0">
                  <Compass className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-xs font-semibold text-slate-200">
                    Chiến lược can thiệp theo 4 nhóm trọng tâm
                  </div>
                  <div className="text-[11px] text-slate-400">
                    Đề xuất giải pháp thiết thực: Chuyên cần, Học thuật, Tiến độ và Động lực học tập.
                  </div>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <div className="p-1.5 rounded-lg bg-cyan-500/10 text-cyan-400 mt-0.5 shrink-0">
                  <Layers className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-xs font-semibold text-slate-200">
                    Tích hợp sẵn sàng chuẩn LMS LTI 1.3
                  </div>
                  <div className="text-[11px] text-slate-400">
                    Kết nối an toàn với Canvas LMS, Moodle, Blackboard và cơ sở dữ liệu đào tạo.
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column: Authentication Card (6 cols on lg) */}
          <div className="lg:col-span-6 w-full max-w-lg mx-auto">
            <div className="bg-slate-900/90 border border-slate-800 rounded-3xl p-6 sm:p-8 shadow-2xl backdrop-blur-xl relative">
              
              {/* 1-Click Fast Demo Accounts Bar */}
              <div className="mb-6 p-4 rounded-2xl bg-slate-950/70 border border-slate-800/80 space-y-2.5">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-bold text-emerald-400 uppercase tracking-wider flex items-center gap-1.5">
                    <Sparkles className="w-3.5 h-3.5" />
                    Khởi Chạy Nhanh (1-Click Demo)
                  </span>
                  <span className="text-[10px] text-slate-400">Không cần mật khẩu</span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                  <button
                    type="button"
                    disabled={loading}
                    onClick={() =>
                      handleQuickLogin(
                        'TS. Nguyễn Minh Khang',
                        'lead.advisor@edurisk.ai',
                        'Trưởng ban Cố vấn Học tập',
                        'MK',
                        'Ban Quản trị & Cố vấn Đào tạo'
                      )
                    }
                    className="flex flex-col p-2.5 rounded-xl bg-slate-850 hover:bg-slate-800 border border-slate-750 hover:border-emerald-500/50 text-left transition-all group"
                  >
                    <div className="flex items-center gap-1.5 text-xs font-bold text-slate-200 group-hover:text-emerald-300">
                      <UserCheck className="w-3.5 h-3.5 text-emerald-400" />
                      <span>Cố vấn</span>
                    </div>
                    <span className="text-[10px] text-slate-400 truncate mt-0.5">TS. Minh Khang</span>
                  </button>

                  <button
                    type="button"
                    disabled={loading}
                    onClick={() =>
                      handleQuickLogin(
                        'Trần Hoàng Nam',
                        'admin@edurisk.ai',
                        'Quản trị viên Enterprise',
                        'AD',
                        'Phòng CNTT & Đảm bảo Chất lượng'
                      )
                    }
                    className="flex flex-col p-2.5 rounded-xl bg-slate-850 hover:bg-slate-800 border border-slate-750 hover:border-teal-500/50 text-left transition-all group"
                  >
                    <div className="flex items-center gap-1.5 text-xs font-bold text-slate-200 group-hover:text-teal-300">
                      <ShieldCheck className="w-3.5 h-3.5 text-teal-400" />
                      <span>Quản trị viên</span>
                    </div>
                    <span className="text-[10px] text-slate-400 truncate mt-0.5">Admin Đào tạo</span>
                  </button>

                  <button
                    type="button"
                    disabled={loading}
                    onClick={() =>
                      handleQuickLogin(
                        'Lê Thu Hà',
                        'thuha.le@edurisk.ai',
                        'Sinh viên',
                        'TH',
                        'Khoa Công nghệ Thông tin (K65)'
                      )
                    }
                    className="flex flex-col p-2.5 rounded-xl bg-slate-850 hover:bg-slate-800 border border-slate-750 hover:border-cyan-500/50 text-left transition-all group"
                  >
                    <div className="flex items-center gap-1.5 text-xs font-bold text-slate-200 group-hover:text-cyan-300">
                      <GraduationCap className="w-3.5 h-3.5 text-cyan-400" />
                      <span>Sinh viên</span>
                    </div>
                    <span className="text-[10px] text-slate-400 truncate mt-0.5">Lê Thu Hà (K65)</span>
                  </button>
                </div>
              </div>

              {/* Tabs: Đăng nhập vs Đăng ký */}
              <div className="flex p-1 bg-slate-950/80 rounded-xl border border-slate-800 mb-6">
                <button
                  type="button"
                  onClick={() => {
                    setActiveTab('login');
                    setErrorMsg(null);
                  }}
                  className={`flex-1 py-2 text-xs font-bold rounded-lg transition-all ${
                    activeTab === 'login'
                      ? 'bg-emerald-600 text-white shadow-md'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  Đăng nhập
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setActiveTab('register');
                    setErrorMsg(null);
                  }}
                  className={`flex-1 py-2 text-xs font-bold rounded-lg transition-all ${
                    activeTab === 'register'
                      ? 'bg-emerald-600 text-white shadow-md'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  Đăng ký tài khoản
                </button>
              </div>

              {/* Error Alert */}
              {errorMsg && (
                <div className="mb-4 p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <span>{errorMsg}</span>
                </div>
              )}

              {/* Form 1: LOGIN */}
              {activeTab === 'login' && (
                <form onSubmit={handleLoginSubmit} className="space-y-4">
                  <div>
                    <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                      Email hoặc Mã tài khoản:
                    </label>
                    <div className="relative">
                      <Mail className="w-4 h-4 text-slate-500 absolute left-3.5 top-3.5" />
                      <input
                        type="email"
                        required
                        value={loginEmail}
                        onChange={(e) => setLoginEmail(e.target.value)}
                        placeholder="advisor@university.edu.vn"
                        className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-slate-950 border border-slate-750 text-slate-100 text-sm placeholder:text-slate-600 focus:border-emerald-500 focus:outline-none transition-colors"
                      />
                    </div>
                  </div>

                  <div>
                    <div className="flex items-center justify-between mb-1.5">
                      <label className="block text-xs font-semibold text-slate-300">
                        Mật khẩu:
                      </label>
                      <button
                        type="button"
                        onClick={() =>
                          addToast(
                            'Để thuận tiện kiểm thử, bạn có thể bấm nút "1-Click Demo" phía trên hoặc nhập mật khẩu bất kỳ.',
                            'info'
                          )
                        }
                        className="text-[11px] text-emerald-400 hover:underline"
                      >
                        Quên mật khẩu?
                      </button>
                    </div>
                    <div className="relative">
                      <Lock className="w-4 h-4 text-slate-500 absolute left-3.5 top-3.5" />
                      <input
                        type={showLoginPassword ? 'text' : 'password'}
                        required
                        value={loginPassword}
                        onChange={(e) => setLoginPassword(e.target.value)}
                        placeholder="••••••••••••"
                        className="w-full pl-10 pr-10 py-2.5 rounded-xl bg-slate-950 border border-slate-750 text-slate-100 text-sm placeholder:text-slate-600 focus:border-emerald-500 focus:outline-none transition-colors"
                      />
                      <button
                        type="button"
                        onClick={() => setShowLoginPassword(!showLoginPassword)}
                        className="absolute right-3.5 top-3.5 text-slate-500 hover:text-slate-300"
                        title={showLoginPassword ? 'Ẩn mật khẩu' : 'Hiện mật khẩu'}
                      >
                        {showLoginPassword ? (
                          <EyeOff className="w-4 h-4" />
                        ) : (
                          <Eye className="w-4 h-4" />
                        )}
                      </button>
                    </div>
                  </div>

                  <div className="flex items-center justify-between text-xs text-slate-400 pt-1">
                    <label className="flex items-center gap-2 cursor-pointer select-none">
                      <input
                        type="checkbox"
                        checked={rememberMe}
                        onChange={(e) => setRememberMe(e.target.checked)}
                        className="rounded border-slate-700 text-emerald-600 focus:ring-emerald-500 w-4 h-4 bg-slate-950"
                      />
                      <span>Ghi nhớ phiên đăng nhập (30 ngày)</span>
                    </label>
                  </div>

                  <button
                    type="submit"
                    disabled={loading}
                    className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-bold text-sm shadow-xl shadow-emerald-600/25 flex items-center justify-center gap-2 transition-all hover:scale-[1.01] disabled:opacity-50"
                  >
                    {loading ? (
                      <span>Đang xác thực hệ thống…</span>
                    ) : (
                      <>
                        <span>Đăng nhập vào Hệ thống</span>
                        <ArrowRight className="w-4 h-4" />
                      </>
                    )}
                  </button>

                  {/* Fast Guest Mode Link */}
                  <div className="text-center pt-2">
                    <button
                      type="button"
                      onClick={() =>
                        handleQuickLogin(
                          'Khách Trải Nghiệm',
                          'guest@edurisk.ai',
                          'Cố vấn tham quan',
                          'GE',
                          'Tài khoản duyệt thử nghiệm'
                        )
                      }
                      className="text-xs text-slate-400 hover:text-emerald-400 transition-colors inline-flex items-center gap-1.5"
                    >
                      <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
                      <span>Duyệt nhanh với tư cách Khách tham quan (Guest Mode)</span>
                    </button>
                  </div>
                </form>
              )}

              {/* Form 2: REGISTER */}
              {activeTab === 'register' && (
                <form onSubmit={handleRegisterSubmit} className="space-y-3.5">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div>
                      <label className="block text-xs font-semibold text-slate-300 mb-1">
                        Họ và tên:
                      </label>
                      <div className="relative">
                        <User className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
                        <input
                          type="text"
                          required
                          value={regName}
                          onChange={(e) => setRegName(e.target.value)}
                          placeholder="Nguyễn Văn A"
                          className="w-full pl-9 pr-3 py-2 rounded-xl bg-slate-950 border border-slate-750 text-slate-100 text-xs focus:border-emerald-500 focus:outline-none"
                        />
                      </div>
                    </div>

                    <div>
                      <label className="block text-xs font-semibold text-slate-300 mb-1">
                        Mã định danh (MSSV/CB):
                      </label>
                      <input
                        type="text"
                        value={regStudentId}
                        onChange={(e) => setRegStudentId(e.target.value)}
                        placeholder="VD: 20210088 hoặc CB-991"
                        className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-750 text-slate-100 text-xs focus:border-emerald-500 focus:outline-none"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-300 mb-1">
                      Email trường học / tổ chức:
                    </label>
                    <div className="relative">
                      <Mail className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
                      <input
                        type="email"
                        required
                        value={regEmail}
                        onChange={(e) => setRegEmail(e.target.value)}
                        placeholder="nguyenvana@university.edu.vn"
                        className="w-full pl-9 pr-3 py-2 rounded-xl bg-slate-950 border border-slate-750 text-slate-100 text-xs focus:border-emerald-500 focus:outline-none"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div>
                      <label className="block text-xs font-semibold text-slate-300 mb-1">
                        Vai trò chuyên trách:
                      </label>
                      <select
                        value={regRole}
                        onChange={(e) => setRegRole(e.target.value)}
                        className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-750 text-slate-100 text-xs focus:border-emerald-500 focus:outline-none"
                      >
                        <option value="Trưởng ban Cố vấn Học tập">Trưởng ban Cố vấn Học tập</option>
                        <option value="Giảng viên Phụ trách Học phần">Giảng viên Phụ trách</option>
                        <option value="Chuyên viên Phân tích Dữ liệu">Chuyên viên Dữ liệu</option>
                        <option value="Sinh viên">Sinh viên / Học viên</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-xs font-semibold text-slate-300 mb-1">
                        Khoa / Viện đào tạo:
                      </label>
                      <div className="relative">
                        <Building className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
                        <input
                          type="text"
                          value={regDepartment}
                          onChange={(e) => setRegDepartment(e.target.value)}
                          placeholder="Khoa CNTT"
                          className="w-full pl-9 pr-3 py-2 rounded-xl bg-slate-950 border border-slate-750 text-slate-100 text-xs focus:border-emerald-500 focus:outline-none"
                        />
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div>
                      <label className="block text-xs font-semibold text-slate-300 mb-1">
                        Mật khẩu:
                      </label>
                      <div className="relative">
                        <Lock className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
                        <input
                          type={showRegPassword ? 'text' : 'password'}
                          required
                          value={regPassword}
                          onChange={(e) => setRegPassword(e.target.value)}
                          placeholder="••••••••"
                          className="w-full pl-9 pr-8 py-2 rounded-xl bg-slate-950 border border-slate-750 text-slate-100 text-xs focus:border-emerald-500 focus:outline-none"
                        />
                        <button
                          type="button"
                          onClick={() => setShowRegPassword(!showRegPassword)}
                          className="absolute right-2.5 top-3 text-slate-500 hover:text-slate-300"
                        >
                          {showRegPassword ? (
                            <EyeOff className="w-3.5 h-3.5" />
                          ) : (
                            <Eye className="w-3.5 h-3.5" />
                          )}
                        </button>
                      </div>
                    </div>

                    <div>
                      <label className="block text-xs font-semibold text-slate-300 mb-1">
                        Xác nhận mật khẩu:
                      </label>
                      <input
                        type={showRegPassword ? 'text' : 'password'}
                        required
                        value={regConfirmPassword}
                        onChange={(e) => setRegConfirmPassword(e.target.value)}
                        placeholder="••••••••"
                        className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-750 text-slate-100 text-xs focus:border-emerald-500 focus:outline-none"
                      />
                    </div>
                  </div>

                  <label className="flex items-start gap-2 cursor-pointer select-none pt-1">
                    <input
                      type="checkbox"
                      checked={regAgreeTerms}
                      onChange={(e) => setRegAgreeTerms(e.target.checked)}
                      className="rounded border-slate-700 text-emerald-600 focus:ring-emerald-500 w-4 h-4 bg-slate-950 mt-0.5"
                    />
                    <span className="text-[11px] text-slate-400 leading-tight">
                      Tôi đồng ý với Quy chuẩn Bảo mật Dữ liệu Học thuật &amp; Tuân thủ quy định đạo đức trí tuệ nhân tạo (AI Ethics).
                    </span>
                  </label>

                  <button
                    type="submit"
                    disabled={loading}
                    className="w-full py-2.5 px-4 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs shadow-lg shadow-emerald-600/20 flex items-center justify-center gap-2 transition-all mt-2 disabled:opacity-50"
                  >
                    {loading ? (
                      <span>Đang tạo tài khoản…</span>
                    ) : (
                      <>
                        <span>Tạo tài khoản &amp; Truy cập ngay</span>
                        <ArrowRight className="w-4 h-4" />
                      </>
                    )}
                  </button>
                </form>
              )}

              {/* Bottom Security Info */}
              <div className="mt-6 pt-4 border-t border-slate-800/80 flex items-center justify-between text-[10px] text-slate-400">
                <span className="flex items-center gap-1">
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                  Mã hóa cấp Enterprise
                </span>
                <span>Chuẩn LTI 1.3 / IMS Global</span>
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="relative z-10 w-full border-t border-slate-800/80 bg-slate-950/80 backdrop-blur-md px-4 sm:px-8 py-3 text-center text-xs text-slate-400">
        EduRisk AI Enterprise &copy; 2026 &bull; Khóa luận Tốt nghiệp Đại học KLTN-13 &bull; Tối ưu hóa can thiệp học tập cá nhân hóa
      </footer>
    </div>
  );
};
