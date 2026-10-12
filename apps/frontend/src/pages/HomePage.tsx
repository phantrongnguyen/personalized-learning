import React from 'react';
import { useApp } from '../state/AppContext';
import {
  Sparkles,
  ArrowRight,
  TrendingUp,
  BrainCircuit,
  Filter,
  Clock,
  Layers,
  ChevronRight,
  LayoutDashboard,
  User,
  PhoneCall,
  ShieldCheck,
  Cpu,
  Database,
  Compass,
  FileSpreadsheet,
  CheckCircle2,
  ExternalLink,
} from 'lucide-react';

export const HomePage: React.FC = () => {
  const { setCurrentView, user } = useApp();

  return (
    <div className="space-y-16 py-6">
      {/* 1. Hero Section */}
      <section className="text-center max-w-4xl mx-auto px-4 pt-6 pb-2">
        {user && (
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-slate-900/90 border border-brand-500/30 text-xs text-slate-300 mb-5 shadow-lg shadow-brand-500/5">
            <span className="w-2 h-2 rounded-full bg-brand-400 animate-pulse" />
            <span>
              Xin chào, <strong className="text-white">{user.name}</strong>
            </span>
            <span className="text-slate-600">&bull;</span>
            <span className="text-brand-400 font-semibold">{user.role}</span>
            {user.department && (
              <>
                <span className="text-slate-600 hidden sm:inline">&bull;</span>
                <span className="text-slate-400 hidden sm:inline">{user.department}</span>
              </>
            )}
          </div>
        )}

        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-brand-500/10 border border-brand-500/20 text-brand-400 text-xs font-semibold mb-6">
          <Sparkles className="w-3.5 h-3.5" />
          <span>EduRisk AI Enterprise Platform &bull; Quản trị Rủi ro Đào tạo &amp; Cá nhân hóa Học tập</span>
        </div>

        <h1 className="text-3xl sm:text-5xl font-extrabold text-white tracking-tight leading-tight sm:leading-tight mb-6">
          Dự Đoán Nguy Cơ &amp; Can Thiệp Học Tập <br className="hidden sm:inline" />
          <span className="bg-gradient-to-r from-brand-400 via-brand-300 to-cyan-400 bg-clip-text text-transparent">
            Chuẩn Xác Với Trí Tuệ Nhân Tạo
          </span>
        </h1>

        <p className="text-base sm:text-lg text-slate-300 max-w-2xl mx-auto leading-relaxed mb-8">
          Ứng dụng mô hình phân lớp <strong className="text-white">LightGBM</strong> tối ưu siêu tham số
          bằng thuật toán lai <strong className="text-brand-400">HCO-VNLS</strong> (Human Conception Optimization &amp; Variable Neighborhood Local Search), hỗ trợ ban cố vấn học tập và cơ sở giáo dục phát hiện sớm nguy cơ trượt/bỏ học để can thiệp kịp thời.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <button
            onClick={() => setCurrentView('dashboard')}
            className="w-full sm:w-auto flex items-center justify-center gap-2 px-6 py-3.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-bold text-sm shadow-xl shadow-brand-600/30 transition-all hover:scale-[1.02]"
          >
            <span>Truy cập Dashboard Phân tích</span>
            <ArrowRight className="w-4 h-4" />
          </button>

          <button
            onClick={() => setCurrentView('about')}
            className="w-full sm:w-auto flex items-center justify-center gap-2 px-6 py-3.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-200 border border-slate-750 font-semibold text-sm transition-all"
          >
            <span>Tìm hiểu kiến trúc giải pháp</span>
            <ChevronRight className="w-4 h-4 text-slate-400" />
          </button>
        </div>
      </section>

      {/* 2. KPI Stats Grid */}
      <section className="max-w-6xl mx-auto px-4">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-lg relative overflow-hidden group hover:border-brand-500/40 transition-colors">
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-xs font-semibold">Độ chính xác (Accuracy)</span>
              <TrendingUp className="w-4 h-4 text-brand-400" />
            </div>
            <div className="text-3xl font-extrabold text-white font-mono">93.04%</div>
            <div className="text-[11px] text-brand-400 mt-1">Đánh giá kiểm thử độc lập (Test 20%)</div>
          </div>

          <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-lg relative overflow-hidden group hover:border-brand-500/40 transition-colors">
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-xs font-semibold">ROC-AUC Score</span>
              <BrainCircuit className="w-4 h-4 text-cyan-400" />
            </div>
            <div className="text-3xl font-extrabold text-white font-mono">0.9785</div>
            <div className="text-[11px] text-cyan-400 mt-1">Khả năng phân tách nhãn nhị phân tối ưu</div>
          </div>

          <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-lg relative overflow-hidden group hover:border-brand-500/40 transition-colors">
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-xs font-semibold">Giảm số chiều dữ liệu</span>
              <Filter className="w-4 h-4 text-amber-400" />
            </div>
            <div className="text-3xl font-extrabold text-white font-mono">86.7%</div>
            <div className="text-[11px] text-amber-400 mt-1">Lọc từ 30 biến xuống 4 đặc trưng cốt lõi</div>
          </div>

          <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-lg relative overflow-hidden group hover:border-brand-500/40 transition-colors">
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-xs font-semibold">Thời điểm quan sát</span>
              <Clock className="w-4 h-4 text-purple-400" />
            </div>
            <div className="text-3xl font-extrabold text-white font-mono">Cutoff 75%</div>
            <div className="text-[11px] text-purple-400 mt-1">Thời điểm vàng để can thiệp trước thi</div>
          </div>
        </div>
      </section>

      {/* 3. Three Core Highlights */}
      <section className="max-w-6xl mx-auto px-4">
        <div className="text-center mb-10">
          <h2 className="text-2xl font-bold text-white mb-2">Quy trình Khép kín từ Dữ liệu tới Hành động</h2>
          <p className="text-xs sm:text-sm text-slate-400">
            Chuyển dịch từ phân tích dự báo (Predictive) sang kê đơn giải pháp (Prescriptive)
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition-all">
            <div className="w-10 h-10 rounded-xl bg-brand-500/10 border border-brand-500/20 text-brand-400 flex items-center justify-center mb-4">
              <Filter className="w-5 h-5" />
            </div>
            <h3 className="text-base font-bold text-white mb-2">1. Lọc Đặc Trưng Tối Ưu (HCO-VNLS)</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Thuật toán lai Human Conception Optimization kết hợp Variable Neighborhood Local Search
              tự động loại bỏ các thuộc tính nhiễu, đa cộng tuyến trong nhật ký LMS.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition-all">
            <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 flex items-center justify-center mb-4">
              <BrainCircuit className="w-5 h-5" />
            </div>
            <h3 className="text-base font-bold text-white mb-2">2. Suy Luận Thời Gian Thực (FastAPI)</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Mô hình LightGBM được đóng gói và phục vụ qua RESTful API tốc độ cao, tính toán xác suất
              rủi ro trượt môn chỉ trong vài mili-giây.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition-all">
            <div className="w-10 h-10 rounded-xl bg-purple-500/10 border border-purple-500/20 text-purple-400 flex items-center justify-center mb-4">
              <Layers className="w-5 h-5" />
            </div>
            <h3 className="text-base font-bold text-white mb-2">3. Đề Xuất Chiến Lược &amp; Radar Chart</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Hệ luật sư phạm đối sánh hành vi sinh viên với nhóm khá giỏi (Pass/Distinction), kê đơn
              hành động cụ thể kèm chỉ số mục tiêu đo lường được.
            </p>
          </div>
        </div>
      </section>

      {/* 4. Thông Tin Nền Tảng & Đặc Tả Kỹ Thuật (Website & System Information) */}
      <section className="max-w-6xl mx-auto px-4 pt-4 border-t border-slate-800/80">
        <div className="flex items-center gap-3 mb-8">
          <div className="p-2.5 rounded-xl bg-brand-500/10 border border-brand-500/20 text-brand-400">
            <Cpu className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-white">Thông Tin Nền Tảng &amp; Đặc Tả Hệ Thống</h2>
            <p className="text-xs text-slate-400">
              Kiến trúc kỹ thuật, chuẩn dữ liệu giáo dục và các cam kết vận hành doanh nghiệp
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Card 1: Về Nền tảng */}
          <div className="p-6 rounded-2xl bg-slate-900/70 border border-slate-800 space-y-3">
            <div className="flex items-center gap-2 text-brand-400 font-bold text-sm">
              <Sparkles className="w-4 h-4" />
              <span>Sứ Mệnh &amp; Bản Quyền</span>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              <strong>EduRisk AI Platform (Enterprise Edition)</strong> là giải pháp AI phân tích hành vi học tập chuyên sâu, đồng hành cùng các trường đại học và tổ chức giáo dục trong việc nhận diện sớm học viên gặp khó khăn và giảm thiểu tỷ lệ bỏ học/trượt môn.
            </p>
            <div className="pt-2 border-t border-slate-800 text-[11px] text-slate-400 space-y-1">
              <div>&bull; Bản quyền: &copy; {new Date().getFullYear()} EduRisk AI Systems</div>
              <div>&bull; Phiên bản: v2.4 Enterprise Stable</div>
              <div>&bull; Môi trường vận hành: Private Cloud / On-Premise</div>
            </div>
          </div>

          {/* Card 2: Đặc tả công nghệ */}
          <div className="p-6 rounded-2xl bg-slate-900/70 border border-slate-800 space-y-3">
            <div className="flex items-center gap-2 text-cyan-400 font-bold text-sm">
              <Database className="w-4 h-4" />
              <span>Dữ Liệu &amp; Thuật Toán Lõi</span>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              Mô hình học máy LightGBM được huấn luyện trên <strong>32.593 bản ghi</strong> thuộc tập dữ liệu <em>Open University Learning Analytics Dataset (OULAD)</em>, sử dụng thuật toán bọc lai <strong>HCO-VNLS</strong> để tối ưu chọn lọc đặc trưng với hàm thích nghi đa mục tiêu.
            </p>
            <div className="pt-2 border-t border-slate-800 text-[11px] text-slate-400 space-y-1">
              <div>&bull; Backend: FastAPI &bull; Python 3.12 &bull; Joblib Engine</div>
              <div>&bull; Frontend: React 18 &bull; TypeScript &bull; Vite &bull; Tailwind</div>
              <div>&bull; Tốc độ suy luận API: &lt; 20ms / truy vấn</div>
            </div>
          </div>

          {/* Card 3: Tiêu chuẩn tuân thủ */}
          <div className="p-6 rounded-2xl bg-slate-900/70 border border-slate-800 space-y-3">
            <div className="flex items-center gap-2 text-purple-400 font-bold text-sm">
              <ShieldCheck className="w-4 h-4" />
              <span>Bảo Mật &amp; Tích Hợp LMS</span>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              Hệ thống đáp ứng các chuẩn kết nối quốc tế trong ngành EdTech, cho phép đồng bộ hóa dữ liệu 2 chiều với hệ thống quản lý học tập (LMS) mà vẫn đảm bảo tính bảo mật và quyền riêng tư tuyệt đối cho dữ liệu học viên.
            </p>
            <div className="pt-2 border-t border-slate-800 text-[11px] text-slate-400 space-y-1">
              <div>&bull; Tương thích: IMS LTI 1.3 Advantage &bull; REST API v1</div>
              <div>&bull; Mã hóa: Chuẩn AES-256 (At-rest) &bull; TLS 1.3 (In-transit)</div>
              <div>&bull; Tiêu chuẩn tuân thủ: FERPA &bull; GDPR &bull; ISO 27001</div>
            </div>
          </div>
        </div>
      </section>

      {/* 5. Trung Tâm Điều Hướng Phân Hệ (Interactive Navigation Hub) */}
      <section className="max-w-6xl mx-auto px-4 pt-2">
        <div className="flex items-center gap-3 mb-8">
          <div className="p-2.5 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-400">
            <Compass className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-white">Trung Tâm Điều Hướng Phân Hệ</h2>
            <p className="text-xs text-slate-400">
              Truy cập nhanh các tính năng và module làm việc chính trong nền tảng EduRisk AI
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          {/* Nav Item 1: Dashboard */}
          <div
            onClick={() => setCurrentView('dashboard')}
            className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 hover:border-brand-500/60 shadow-lg cursor-pointer group transition-all duration-200 hover:-translate-y-1"
          >
            <div className="flex items-center justify-between mb-3">
              <div className="p-2.5 rounded-xl bg-brand-500/15 text-brand-400 group-hover:scale-110 transition-transform">
                <LayoutDashboard className="w-5 h-5" />
              </div>
              <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-brand-500/20 text-brand-300">
                LÀM VIỆC CHÍNH
              </span>
            </div>

            <h3 className="text-base font-bold text-white group-hover:text-brand-300 transition-colors mb-1.5 flex items-center justify-between">
              <span>Dashboard Phân Tích</span>
              <ExternalLink className="w-3.5 h-3.5 text-slate-500 group-hover:text-brand-400" />
            </h3>
            <p className="text-xs text-slate-400 leading-relaxed mb-4">
              Nhập 17 đặc trưng học tập OULAD, nạp mẫu sinh viên, xem đồng hồ đo SVG Gauge và biểu đồ Radar đối sánh.
            </p>

            <div className="flex items-center gap-1 text-xs font-semibold text-brand-400">
              <span>Mở Dashboard</span>
              <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
            </div>
          </div>

          {/* Nav Item 2: Profile */}
          <div
            onClick={() => setCurrentView('profile')}
            className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 hover:border-cyan-500/60 shadow-lg cursor-pointer group transition-all duration-200 hover:-translate-y-1"
          >
            <div className="flex items-center justify-between mb-3">
              <div className="p-2.5 rounded-xl bg-cyan-500/15 text-cyan-400 group-hover:scale-110 transition-transform">
                <User className="w-5 h-5" />
              </div>
              <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300">
                QUẢN TRỊ
              </span>
            </div>

            <h3 className="text-base font-bold text-white group-hover:text-cyan-300 transition-colors mb-1.5 flex items-center justify-between">
              <span>Hồ Sơ Chuyên Gia</span>
              <ExternalLink className="w-3.5 h-3.5 text-slate-500 group-hover:text-cyan-400" />
            </h3>
            <p className="text-xs text-slate-400 leading-relaxed mb-4">
              Quản lý tài khoản cố vấn, theo dõi thống kê số ca rủi ro phát hiện trong phiên và lấy LMS API Integration Key.
            </p>

            <div className="flex items-center gap-1 text-xs font-semibold text-cyan-400">
              <span>Xem Hồ sơ &amp; Cài đặt</span>
              <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
            </div>
          </div>

          {/* Nav Item 3: Architecture & Model */}
          <div
            onClick={() => setCurrentView('about')}
            className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 hover:border-purple-500/60 shadow-lg cursor-pointer group transition-all duration-200 hover:-translate-y-1"
          >
            <div className="flex items-center justify-between mb-3">
              <div className="p-2.5 rounded-xl bg-purple-500/15 text-purple-400 group-hover:scale-110 transition-transform">
                <Layers className="w-5 h-5" />
              </div>
              <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-purple-500/20 text-purple-300">
                KHOA HỌC
              </span>
            </div>

            <h3 className="text-base font-bold text-white group-hover:text-purple-300 transition-colors mb-1.5 flex items-center justify-between">
              <span>Kiến Trúc Thuật Toán</span>
              <ExternalLink className="w-3.5 h-3.5 text-slate-500 group-hover:text-purple-400" />
            </h3>
            <p className="text-xs text-slate-400 leading-relaxed mb-4">
              Chi tiết cơ chế thuật toán lai HCO-VNLS, công thức hàm thích ứng Fitness đa mục tiêu và bảng đối chứng thực nghiệm.
            </p>

            <div className="flex items-center gap-1 text-xs font-semibold text-purple-400">
              <span>Tìm hiểu thuật toán</span>
              <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
            </div>
          </div>

          {/* Nav Item 4: Contact & Solutions */}
          <div
            onClick={() => setCurrentView('contact')}
            className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 hover:border-amber-500/60 shadow-lg cursor-pointer group transition-all duration-200 hover:-translate-y-1"
          >
            <div className="flex items-center justify-between mb-3">
              <div className="p-2.5 rounded-xl bg-amber-500/15 text-amber-400 group-hover:scale-110 transition-transform">
                <PhoneCall className="w-5 h-5" />
              </div>
              <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-amber-500/20 text-amber-300">
                TƯ VẤN
              </span>
            </div>

            <h3 className="text-base font-bold text-white group-hover:text-amber-300 transition-colors mb-1.5 flex items-center justify-between">
              <span>Hợp Tác Doanh Nghiệp</span>
              <ExternalLink className="w-3.5 h-3.5 text-slate-500 group-hover:text-amber-400" />
            </h3>
            <p className="text-xs text-slate-400 leading-relaxed mb-4">
              Kênh tư vấn triển khai giải pháp Private Cloud, hỗ trợ kỹ thuật API và bộ giải đáp thắc mắc chuyên sâu (FAQs).
            </p>

            <div className="flex items-center gap-1 text-xs font-semibold text-amber-400">
              <span>Liên hệ hợp tác</span>
              <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
            </div>
          </div>
        </div>
      </section>

      {/* 6. Hướng Dẫn Vận Hành 4 Bước (Operational Workflow Shortcuts) */}
      <section className="max-w-6xl mx-auto px-4 pb-4">
        <div className="p-6 sm:p-8 rounded-2xl bg-slate-950/80 border border-slate-800/80 space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-800">
            <div>
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <FileSpreadsheet className="w-5 h-5 text-brand-400" />
                <span>Quy Trình 4 Bước Phân Tích &amp; Can Thiệp Nguy Cơ</span>
              </h3>
              <p className="text-xs text-slate-400 mt-1">
                Hướng dẫn nhanh dành cho cố vấn học tập và ban quản trị đào tạo
              </p>
            </div>

            <button
              onClick={() => setCurrentView('dashboard')}
              className="px-4 py-2 rounded-xl bg-brand-600/20 hover:bg-brand-600/30 text-brand-300 border border-brand-500/30 text-xs font-bold transition-colors w-fit"
            >
              Bắt đầu phân tích ngay &rarr;
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
            <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80 space-y-1.5">
              <div className="flex items-center gap-2 font-bold text-brand-400">
                <CheckCircle2 className="w-4 h-4" />
                <span>Bước 1: Nạp Dữ Liệu</span>
              </div>
              <p className="text-slate-300 leading-relaxed">
                Nhập 17 trường chỉ số học tập hoặc nhấn nhanh mẫu thử nghiệm (Sinh viên yếu / Sinh viên tốt).
              </p>
            </div>

            <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80 space-y-1.5">
              <div className="flex items-center gap-2 font-bold text-cyan-400">
                <CheckCircle2 className="w-4 h-4" />
                <span>Bước 2: Dự Báo Rủi Ro</span>
              </div>
              <p className="text-slate-300 leading-relaxed">
                Nhấn "Phân tích nguy cơ" để mô hình LightGBM tính toán xác suất phần trăm và nhãn cảnh báo.
              </p>
            </div>

            <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80 space-y-1.5">
              <div className="flex items-center gap-2 font-bold text-purple-400">
                <CheckCircle2 className="w-4 h-4" />
                <span>Bước 3: Đối Sánh Năng Lực</span>
              </div>
              <p className="text-slate-300 leading-relaxed">
                Quan sát biểu đồ Radar Chart để phát hiện ngay các chỉ số bị tụt hậu so với ngưỡng chuẩn giỏi.
              </p>
            </div>

            <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80 space-y-1.5">
              <div className="flex items-center gap-2 font-bold text-amber-400">
                <CheckCircle2 className="w-4 h-4" />
                <span>Bước 4: Kê Đơn &amp; Báo Cáo</span>
              </div>
              <p className="text-slate-300 leading-relaxed">
                Sao chép khuyến nghị can thiệp hành vi 1-click và xuất lịch sử ra file CSV chuẩn tiếng Việt.
              </p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};
