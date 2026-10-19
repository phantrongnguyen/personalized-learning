import React, { useState } from 'react';
import { BrainCircuit, Cpu, Target, Award } from 'lucide-react';
import { modelEvaluation } from '../data/modelEvaluation';

const percent = (value: number) => `${(value * 100).toLocaleString('vi-VN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}%`;
const score = (value: number) => value.toLocaleString('vi-VN', { minimumFractionDigits: 6, maximumFractionDigits: 6 });
const methodLabel = (method: string) => method === 'Full features' ? 'Đủ đặc trưng' : method;

export const AboutPage: React.FC = () => {
  const [cutoff, setCutoff] = useState(0.75);
  const rows = modelEvaluation.filter(row => row.cutoff === cutoff);
  const reference = rows.find(row => row.model === 'LightGBM' && row.method === 'HCO-VNLS')!;

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 space-y-10">
      <header>
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-xs font-semibold mb-3">
          <BrainCircuit className="w-3.5 h-3.5" />
          <span>Kiến trúc giải pháp và đánh giá thực nghiệm</span>
        </div>
        <h1 className="text-3xl font-extrabold text-white tracking-tight">HCO–VNLS và mô hình dự báo nguy cơ học tập</h1>
        <p className="text-sm text-slate-400 mt-3 max-w-3xl leading-relaxed">
          Chọn tập con đặc trưng bằng HCO–VNLS, dự báo bằng LightGBM và hỗ trợ cố vấn xây dựng kế hoạch học tập.
          Kết quả OULAD dưới đây giúp đánh giá chất lượng phân loại và mức đánh đổi khi giảm số đặc trưng.
        </p>
      </header>

      <section className="grid grid-cols-1 md:grid-cols-3 gap-5" aria-label="Thành phần chọn đặc trưng">
        {[
          { icon: Cpu, title: 'HCO: tìm kiếm tập con', text: 'Triển khai trong dự án cập nhật vị trí và vận tốc, rồi lấy mẫu mask nhị phân qua sigmoid. Mỗi bit biểu thị giữ hoặc bỏ một đặc trưng.' },
          { icon: Target, title: 'VNLS: tìm kiếm lân cận', text: 'Lật một bit quanh mask hiện tại và giữ ứng viên có fitness cao hơn. Hybrid kết hợp bước tìm kiếm quần thể với tinh chỉnh lân cận.' },
          { icon: Award, title: 'Cân bằng chất lượng và độ gọn', text: 'Fitness dùng 85% AP trung bình của GroupKFold ba fold trong train và 15% tỷ lệ giảm số cột. Đây là chọn đặc trưng, không phải tối ưu siêu tham số bộ học.' },
        ].map(({ icon: Icon, title, text }) => (
          <article key={title} className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800">
            <Icon className="w-5 h-5 text-brand-400 mb-4" />
            <h2 className="text-base font-bold text-white mb-2">{title}</h2>
            <p className="text-xs text-slate-400 leading-relaxed">{text}</p>
          </article>
        ))}
      </section>

      <section className="p-5 rounded-2xl bg-slate-950/70 border border-slate-800 space-y-3" aria-label="Hàm fitness">
        <h2 className="text-sm font-semibold text-brand-400">Hàm đánh giá mask</h2>
        <div className="overflow-x-auto rounded-xl bg-slate-900 p-4">
          <code className="text-sm text-slate-100 whitespace-nowrap">Fitness(X) = 0.85 × AP_train_CV(X) + 0.15 × (1 − |X| / 38)</code>
        </div>
        <p className="text-xs text-slate-400 leading-relaxed">
          |X| là số cột được chọn trong 38 đặc trưng gốc trước mã hóa. Fitness cao hơn có thể do ít cột hơn dù AP giảm.
          Ngân sách tìm kiếm là 8 mask mới, seed 41. Tên thuật toán không tự xác nhận việc tái hiện chính xác một công bố cụ thể.
        </p>
      </section>

      <section className="space-y-4" aria-labelledby="evaluation-heading">
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
          <div>
            <h2 id="evaluation-heading" className="text-xl font-bold text-white">Bảng đầy đủ các chỉ số đánh giá mô hình</h2>
            <p className="text-xs text-slate-400 mt-2 leading-relaxed max-w-3xl">
              24 cấu hình: 3 bộ học × 2 mốc quan sát × 4 chế độ đặc trưng. Dữ liệu chia theo sinh viên;
              model fit trên train, chấm trên validation lịch sử. Ngưỡng phân loại 0,5.
            </p>
          </div>
          <label className="text-xs text-slate-300 flex flex-col gap-2 shrink-0">
            Mốc quan sát (cutoff)
            <select value={cutoff} onChange={event => setCutoff(Number(event.target.value))}
              className="rounded-lg bg-slate-900 border border-slate-700 px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-brand-500">
              <option value={0.5}>50% thời lượng học phần</option>
              <option value={0.75}>75% thời lượng học phần</option>
            </select>
          </label>
        </div>
        <p className="text-xs text-slate-400">
          Đang xem {rows.length} cấu hình · {reference.n.toLocaleString('vi-VN')} lượt đăng ký học phần validation.
          Precision, Recall, F1 và AP đo cho lớp nguy cơ (Fail / Withdrawn).
        </p>
        <div className="overflow-x-auto rounded-2xl border border-slate-800 bg-slate-900/80" role="region" aria-label="Chỉ số phân loại; cuộn ngang để xem đủ cột" tabIndex={0}>
          <table className="w-full min-w-[1200px] text-left text-xs">
            <caption className="text-left px-4 py-3 text-slate-400">
              Accuracy / Precision / Recall hiển thị theo %; F1, AP, ROC-AUC và Brier theo thang 0–1.
              Brier càng thấp càng tốt; các chỉ số còn lại càng cao càng tốt trong cùng phạm vi đánh giá.
            </caption>
            <thead className="bg-slate-950 text-slate-300 border-b border-slate-800">
              <tr>{['Bộ học / Phương pháp', 'Cột', 'Giảm cột', 'Accuracy', 'Precision', 'Recall', 'F1 nguy cơ', 'F1 weighted', 'AP', 'ROC-AUC', 'Brier'].map(label => (
                <th key={label} scope="col" className="px-4 py-3 whitespace-nowrap">{label}</th>
              ))}</tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {rows.map(row => (
                <tr key={`${row.model}-${row.method}`} className={row.model === 'LightGBM' && row.method === 'HCO-VNLS' ? 'bg-brand-500/10 text-brand-300' : 'text-slate-300'}>
                  <th scope="row" className="px-4 py-3 text-left font-medium whitespace-nowrap">{row.model} · {methodLabel(row.method)}</th>
                  <td className="px-4 py-3 font-mono">{row.features}/38</td>
                  <td className="px-4 py-3 font-mono">{percent(1 - row.features / 38)}</td>
                  {[percent(row.accuracy), percent(row.precision_risk), percent(row.recall_risk), score(row.f1_risk), score(row.weighted_f1), score(row.average_precision_risk), score(row.roc_auc), score(row.brier_score)].map((value, index) => (
                    <td key={index} className="px-4 py-3 text-right font-mono whitespace-nowrap">{value}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="text-xs text-slate-400 leading-relaxed">
          LightGBM dùng mask đóng băng từ notebook 05b; XGBoost/CatBoost tìm mask với evaluator tương ứng,
          nên các phương pháp cùng tên không nhất thiết dùng cùng tập cột. CatBoost giữ category gốc,
          LightGBM/XGBoost dùng tiền xử lý và One-Hot. Không có model dẫn đầu trên mọi chỉ số.
        </p>

        <details className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
          <summary className="cursor-pointer text-sm font-semibold text-slate-200">Xem số cảnh báo và ma trận nhầm lẫn</summary>
          <div className="overflow-x-auto mt-4" role="region" aria-label="Ma trận nhầm lẫn" tabIndex={0}>
            <table className="w-full min-w-[720px] text-xs text-left">
              <caption className="text-left pb-3 text-slate-400">TN: không nguy cơ nhận đúng; FP: cảnh báo nhầm; FN: bỏ sót nguy cơ; TP: nguy cơ nhận đúng. Số liệu theo lượt đăng ký học phần.</caption>
              <thead><tr>{['Bộ học / Phương pháp', 'TN', 'FP', 'FN', 'TP', 'Tổng cảnh báo', 'Số mẫu'].map(label => <th key={label} scope="col" className="px-3 py-2 text-slate-300">{label}</th>)}</tr></thead>
              <tbody className="divide-y divide-slate-800">
                {rows.map(row => <tr key={`${row.model}-${row.method}`} className="text-slate-400">
                  <th scope="row" className="px-3 py-2 font-medium">{row.model} · {methodLabel(row.method)}</th>
                  {[row.tn, row.fp, row.fn, row.tp, row.alerts, row.n].map((value, index) => <td key={index} className="px-3 py-2 font-mono">{value.toLocaleString('vi-VN')}</td>)}
                </tr>)}
              </tbody>
            </table>
          </div>
        </details>
      </section>

      <section className="space-y-4" aria-labelledby="metric-guide-heading">
        <h2 id="metric-guide-heading" className="text-xl font-bold text-white">Ý nghĩa các chỉ số</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {[
            ['Accuracy', '(TP + TN) / N', 'Tỷ lệ phân loại đúng toàn bộ mẫu; không thay thế Recall khi cần nhận diện nguy cơ.'],
            ['Precision', 'TP / (TP + FP)', 'Trong các cảnh báo nguy cơ, bao nhiêu trường hợp thực sự có nguy cơ.'],
            ['Recall', 'TP / (TP + FN)', 'Trong tất cả trường hợp nguy cơ, bao nhiêu được phát hiện. Recall thấp đồng nghĩa bỏ sót nhiều.'],
            ['F1-score', '2 × Precision × Recall / (Precision + Recall)', 'Cân bằng Precision và Recall cho lớp nguy cơ. F1 weighted là trung bình F1 các lớp, có trọng số theo số mẫu.'],
            ['AP và ROC-AUC', 'Đánh giá trên xác suất trước khi chọn ngưỡng', 'AP tổng hợp precision theo mức recall của lớp nguy cơ; ROC-AUC đo khả năng phân biệt hai lớp. Hai chỉ số không thể dùng thay nhau.'],
            ['Brier score', 'Trung bình (xác suất − nhãn)²', 'Đo sai số xác suất; càng thấp càng tốt. Riêng Brier chưa đủ xác nhận model được hiệu chỉnh tốt.'],
          ].map(([title, formula, text]) => <article key={title} className="p-5 rounded-xl border border-slate-800 bg-slate-900/60">
            <h3 className="font-semibold text-white mb-2">{title}</h3>
            <p className="text-xs text-brand-300 mb-2 break-words">{formula}</p>
            <p className="text-xs text-slate-400 leading-relaxed">{text}</p>
          </article>)}
        </div>
      </section>

      <section className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 space-y-3" aria-labelledby="recommendation-heading">
        <h2 id="recommendation-heading" className="text-xl font-bold text-white">Độ phù hợp của gợi ý học tập</h2>
        <p className="text-sm text-slate-300 leading-relaxed">
          <strong>Chưa có số liệu đánh giá trong các thí nghiệm đã phân tích.</strong> Accuracy, Precision, Recall
          và F1 ở trên đánh giá dự báo nguy cơ, không đo mức phù hợp của gợi ý hoặc hiệu quả can thiệp.
        </p>
        <p className="text-xs text-slate-400 leading-relaxed">
          Để đánh giá phần gợi ý, cần thu thập nhận xét của sinh viên/cố vấn, đo mức hữu ích và tính khả thi,
          tỷ lệ chấp nhận/hoàn thành hành động, rồi đối chiếu thay đổi tiến độ học tập theo một thiết kế đánh giá phù hợp.
          Hiện chưa thể đưa ra điểm phù hợp hoặc kết luận gợi ý làm giảm trượt môn/bỏ học.
        </p>
      </section>

      <aside className="rounded-2xl border border-amber-500/20 bg-amber-500/5 p-6 space-y-3">
        <h2 className="text-base font-bold text-amber-300">Phạm vi và giới hạn kết quả</h2>
        <p className="text-xs text-slate-300 leading-relaxed">
          Hybrid LightGBM 75% giữ 17/38 cột và AP gần đủ cột, nhưng vẫn bỏ sót 362/1.167 trường hợp nguy cơ (31,02%) tại ngưỡng 0,5.
          Qua 5 seed, AP validation trung bình 0,893906 ± 0,003150; Jaccard tập cột 0,2568 cho thấy độ ổn định còn hạn chế.
          Đây là dao động giữa seed trên cùng split, không phải khoảng tin cậy từ các tập dữ liệu độc lập.
        </p>
        <p className="text-xs text-slate-400 leading-relaxed">
          Các điểm tham chiếu thuộc model fit train. Artifact đóng gói được fit lại trên train + validation (19.712 dòng ở cutoff 75%),
          nên các điểm này không phải phép đo độc lập của artifact hoặc model đang chạy. Validation/test lịch sử từng được xem;
          chưa có học kỳ mới độc lập, xác nhận trên HUIT hay ngưỡng được tối ưu cho vận hành. Quần thể thay đổi giữa cutoff 50% và 75%.
        </p>
      </aside>
    </div>
  );
};
