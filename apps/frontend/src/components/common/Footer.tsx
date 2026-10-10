import React, { useState } from 'react';
import { useApp, NavigationPage } from '../../state/AppContext';
import {
  GraduationCap,
  ShieldCheck,
  Server,
  Mail,
  Phone,
  ArrowRight,
  ExternalLink,
  Lock,
  Globe,
  Award,
  Terminal,
  CheckCircle2,
  Send,
} from 'lucide-react';

export const Footer: React.FC = () => {
  const { setCurrentView, addToast } = useApp();
  const [newsletterEmail, setNewsletterEmail] = useState('');

  const handleNav = (view: NavigationPage) => {
    setCurrentView(view);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleSubscribe = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newsletterEmail.trim()) return;
    addToast(
      `Cảm ơn bạn! Báo cáo xu hướng AI Giáo dục sẽ được gửi tới: ${newsletterEmail}`,
      'success'
    );
    setNewsletterEmail('');
  };

  return (
    <footer className="mt-20 border-t border-slate-800 bg-slate-950 text-slate-400 text-xs relative overflow-hidden">
      {/* Background glow effects */}
      <div className="absolute top-0 left-1/4 w-96 h-96 bg-emerald-500/5 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-cyan-500/5 rounded-full blur-3xl pointer-events-none" />

      {/* 1. Top Enterprise Callout / Newsletter Banner */}
      <div className="border-b border-slate-800/80 bg-gradient-to-r from-slate-900/90 via-slate-950 to-slate-900/90">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
          <div className="flex flex-col lg:flex-row items-center justify-between gap-6">
            <div className="space-y-2 text-center lg:text-left max-w-xl">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-[11px] font-semibold">
                <Award className="w-3.5 h-3.5" />
                <span>Giải pháp AI Quản trị Rủi ro Đào tạo Tiên phong</span>
              </div>
              <h3 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
                Sẵn sàng Tối ưu Tỷ lệ Tốt nghiệp &amp; Giữ chân Học viên?
              </h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Nhận tài liệu kỹ thuật, nghiên cứu thực nghiệm mô hình HCO-VNLS và bản tin phân tích rủi ro học tập định kỳ dành cho các cơ sở giáo dục.
              </p>
            </div>

            {/* Newsletter Input Form */}
            <form
              onSubmit={handleSubscribe}
              className="flex flex-col sm:flex-row items-center gap-2 w-full lg:w-auto max-w-md"
            >
              <div className="relative w-full sm:w-72">
                <Mail className="w-4 h-4 text-slate-500 absolute left-3.5 top-3.5" />
                <input
                  type="email"
                  required
                  value={newsletterEmail}
                  onChange={(e) => setNewsletterEmail(e.target.value)}
                  placeholder="contact@university.edu.vn"
                  className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-slate-900 border border-slate-750 text-slate-200 text-xs focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500 transition-all placeholder:text-slate-500"
                />
              </div>
              <button
                type="submit"
                className="w-full sm:w-auto flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs shadow-lg shadow-emerald-600/20 transition-all shrink-0"
              >
                <span>Đăng ký nhận tin</span>
                <Send className="w-3.5 h-3.5" />
              </button>
            </form>
          </div>
        </div>
      </div>

      {/* 2. Main Multi-Column Corporate Links Grid */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-14">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-12 gap-10">
          {/* Column 1: Brand & Enterprise Profile (4 cols) */}
          <div className="lg:col-span-4 space-y-4">
            <div
              onClick={() => handleNav('home')}
              className="flex items-center gap-3 cursor-pointer group w-fit"
            >
              <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-400 flex items-center justify-center shadow-lg shadow-emerald-500/20 group-hover:scale-105 transition-transform">
                <GraduationCap className="w-6 h-6 text-white" />
              </div>
              <div>
                <div className="flex items-center gap-1.5 font-bold tracking-tight text-white text-base leading-tight">
                  <span>EduRisk AI Platform</span>
                  <span className="px-1.5 py-0.2 text-[9px] font-extrabold uppercase rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                    Enterprise
                  </span>
                </div>
                <p className="text-[10px] text-slate-400 font-mono">
                  Educational Intelligence &amp; Retention Analytics
                </p>
              </div>
            </div>

            <p className="text-xs text-slate-400 leading-relaxed max-w-sm">
              Hệ thống trí tuệ nhân tạo chuyên sâu hỗ trợ các trường đại học, học viện và tổ chức đào tạo phát hiện sớm nguy cơ trượt/bỏ học và tự động kê đơn can thiệp sư phạm cá nhân hóa.
            </p>

            {/* Corporate Compliance Badges */}
            <div className="flex flex-wrap items-center gap-2 pt-1 text-[10px] text-slate-400">
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-slate-900 border border-slate-800">
                <ShieldCheck className="w-3 h-3 text-cyan-400" />
                <span>ISO/IEC 27001</span>
              </span>
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-slate-900 border border-slate-800">
                <Lock className="w-3 h-3 text-purple-400" />
                <span>GDPR / FERPA</span>
              </span>
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-slate-900 border border-slate-800">
                <Server className="w-3 h-3 text-emerald-400" />
                <span>LTI 1.3 Advantage</span>
              </span>
            </div>
          </div>

          {/* Column 2: Giải Pháp & Tính Năng (3 cols) */}
          <div className="lg:col-span-3 space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200">
              Giải Pháp &amp; Nền Tảng
            </h4>
            <ul className="space-y-2 text-xs">
              <li>
                <button
                  type="button"
                  onClick={() => handleNav('dashboard')}
                  className="hover:text-emerald-400 transition-colors flex items-center gap-1.5"
                >
                  <ArrowRight className="w-3 h-3 text-emerald-500" />
                  <span>Dashboard Phân Tích 17 Chỉ Số</span>
                </button>
              </li>
              <li>
                <button
                  type="button"
                  onClick={() => handleNav('dashboard')}
                  className="hover:text-emerald-400 transition-colors flex items-center gap-1.5"
                >
                  <ArrowRight className="w-3 h-3 text-emerald-500" />
                  <span>Đồng Hồ Đo Rủi Ro Radial Gauge</span>
                </button>
              </li>
              <li>
                <button
                  type="button"
                  onClick={() => handleNav('dashboard')}
                  className="hover:text-emerald-400 transition-colors flex items-center gap-1.5"
                >
                  <ArrowRight className="w-3 h-3 text-emerald-500" />
                  <span>Biểu Đồ Radar Đối Sánh Năng Lực</span>
                </button>
              </li>
              <li>
                <button
                  type="button"
                  onClick={() => handleNav('dashboard')}
                  className="hover:text-emerald-400 transition-colors flex items-center gap-1.5"
                >
                  <ArrowRight className="w-3 h-3 text-emerald-500" />
                  <span>Kê Đơn Can Thiệp Sư Phạm Tự Động</span>
                </button>
              </li>
              <li>
                <button
                  type="button"
                  onClick={() => handleNav('dashboard')}
                  className="hover:text-emerald-400 transition-colors flex items-center gap-1.5"
                >
                  <ArrowRight className="w-3 h-3 text-emerald-500" />
                  <span>Xuất Báo Cáo CSV (UTF-8 BOM)</span>
                </button>
              </li>
              <li>
                <button
                  type="button"
                  onClick={() => handleNav('about')}
                  className="hover:text-emerald-400 transition-colors flex items-center gap-1.5"
                >
                  <ArrowRight className="w-3 h-3 text-emerald-500" />
                  <span>Mô Hình LightGBM Mốc Cutoff 75%</span>
                </button>
              </li>
            </ul>
          </div>

          {/* Column 3: Tích Hợp & Công Nghệ (3 cols) */}
          <div className="lg:col-span-3 space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200">
              Tích Hợp &amp; Công Nghệ
            </h4>
            <ul className="space-y-2 text-xs">
              <li>
                <button
                  type="button"
                  onClick={() => handleNav('about')}
                  className="hover:text-cyan-400 transition-colors flex items-center gap-1.5"
                >
                  <Terminal className="w-3 h-3 text-cyan-500" />
                  <span>Thuật Toán Lai HCO-VNLS</span>
                </button>
              </li>
              <li>
                <button
                  type="button"
                  onClick={() => handleNav('profile')}
                  className="hover:text-cyan-400 transition-colors flex items-center gap-1.5"
                >
                  <Terminal className="w-3 h-3 text-cyan-500" />
                  <span>Khóa Tích Hợp LMS (API Key)</span>
                </button>
              </li>
              <li>
                <a
                  href="/docs"
                  target="_blank"
                  rel="noreferrer"
                  className="hover:text-cyan-400 transition-colors flex items-center gap-1.5"
                >
                  <ExternalLink className="w-3 h-3 text-cyan-500" />
                  <span>Tài Liệu REST API (Swagger / OpenAPI)</span>
                </a>
              </li>
              <li>
                <button
                  type="button"
                  onClick={() => handleNav('contact')}
                  className="hover:text-cyan-400 transition-colors flex items-center gap-1.5"
                >
                  <CheckCircle2 className="w-3 h-3 text-cyan-500" />
                  <span>Đồng Bộ Hai Chiều Canvas &amp; Moodle</span>
                </button>
              </li>
              <li>
                <button
                  type="button"
                  onClick={() => handleNav('contact')}
                  className="hover:text-cyan-400 transition-colors flex items-center gap-1.5"
                >
                  <CheckCircle2 className="w-3 h-3 text-cyan-500" />
                  <span>Triển Khai Docker &amp; Kubernetes</span>
                </button>
              </li>
              <li>
                <button
                  type="button"
                  onClick={() => handleNav('profile')}
                  className="hover:text-cyan-400 transition-colors flex items-center gap-1.5"
                >
                  <CheckCircle2 className="w-3 h-3 text-cyan-500" />
                  <span>Phân Quyền Bảo Mật Tier 1 Access</span>
                </button>
              </li>
            </ul>
          </div>

          {/* Column 4: Liên Hệ & Hỗ Trợ Doanh Nghiệp (2 cols) */}
          <div className="lg:col-span-2 space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200">
              Liên Hệ Hợp Tác
            </h4>
            <div className="space-y-2.5 text-xs text-slate-400">
              <div className="flex items-start gap-2">
                <Phone className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
                <div>
                  <div className="text-[11px] text-slate-500">Hotline Doanh nghiệp:</div>
                  <strong className="text-slate-200 font-mono">1900 888 668</strong>
                </div>
              </div>

              <div className="flex items-start gap-2">
                <Mail className="w-3.5 h-3.5 text-cyan-400 shrink-0 mt-0.5" />
                <div>
                  <div className="text-[11px] text-slate-500">Email tư vấn:</div>
                  <code className="text-slate-300 font-mono text-[11px]">enterprise@edurisk.ai</code>
                </div>
              </div>

              <div className="pt-2">
                <button
                  type="button"
                  onClick={() => handleNav('contact')}
                  className="w-full flex items-center justify-center gap-1.5 px-3 py-2 rounded-xl bg-slate-850 hover:bg-slate-800 border border-slate-750 text-slate-200 text-xs font-semibold transition-colors"
                >
                  <span>Gửi yêu cầu Demo</span>
                  <ArrowRight className="w-3 h-3" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 3. Bottom Legal, Security & Copyright Bar */}
      <div className="border-t border-slate-800/80 bg-slate-950/95 py-6">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex flex-wrap items-center justify-center md:justify-start gap-x-6 gap-y-2 text-[11px] text-slate-400">
            <span>&copy; {new Date().getFullYear()} EduRisk AI Systems Inc. Bảo lưu mọi quyền.</span>
            <span className="hidden sm:inline text-slate-700">&bull;</span>
            <button
              type="button"
              onClick={() => handleNav('about')}
              className="hover:text-slate-200 transition-colors"
            >
              Điều khoản dịch vụ (Terms)
            </button>
            <span className="hidden sm:inline text-slate-700">&bull;</span>
            <button
              type="button"
              onClick={() => handleNav('about')}
              className="hover:text-slate-200 transition-colors"
            >
              Chính sách bảo mật dữ liệu (Privacy Policy)
            </button>
            <span className="hidden sm:inline text-slate-700">&bull;</span>
            <button
              type="button"
              onClick={() => handleNav('contact')}
              className="hover:text-slate-200 transition-colors"
            >
              Tiêu chuẩn tuân thủ (Compliance)
            </button>
          </div>

          <div className="flex items-center gap-3 text-[11px] text-slate-400">
            <span className="flex items-center gap-1 text-slate-400">
              <Globe className="w-3.5 h-3.5 text-emerald-400" />
              <span>Tiếng Việt (VN)</span>
            </span>
            <span className="text-slate-700">&bull;</span>
            <span className="font-mono text-slate-400">v2.4 Enterprise</span>
          </div>
        </div>
      </div>
    </footer>
  );
};
