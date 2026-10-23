import { ZoomableChart } from '../components/evaluation/ZoomableChart';
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
  const { setCurrentView } = useApp();

  return (
    <div className="space-y-16 py-6">
      {/* 1. Hero Section */}
      <section className="text-center max-w-4xl mx-auto px-4 pt-6 pb-2">
        <h1 className="text-3xl sm:text-5xl font-extrabold text-white tracking-tight leading-tight sm:leading-tight mb-6">
          Dự Đoán Nguy Cơ &amp; Can Thiệp Học Tập <br className="hidden sm:inline" />
          <span className="bg-gradient-to-r from-brand-400 via-brand-300 to-cyan-400 bg-clip-text text-transparent">
            Hỗ trợ quyết định từ dữ liệu học tập
          </span>
        </h1>

        <p className="text-base sm:text-lg text-slate-300 max-w-2xl mx-auto leading-relaxed mb-8">
          Kết hợp <strong className="text-white">LightGBM</strong> với thuật toán chọn đặc trưng
          <strong className="text-brand-400"> HCO–VNLS</strong> để nhận diện nguy cơ trượt môn hoặc bỏ học.
          Kết quả nghiên cứu trên OULAD hỗ trợ cố vấn xem xét và lập kế hoạch học tập phù hợp.
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
      <section className="max-w-6xl mx-auto px-4" aria-labelledby="validation-heading">
        <h2 id="validation-heading" className="text-xl font-bold text-white mb-2">Kết quả tham chiếu trên OULAD</h2>
        <p className="text-sm text-slate-400 mb-5 leading-relaxed">
          HCO–VNLS + LightGBM · cutoff 75% · seed 41. Các chỉ số được đo trên validation của model fit train,
          không phải điểm kiểm thử độc lập của model đã fit lại trên train + validation.
        </p>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-lg relative overflow-hidden group hover:border-brand-500/40 transition-colors">
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-xs font-semibold">Độ chính xác (Accuracy)</span>
              <TrendingUp className="w-4 h-4 text-brand-400" />
            </div>
            <div className="text-3xl font-extrabold text-white font-mono">87,41%</div>
            <div className="text-[11px] text-brand-400 mt-1">Validation lịch sử · 3.415 lượt đăng ký</div>
          </div>

          <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-lg relative overflow-hidden group hover:border-brand-500/40 transition-colors">
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-xs font-semibold">Average Precision (AP)</span>
              <BrainCircuit className="w-4 h-4 text-cyan-400" />
            </div>
            <div className="text-3xl font-extrabold text-white font-mono">0,8968</div>
            <div className="text-[11px] text-cyan-400 mt-1">AP lớp nguy cơ · ROC-AUC: 0,9174</div>
          </div>

          <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-lg relative overflow-hidden group hover:border-brand-500/40 transition-colors">
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-xs font-semibold">Giảm số đặc trưng đầu vào</span>
              <Filter className="w-4 h-4 text-amber-400" />
            </div>
            <div className="text-3xl font-extrabold text-white font-mono">55,26%</div>
            <div className="text-[11px] text-amber-400 mt-1">Từ 38 xuống 17 cột trước mã hóa</div>
          </div>

          <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-lg relative overflow-hidden group hover:border-brand-500/40 transition-colors">
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-xs font-semibold">Phát hiện trường hợp nguy cơ (Recall)</span>
              <Clock className="w-4 h-4 text-purple-400" />
            </div>
            <div className="text-3xl font-extrabold text-white font-mono">68,98%</div>
            <div className="text-[11px] text-purple-400 mt-1">Cutoff 75% · Ngưỡng phân loại 0,5</div>
          </div>
        </div>
      </section>

      <section className="max-w-6xl mx-auto px-4" aria-labelledby="comparison-heading">
        <div className="mb-5">
          <h2 id="comparison-heading" className="text-2xl font-bold text-white mb-2">Ít đặc trưng hơn, chất lượng gần giữ nguyên</h2>
          <p className="text-sm text-slate-400 leading-relaxed max-w-3xl">
            Tại cutoff 75%, hybrid LightGBM giảm 21 cột nhưng AP thấp hơn đối chứng đủ cột 0,000231.
            Lợi ích chính là độ gọn của đầu vào; chưa có bằng chứng cải thiện khả năng phát hiện nguy cơ.
          </p>
        </div>
        <ZoomableChart title="So sánh kết quả các bộ học tại cutoff 75%" variant="table">
        <div className="overflow-x-auto rounded-2xl border border-slate-800 bg-slate-900/60">
          <table className="w-full min-w-[640px] text-sm text-left">
            <caption className="text-left px-5 py-4 text-xs text-slate-400">
              Validation lịch sử · ngưỡng 0,5 · cùng cutoff 75%. Mỗi bộ học dùng mask được chọn với evaluator tương ứng.
            </caption>
            <thead className="bg-slate-800/70 text-slate-300">
              <tr>
                {['Bộ học / Đặc trưng', 'Số cột', 'Accuracy', 'Recall nguy cơ', 'AP'].map(label => (
                  <th key={label} scope="col" className="px-5 py-3 font-semibold whitespace-nowrap">{label}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {[
                { name: 'LightGBM · Đủ cột', columns: 38, accuracy: '87,35%', recall: '68,98%', ap: '0,896987' },
                { name: 'LightGBM · HCO–VNLS', columns: 17, accuracy: '87,41%', recall: '68,98%', ap: '0,896757', highlighted: true },
                { name: 'XGBoost · Đủ cột', columns: 38, accuracy: '87,29%', recall: '68,29%', ap: '0,895345' },
                { name: 'XGBoost · HCO–VNLS', columns: 17, accuracy: '87,32%', recall: '67,95%', ap: '0,894079' },
                { name: 'CatBoost · Đủ cột', columns: 38, accuracy: '87,14%', recall: '68,47%', ap: '0,897867' },
                { name: 'CatBoost · HCO–VNLS', columns: 16, accuracy: '85,89%', recall: '64,70%', ap: '0,883905' },
              ].map(row => (
                <tr key={row.name} className={row.highlighted ? 'bg-brand-500/10 text-brand-300' : 'text-slate-300'}>
                  <th scope="row" className="px-5 py-3 font-medium">{row.name}</th>
                  <td className="px-5 py-3 font-mono">{row.columns}</td>
                  <td className="px-5 py-3 font-mono">{row.accuracy}</td>
                  <td className="px-5 py-3 font-mono">{row.recall}</td>
                  <td className="px-5 py-3 font-mono">{row.ap}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        </ZoomableChart>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-5">
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
            <h3 className="font-semibold text-white mb-2">Hiểu đúng cảnh báo</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Hybrid LightGBM phát hiện 805/1.167 lượt đăng ký nguy cơ, bỏ sót 362 (31,02%) và cảnh báo nhầm 68 trường hợp.
              Đơn vị đánh giá là lượt đăng ký học phần, không phải sinh viên duy nhất.
            </p>
          </div>
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
            <h3 className="font-semibold text-white mb-2">Kết quả phụ thuộc thời điểm</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Ở cutoff 50%, AP của hybrid LightGBM là 0,845151, thấp hơn đủ cột 0,851085.
              Mốc 75% có kết quả tốt hơn nhưng ít thời gian hỗ trợ hơn và quần thể đánh giá cũng thay đổi.
            </p>
          </div>
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
            <h3 className="font-semibold text-white mb-2">Cần kiểm chứng thêm</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Qua 5 seed, AP validation hybrid 75% trung bình 0,893906; độ trùng lặp tập cột Jaccard chỉ 0,2568.
              Chưa có tập học kỳ mới độc lập để xác nhận kết quả hoặc hiệu quả can thiệp.
            </p>
          </div>
        </div>
        <p className="text-xs text-slate-400 mt-4 leading-relaxed">
          AP đo chất lượng xếp hạng lớp nguy cơ, khác ROC-AUC. Nguồn: báo cáo thí nghiệm HCO–VNLS,
          đối chiếu ngày 19/10/2026. Đây là kết quả nghiên cứu tham chiếu, không phải phép đo model đang hoạt động.
        </p>
      </section>

      {/* 3. Three Core Highlights */}
      <section className="max-w-6xl mx-auto px-4">
        <div className="text-center mb-10">
          <h2 className="text-2xl font-bold text-white mb-2">Quy trình Khép kín từ Dữ liệu tới Hành động</h2>
          <p className="text-xs sm:text-sm text-slate-400">
            Theo dõi chỉ số, xem dự báo và xây dựng kế hoạch hỗ trợ cùng cố vấn
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition-all">
            <div className="w-10 h-10 rounded-xl bg-brand-500/10 border border-brand-500/20 text-brand-400 flex items-center justify-center mb-4">
              <Filter className="w-5 h-5" />
            </div>
            <h3 className="text-base font-bold text-white mb-2">1. Chọn đặc trưng với HCO–VNLS</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Tìm tập con đặc trưng bằng cách cân bằng AP trên train-CV và số cột được giữ lại.
              Cấu hình 75% chọn 17/38 cột; chưa chứng minh đây là tập đặc trưng tối ưu.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition-all">
            <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 flex items-center justify-center mb-4">
              <BrainCircuit className="w-5 h-5" />
            </div>
            <h3 className="text-base font-bold text-white mb-2">2. Dự báo với LightGBM</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Pipeline LightGBM nhận 17 đặc trưng đúng mốc quan sát và trả xác suất nguy cơ qua API.
              Model cutoff 75% cần dữ liệu tương ứng, không tự áp dụng cho mốc 50%.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition-all">
            <div className="w-10 h-10 rounded-xl bg-purple-500/10 border border-purple-500/20 text-purple-400 flex items-center justify-center mb-4">
              <Layers className="w-5 h-5" />
            </div>
            <h3 className="text-base font-bold text-white mb-2">3. Xem xét và lập kế hoạch hỗ trợ</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Biểu đồ và gợi ý giúp sinh viên, giảng viên, cố vấn trao đổi về tiến độ học tập.
              Hiệu quả giảm trượt môn hoặc bỏ học của các can thiệp chưa được đánh giá thực địa.
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
            <h2 className="text-2xl font-bold text-white">Dữ liệu và phạm vi sử dụng</h2>
            <p className="text-xs text-slate-400">
              Thông tin nghiên cứu và chức năng hỗ trợ trong dự án
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Card 1: Về Nền tảng */}
          <div className="p-6 rounded-2xl bg-slate-900/70 border border-slate-800 space-y-3">
            <div className="flex items-center gap-2 text-brand-400 font-bold text-sm">
              <Sparkles className="w-4 h-4" />
              <span>Mục tiêu của dự án</span>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              <strong>EduRisk AI</strong> là dự án hỗ trợ nhận diện nguy cơ học tập, theo dõi tiến độ
              và lập kế hoạch can thiệp. Dự báo là thông tin tham khảo để trao đổi, không thay thế đánh giá của người phụ trách.
            </p>
            <div className="pt-2 border-t border-slate-800 text-[11px] text-slate-400 space-y-1">
              <div>&bull; Bài toán: nguy cơ trượt môn hoặc bỏ học</div>
              <div>&bull; Nhãn nguy cơ: Fail / Withdrawn</div>
              <div>&bull; Nhãn không nguy cơ: Pass / Distinction</div>
            </div>
          </div>

          {/* Card 2: Đặc tả công nghệ */}
          <div className="p-6 rounded-2xl bg-slate-900/70 border border-slate-800 space-y-3">
            <div className="flex items-center gap-2 text-cyan-400 font-bold text-sm">
              <Database className="w-4 h-4" />
              <span>Dữ Liệu &amp; Thuật Toán Lõi</span>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              Thí nghiệm cutoff 75% sử dụng <strong>23.159 lượt đăng ký học phần</strong> từ
              <em> Open University Learning Analytics Dataset (OULAD)</em>: 16.297 train,
              3.415 validation và 3.447 test, chia theo sinh viên.
            </p>
            <div className="pt-2 border-t border-slate-800 text-[11px] text-slate-400 space-y-1">
              <div>&bull; Chọn mask: GroupKFold 3 fold trong train</div>
              <div>&bull; Bộ học: LightGBM 80 cây · seed 41</div>
              <div>&bull; Đóng gói: fit lại 19.712 dòng train + validation</div>
            </div>
          </div>

          {/* Card 3: Tiêu chuẩn tuân thủ */}
          <div className="p-6 rounded-2xl bg-slate-900/70 border border-slate-800 space-y-3">
            <div className="flex items-center gap-2 text-purple-400 font-bold text-sm">
              <ShieldCheck className="w-4 h-4" />
              <span>Điều kiện áp dụng</span>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              Đặc trưng phải được tính từ thông tin đã có tại cutoff. Kết quả OULAD chưa xác nhận
              khả năng khái quát sang sinh viên HUIT hoặc một học kỳ mới.
            </p>
            <div className="pt-2 border-t border-slate-800 text-[11px] text-slate-400 space-y-1">
              <div>&bull; Ngưỡng 0,5 chưa tối ưu cho vận hành</div>
              <div>&bull; Chưa đánh giá đầy đủ độ hiệu chỉnh xác suất</div>
              <div>&bull; Cần dữ liệu mới để kiểm chứng độc lập</div>
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
              Nhập 17 đặc trưng học tập theo cutoff 75%, xem dự báo nguy cơ và biểu đồ đối sánh.
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
              <span>Hồ sơ cá nhân</span>
              <ExternalLink className="w-3.5 h-3.5 text-slate-500 group-hover:text-cyan-400" />
            </h3>
            <p className="text-xs text-slate-400 leading-relaxed mb-4">
              Xem và cập nhật thông tin tài khoản, ảnh đại diện và thông tin liên hệ.
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
              <span>Liên hệ và hỗ trợ</span>
              <ExternalLink className="w-3.5 h-3.5 text-slate-500 group-hover:text-amber-400" />
            </h3>
            <p className="text-xs text-slate-400 leading-relaxed mb-4">
              Tìm thông tin liên hệ và gửi trao đổi về cách sử dụng nền tảng.
            </p>

            <div className="flex items-center gap-1 text-xs font-semibold text-amber-400">
              <span>Xem thông tin liên hệ</span>
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
                Chuẩn bị 17 đặc trưng từ dữ liệu đã có tại mốc 75% thời lượng học phần.
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
                <span>Bước 3: Xem xét chỉ số</span>
              </div>
              <p className="text-slate-300 leading-relaxed">
                Xem biểu đồ đối sánh và trao đổi với cố vấn về các chỉ số cần theo dõi.
              </p>
            </div>

            <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80 space-y-1.5">
              <div className="flex items-center gap-2 font-bold text-amber-400">
                <CheckCircle2 className="w-4 h-4" />
                <span>Bước 4: Lập kế hoạch hỗ trợ</span>
              </div>
              <p className="text-slate-300 leading-relaxed">
                Cùng cố vấn chọn hành động phù hợp và theo dõi tiến độ; dự báo không tự quyết định kết quả học vụ.
              </p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};
