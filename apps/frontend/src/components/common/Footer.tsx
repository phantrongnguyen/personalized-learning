import React, { useState } from 'react';
import { useApp, NavigationPage } from '../../state/AppContext';
import { BrandLogo } from './BrandLogo';
import {
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
  const { apiBase, setCurrentView, addToast } = useApp();
  const [newsletterEmail, setNewsletterEmail] = useState('');

  const handleNav = (view: NavigationPage) => {
    setCurrentView(view);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleSubscribe = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newsletterEmail.trim()) return;
    addToast(
      `Biểu mẫu minh họa chưa kết nối dịch vụ gửi tin; chưa có email nào được gửi`,
      'info'
    );
    setNewsletterEmail('');
  };

  return (
    <footer className="mt-20 border-t border-slate-800 bg-slate-950 text-slate-400 text-xs relative overflow-hidden">
      {/* Background glow effects */}
      <div className="absolute top-0 left-1/4 w-96 h-96 bg-brand-500/5 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-cyan-500/5 rounded-full blur-3xl pointer-events-none" />

      {/* 1. Top Enterprise Callout / Newsletter Banner */}
      <div className="border-b border-slate-800/80 bg-gradient-to-r from-slate-900/90 via-slate-950 to-slate-900/90">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
          <div className="flex flex-col lg:flex-row items-center justify-between gap-6">
            <div className="space-y-2 text-center lg:text-left max-w-xl">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-500/10 border border-brand-500/20 text-brand-400 text-[11px] font-semibold">
                <Award className="w-3.5 h-3.5" />
                <span>Dự án nghiên cứu hỗ trợ quyết định học tập</span>
              </div>
              <h3 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
                Dữ liệu học tập, gợi ý có căn cứ
              </h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Đây là ứng dụng nghiên cứu. Dự báo và gợi ý cần được giảng viên kiểm tra trước khi quyết định hỗ trợ. Biểu mẫu nhận tin chưa kết nối dịch vụ gửi email; không nhập email cá nhân thật.
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
                  className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-slate-900 border border-slate-750 text-slate-200 text-xs focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 transition-all placeholder:text-slate-500"
                />
              </div>
              <button
                type="submit"
                className="w-full sm:w-auto flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-bold text-xs shadow-lg shadow-brand-600/20 transition-all shrink-0"
              >
                <span>Xem thử biểu mẫu</span>
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
              <BrandLogo className="w-[239px] max-w-full" />
            </div>

            <p className="text-xs text-slate-400 leading-relaxed max-w-sm">
              Ứng dụng nghiên cứu dự báo nguy cơ học tập trên dữ liệu OULAD và đưa ra gợi ý có căn cứ để giảng viên xem xét. Không tự giao bài tập và chưa kiểm chứng hiệu quả trên dữ liệu HUIT.
            </p>

            {/* Corporate Compliance Badges */}
            <div className="flex flex-wrap items-center gap-2 pt-1 text-[10px] text-slate-400">
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-slate-900 border border-slate-800">
                <ShieldCheck className="w-3 h-3 text-cyan-400" />
                <span>Dữ liệu OULAD lịch sử</span>
              </span>
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-slate-900 border border-slate-800">
                <Lock className="w-3 h-3 text-purple-400" />
                <span>Giảng viên quyết định</span>
              </span>
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-slate-900 border border-slate-800">
                <Server className="w-3 h-3 text-brand-400" />
                <span>Chưa tích hợp LMS</span>
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
                  className="hover:text-brand-400 transition-colors flex items-center gap-1.5"
                >
                  <ArrowRight className="w-3 h-3 text-brand-500" />
                  <span>Trang phân tích học tập</span>
                </button>
              </li>
              <li>
                <button
                  type="button"
                  onClick={() => handleNav('dashboard')}
                  className="hover:text-brand-400 transition-colors flex items-center gap-1.5"
                >
                  <ArrowRight className="w-3 h-3 text-brand-500" />
                  <span>Đồng Hồ Đo Rủi Ro Radial Gauge</span>
                </button>
              </li>
              <li>
                <button
                  type="button"
                  onClick={() => handleNav('dashboard')}
                  className="hover:text-brand-400 transition-colors flex items-center gap-1.5"
                >
                  <ArrowRight className="w-3 h-3 text-brand-500" />
                  <span>Biểu Đồ Radar Đối Sánh Năng Lực</span>
                </button>
              </li>
              <li>
                <button
                  type="button"
                  onClick={() => handleNav('dashboard')}
                  className="hover:text-brand-400 transition-colors flex items-center gap-1.5"
                >
                  <ArrowRight className="w-3 h-3 text-brand-500" />
                  <span>Gợi ý để giảng viên xem xét</span>
                </button>
              </li>
              <li>
                <button
                  type="button"
                  onClick={() => handleNav('dashboard')}
                  className="hover:text-brand-400 transition-colors flex items-center gap-1.5"
                >
                  <ArrowRight className="w-3 h-3 text-brand-500" />
                  <span>Xuất Báo Cáo CSV (UTF-8 BOM)</span>
                </button>
              </li>
              <li>
                <button
                  type="button"
                  onClick={() => handleNav('about')}
                  className="hover:text-brand-400 transition-colors flex items-center gap-1.5"
                >
                  <ArrowRight className="w-3 h-3 text-brand-500" />
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
                  <span>API nội bộ của ứng dụng</span>
                </button>
              </li>
              <li>
                <a
                  href={`${apiBase}/docs`}
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
                  <span>Tích hợp LMS cần kiểm chứng</span>
                </button>
              </li>
              <li>
                <button
                  type="button"
                  onClick={() => handleNav('contact')}
                  className="hover:text-cyan-400 transition-colors flex items-center gap-1.5"
                >
                  <CheckCircle2 className="w-3 h-3 text-cyan-500" />
                  <span>Chạy thử bằng Docker</span>
                </button>
              </li>
              <li>
                <button
                  type="button"
                  onClick={() => handleNav('profile')}
                  className="hover:text-cyan-400 transition-colors flex items-center gap-1.5"
                >
                  <CheckCircle2 className="w-3 h-3 text-cyan-500" />
                  <span>Phân quyền theo vai trò</span>
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
                <Phone className="w-3.5 h-3.5 text-brand-400 shrink-0 mt-0.5" />
                <div>
                  <div className="text-[11px] text-slate-500">Hotline:</div>
                  <strong className="text-slate-200 font-mono">Chưa thiết lập</strong>
                </div>
              </div>

              <div className="flex items-start gap-2">
                <Mail className="w-3.5 h-3.5 text-cyan-400 shrink-0 mt-0.5" />
                <div>
                  <div className="text-[11px] text-slate-500">Email liên hệ:</div>
                  <code className="text-slate-300 font-mono text-[11px]">Chưa thiết lập</code>
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
            <span>&copy; {new Date().getFullYear()} EduRisk AI — dự án nghiên cứu.</span>
            <span className="hidden sm:inline text-slate-700">&bull;</span>
            <button
              type="button"
              onClick={() => handleNav('about')}
              className="hover:text-slate-200 transition-colors"
            >
              Giới thiệu nghiên cứu
            </button>
            <span className="hidden sm:inline text-slate-700">&bull;</span>
            <button
              type="button"
              onClick={() => handleNav('about')}
              className="hover:text-slate-200 transition-colors"
            >
              Giới hạn dữ liệu
            </button>
            <span className="hidden sm:inline text-slate-700">&bull;</span>
            <button
              type="button"
              onClick={() => handleNav('contact')}
              className="hover:text-slate-200 transition-colors"
            >
              Thông tin liên hệ
            </button>
          </div>

          <div className="flex items-center gap-3 text-[11px] text-slate-400">
            <span className="flex items-center gap-1 text-slate-400">
              <Globe className="w-3.5 h-3.5 text-brand-400" />
              <span>Tiếng Việt (VN)</span>
            </span>
            <span className="text-slate-700">&bull;</span>
            <span className="font-mono text-slate-400">Bản nghiên cứu</span>
          </div>
        </div>
      </div>
    </footer>
  );
};
