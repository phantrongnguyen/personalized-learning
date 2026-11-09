import React, { useState } from 'react';
import { useApp } from '../state/AppContext';
import { loginApi, mapBackendUser } from '../services/api';
import { ThemeToggle } from '../components/common/ThemeToggle';
import {
  GraduationCap,
  User,
  Mail,
  Lock,
  Eye,
  EyeOff,
  Building,
  ArrowRight,
  AlertCircle,
} from 'lucide-react';

export const AuthPage: React.FC = () => {
  const { login, addToast, apiBase } = useApp();

  const [activeTab, setActiveTab] = useState<'login' | 'register'>('login');
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Login form state
  const [loginEmail, setLoginEmail] = useState('');
  const [loginMode, setLoginMode] = useState<'student' | 'staff'>('student');
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

  // Xác thực trực tiếp qua Backend FastAPI (JWT + RBAC)
  const authenticate = async (email: string, password: string) => {
    setErrorMsg(null);
    setLoading(true);
    try {
      const { user } = await loginApi(apiBase, email, password);
      login(mapBackendUser(user));
    } catch (err: unknown) {
      const message =
        (err as Error).message || 'Đăng nhập không thành công. Vui lòng kiểm tra lại.';
      setErrorMsg(message);
      addToast(message, 'error', 5000);
    } finally {
      setLoading(false);
    }
  };

  const handleLoginSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);

    if (!loginEmail.trim()) {
      setErrorMsg(loginMode === 'student' ? 'Vui lòng nhập mã số sinh viên.' : 'Vui lòng nhập email công tác.');
      return;
    }
    if (loginMode === 'student' && loginEmail.includes('@')) {
      setErrorMsg('Sinh viên vui lòng đăng nhập bằng mã số sinh viên, không phải email.');
      return;
    }
    if (!loginPassword) {
      setErrorMsg('Vui lòng nhập mật khẩu xác thực.');
      return;
    }

    void authenticate(loginEmail.trim(), loginPassword);
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

    // Backend hiện không mở đăng ký công khai; tài khoản do Quản trị viên cấp.
    addToast(
      'Chức năng đăng ký công khai đang tạm khóa. Vui lòng liên hệ Quản trị viên để được cấp tài khoản.',
      'info',
      6000
    );
    setErrorMsg('Đăng ký công khai tạm khóa. Tài khoản được Quản trị viên cấp qua phân hệ Admin.');
  };

  return (
    <div className="min-h-screen min-h-[100svh] bg-slate-950 text-slate-100 flex flex-col relative isolate overflow-hidden selection:bg-brand-500/30">
      <img
        src={`${import.meta.env.BASE_URL}images/login-campus-enhanced.png`}
        alt=""
        aria-hidden="true"
        fetchPriority="high"
        className="absolute inset-0 h-full w-full object-cover object-center pointer-events-none"
      />
      <div aria-hidden="true" className="absolute inset-0 bg-gradient-to-r from-slate-950/10 via-slate-950/20 to-slate-950/60 pointer-events-none" />

      <div className="absolute top-5 right-5 sm:right-10 z-20">
        <ThemeToggle />
      </div>

      {/* Main Container */}
      <main className="relative z-10 flex-1 max-w-7xl w-full mx-auto px-4 sm:px-8 lg:px-12 py-20 flex items-center justify-center">
          {/* Authentication card */}
          <div className="w-full max-w-md">
            <div className="bg-slate-900/95 border border-slate-700/60 rounded-3xl p-6 sm:p-8 shadow-2xl backdrop-blur-xl relative">

              <div className="mb-6 flex justify-center">
                <img
                  src={`${import.meta.env.BASE_URL}images/huit.jpg`}
                  alt="Logo Trường Đại học Công Thương TP. Hồ Chí Minh (HUIT)"
                  width={304}
                  height={304}
                  className="theme-logo h-20 w-20 sm:h-24 sm:w-24 object-contain"
                />
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
                      ? 'bg-brand-600 text-white shadow-md'
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
                      ? 'bg-brand-600 text-white shadow-md'
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
                    <label htmlFor="login-mode" className="block text-xs font-semibold text-slate-300 mb-1.5">Loại tài khoản:</label>
                    <select id="login-mode" value={loginMode} disabled={loading} onChange={e => {
                      setLoginMode(e.target.value as 'student' | 'staff');
                      setLoginEmail(''); setLoginPassword(''); setErrorMsg(null);
                    }} className="w-full px-4 py-2.5 rounded-xl bg-slate-950 border border-slate-750 text-slate-100 text-sm">
                      <option value="student">Sinh viên</option>
                      <option value="staff">Giảng viên / Cố vấn / Quản trị viên</option>
                    </select>
                  </div>
                  <div>
                    <label htmlFor="login-username" className="block text-xs font-semibold text-slate-300 mb-1.5">
                      {loginMode === 'student' ? 'Mã số sinh viên' : 'Email công tác:'}
                    </label>
                    <div className="relative">
                      {loginMode === 'student' ? <GraduationCap className="w-4 h-4 text-slate-500 absolute left-3.5 top-3.5" /> : <Mail className="w-4 h-4 text-slate-500 absolute left-3.5 top-3.5" />}
                      <input
                        id="login-username"
                        type={loginMode === 'student' ? 'text' : 'email'}
                        autoComplete="username"
                        autoCapitalize="none"
                        spellCheck={false}
                        disabled={loading}
                        required
                        value={loginEmail}
                        onChange={(e) => setLoginEmail(e.target.value)}
                        placeholder={loginMode === 'student' ? 'Nhập mã số sinh viên' : 'Nhập email công tác'}
                        className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-slate-950 border border-slate-750 text-slate-100 text-sm placeholder:text-slate-600 focus:border-brand-500 focus:outline-none transition-colors"
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
                            'Vui lòng liên hệ quản trị viên để được hỗ trợ đặt lại mật khẩu.',
                            'info'
                          )
                        }
                        className="text-[11px] text-brand-400 hover:underline"
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
                        className="w-full pl-10 pr-10 py-2.5 rounded-xl bg-slate-950 border border-slate-750 text-slate-100 text-sm placeholder:text-slate-600 focus:border-brand-500 focus:outline-none transition-colors"
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
                        className="rounded border-slate-700 text-brand-600 focus:ring-brand-500 w-4 h-4 bg-slate-950"
                      />
                      <span>Ghi nhớ đăng nhập</span>
                    </label>
                  </div>

                  <button
                    type="submit"
                    disabled={loading}
                    className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-brand-600 to-brand-600 hover:from-brand-500 hover:to-brand-500 text-white font-bold text-sm shadow-xl shadow-brand-600/25 flex items-center justify-center gap-2 transition-all hover:scale-[1.01] disabled:opacity-50"
                  >
                    {loading ? (
                      <span>Đang đăng nhập…</span>
                    ) : (
                      <>
                        <span>Đăng nhập</span>
                        <ArrowRight className="w-4 h-4" />
                      </>
                    )}
                  </button>

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
                          placeholder=""
                          className="w-full pl-9 pr-3 py-2 rounded-xl bg-slate-950 border border-slate-750 text-slate-100 text-xs focus:border-brand-500 focus:outline-none"
                        />
                      </div>
                    </div>

                    <div>
                      <label className="block text-xs font-semibold text-slate-300 mb-1">
                        Mã số sinh viên
                      </label>
                      <input
                        type="text"
                        value={regStudentId}
                        onChange={(e) => setRegStudentId(e.target.value)}
                        placeholder=""
                        className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-750 text-slate-100 text-xs focus:border-brand-500 focus:outline-none"
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
                        placeholder=""
                        className="w-full pl-9 pr-3 py-2 rounded-xl bg-slate-950 border border-slate-750 text-slate-100 text-xs focus:border-brand-500 focus:outline-none"
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
                        className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-750 text-slate-100 text-xs focus:border-brand-500 focus:outline-none"
                      >
                        <option value="Trưởng ban Cố vấn Học tập">Trưởng ban Cố vấn Học tập</option>
                        <option value="Giảng viên Phụ trách Học phần">Giảng viên Phụ trách</option>
                        <option value="Chuyên viên Phân tích Dữ liệu">Chuyên viên Dữ liệu</option>
                        <option value="Sinh viên">Sinh viên</option>
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
                          placeholder=""
                          className="w-full pl-9 pr-3 py-2 rounded-xl bg-slate-950 border border-slate-750 text-slate-100 text-xs focus:border-brand-500 focus:outline-none"
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
                          className="w-full pl-9 pr-8 py-2 rounded-xl bg-slate-950 border border-slate-750 text-slate-100 text-xs focus:border-brand-500 focus:outline-none"
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
                        className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-750 text-slate-100 text-xs focus:border-brand-500 focus:outline-none"
                      />
                    </div>
                  </div>

                  <label className="flex items-start gap-2 cursor-pointer select-none pt-1">
                    <input
                      type="checkbox"
                      checked={regAgreeTerms}
                      onChange={(e) => setRegAgreeTerms(e.target.checked)}
                      className="rounded border-slate-700 text-brand-600 focus:ring-brand-500 w-4 h-4 bg-slate-950 mt-0.5"
                    />
                    <span className="text-[11px] text-slate-400 leading-tight">
                      Tôi đồng ý với Quy chuẩn Bảo mật Dữ liệu Học thuật &amp; Tuân thủ quy định đạo đức trí tuệ nhân tạo (AI Ethics).
                    </span>
                  </label>

                  <button
                    type="submit"
                    disabled={loading}
                    className="w-full py-2.5 px-4 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-bold text-xs shadow-lg shadow-brand-600/20 flex items-center justify-center gap-2 transition-all mt-2 disabled:opacity-50"
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

            </div>
          </div>
      </main>
    </div>
  );
};
