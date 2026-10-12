import React from 'react';
import { BrainCircuit, Cpu, Target, Award, ArrowUpRight } from 'lucide-react';

export const AboutPage: React.FC = () => {
  return (
    <div className="max-w-5xl mx-auto px-4 py-8 space-y-12">
      {/* Header */}
      <div>
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-xs font-semibold mb-3">
          <BrainCircuit className="w-3.5 h-3.5" />
          <span>Kiến Trúc Cốt Lõi &amp; Công Nghệ Đột Phá</span>
        </div>
        <h1 className="text-3xl font-extrabold text-white tracking-tight">
          Thuật Toán Lai HCO-VNLS &amp; Mô Hình LightGBM
        </h1>
        <p className="text-sm text-slate-400 mt-2 max-w-3xl leading-relaxed">
          Nền tảng trí tuệ nhân tạo EduRisk AI kết hợp thuật toán tối ưu hóa tổ hợp đa mục tiêu và mô hình học máy phân lớp tốc độ cao, hỗ trợ chẩn đoán nguy cơ và tự động kê đơn can thiệp cho hệ thống LMS trường học và doanh nghiệp.
        </p>
      </div>

      {/* 3 Pillars */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800">
          <div className="p-2.5 rounded-xl bg-brand-500/10 text-brand-400 w-fit mb-4">
            <Cpu className="w-5 h-5" />
          </div>
          <h3 className="text-base font-bold text-white mb-2">HCO (Khám phá toàn cục)</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Human Conception Optimization mô phỏng quá trình thụ tinh tự nhiên với các pha bơi tự do, 
            điều hướng dịch nhầy và siêu hoạt hóa (Hyperactivation) bằng nhiễu Cauchy để thoát bẫy cực trị địa phương.
          </p>
        </div>

        <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800">
          <div className="p-2.5 rounded-xl bg-cyan-500/10 text-cyan-400 w-fit mb-4">
            <Target className="w-5 h-5" />
          </div>
          <h3 className="text-base font-bold text-white mb-2">VNLS (Khai thác cục bộ)</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Variable Neighborhood Local Search áp dụng 4 cấu trúc lân cận nhị phân (1-bit flip, 2-bit flip, 
            bit swap, feature drop) nhằm tinh chỉnh và rút gọn tối đa tập thuộc tính sau mỗi thế hệ HCO.
          </p>
        </div>

        <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800">
          <div className="p-2.5 rounded-xl bg-purple-500/10 text-purple-400 w-fit mb-4">
            <Award className="w-5 h-5" />
          </div>
          <h3 className="text-base font-bold text-white mb-2">Mục Tiêu Đa Tiêu Chí</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Hàm thích nghi cân bằng giữa tối đa hóa hiệu năng phân loại (85% F1-Score) và tối thiểu hóa 
            số lượng thuộc tính cần thu thập (15% tỷ lệ loại bỏ thuộc tính dư thừa).
          </p>
        </div>
      </div>

      {/* Fitness Formula Box */}
      <div className="p-6 rounded-2xl bg-slate-950/70 border border-slate-800/80 space-y-3 font-mono">
        <div className="text-xs text-brand-400 font-semibold uppercase tracking-wider">
          📐 Hàm thích ứng tối ưu hóa đa mục tiêu (Fitness Function):
        </div>
        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 text-center text-sm sm:text-base text-slate-100 overflow-x-auto">
          <code>Fitness(X) = 0.85 &times; F1_Score(X) + 0.15 &times; (1 - |X| / 30)</code>
        </div>
        <p className="text-xs text-slate-400 font-sans leading-relaxed">
          Trong đó: <code className="text-slate-300">X</code> là vector nhị phân đại diện cho tập đặc trưng được chọn;{' '}
          <code className="text-slate-300">|X|</code> là số lượng đặc trưng được kích hoạt;{' '}
          <code className="text-slate-300">30</code> là tổng số chiều đặc trưng ban đầu từ tập dữ liệu OULAD.
        </p>
      </div>

      {/* Comparison Table */}
      <div className="space-y-4">
        <div>
          <h3 className="text-lg font-bold text-white">Bảng Đối Chứng Hiệu Năng Thực Nghiệm</h3>
          <p className="text-xs text-slate-400">
            Kết quả kiểm nghiệm trên 6.519 mẫu dữ liệu kiểm thử độc lập (Test 20%) phân tầng
          </p>
        </div>

        <div className="overflow-x-auto rounded-2xl border border-slate-800 bg-slate-900/80">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950 text-slate-400 font-semibold border-b border-slate-800">
              <tr>
                <th className="py-3 px-4">Phương pháp tối ưu</th>
                <th className="py-3 px-4 text-center">Số đặc trưng</th>
                <th className="py-3 px-4 text-center">Tỷ lệ giảm chiều</th>
                <th className="py-3 px-4 text-right">Accuracy</th>
                <th className="py-3 px-4 text-right">F1-Score</th>
                <th className="py-3 px-4 text-right">ROC-AUC</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              <tr className="hover:bg-slate-850/50">
                <td className="py-3 px-4 font-sans font-medium text-slate-300">Baseline (Toàn bộ)</td>
                <td className="py-3 px-4 text-center text-slate-400">30 / 30</td>
                <td className="py-3 px-4 text-center text-slate-400">0.0%</td>
                <td className="py-3 px-4 text-right text-slate-300">93.04%</td>
                <td className="py-3 px-4 text-right text-slate-300">0.9304</td>
                <td className="py-3 px-4 text-right text-slate-300">0.9799</td>
              </tr>
              <tr className="hover:bg-slate-850/50">
                <td className="py-3 px-4 font-sans font-medium text-slate-300">Genetic Algorithm (GA)</td>
                <td className="py-3 px-4 text-center text-slate-400">12 / 30</td>
                <td className="py-3 px-4 text-center text-slate-400">60.0%</td>
                <td className="py-3 px-4 text-right text-slate-300">91.84%</td>
                <td className="py-3 px-4 text-right text-slate-300">0.9184</td>
                <td className="py-3 px-4 text-right text-slate-300">0.9727</td>
              </tr>
              <tr className="hover:bg-slate-850/50">
                <td className="py-3 px-4 font-sans font-medium text-slate-300">Binary PSO</td>
                <td className="py-3 px-4 text-center text-slate-400">5 / 30</td>
                <td className="py-3 px-4 text-center text-slate-400">83.3%</td>
                <td className="py-3 px-4 text-right text-slate-300">93.02%</td>
                <td className="py-3 px-4 text-right text-slate-300">0.9303</td>
                <td className="py-3 px-4 text-right text-slate-300">0.9783</td>
              </tr>
              <tr className="hover:bg-slate-850/50">
                <td className="py-3 px-4 font-sans font-medium text-slate-300">HCO Thuần túy</td>
                <td className="py-3 px-4 text-center text-slate-400">12 / 30</td>
                <td className="py-3 px-4 text-center text-slate-400">60.0%</td>
                <td className="py-3 px-4 text-right text-slate-300">93.39%</td>
                <td className="py-3 px-4 text-right text-slate-300">0.9339</td>
                <td className="py-3 px-4 text-right text-slate-300">0.9810</td>
              </tr>
              <tr className="bg-brand-950/20 font-bold border-l-2 border-brand-500">
                <td className="py-3 px-4 font-sans text-brand-300 flex items-center gap-1.5">
                  <span>HCO-VNLS Đề xuất</span>
                  <ArrowUpRight className="w-3.5 h-3.5" />
                </td>
                <td className="py-3 px-4 text-center text-brand-400">4 / 30</td>
                <td className="py-3 px-4 text-center text-brand-400">86.7%</td>
                <td className="py-3 px-4 text-right text-brand-300">93.04%</td>
                <td className="py-3 px-4 text-right text-brand-300">0.9304</td>
                <td className="py-3 px-4 text-right text-brand-300">0.9785</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
