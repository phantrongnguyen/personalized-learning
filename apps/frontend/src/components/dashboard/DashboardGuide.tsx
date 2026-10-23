import React, { useId, useRef } from 'react';
import { BookOpen, X } from 'lucide-react';
import { FIELDS } from '@shared/constants';

const featureDescriptions: Record<string, string> = {
  code_module: 'Học phần đang được phân tích, theo mã khóa học OULAD.',
  gender: 'Giới tính được ghi nhận trong hồ sơ: F hoặc M.',
  highest_education: 'Nhóm trình độ học vấn cao nhất trước khi đăng ký học.',
  age_band: 'Nhóm tuổi của sinh viên theo phân nhóm OULAD.',
  studied_credits: 'Số tín chỉ đang theo học, dùng đơn vị tín chỉ OULAD.',
  date_registration: 'Số ngày đăng ký so với ngày bắt đầu học phần.',
  total_clicks_to_t: 'Tổng số lượt tương tác trên môi trường học trực tuyến đến cutoff.',
  clicks_resource_to_t: 'Lượt tương tác với tài nguyên học tập đến cutoff.',
  clicks_url_to_t: 'Lượt tương tác với các tài nguyên dạng liên kết URL đến cutoff.',
  active_days_to_t: 'Số ngày có ít nhất một lượt tương tác đến cutoff.',
  active_day_ratio: 'Tỷ lệ ngày có hoạt động trong khoảng thời gian quan sát.',
  days_since_last_activity: 'Số ngày từ hoạt động cuối cùng đến cutoff, không tính đến hôm nay.',
  clicks_recent_7: 'Tổng lượt tương tác trong cửa sổ 7 ngày kết thúc tại cutoff.',
  clicks_recent_30: 'Tổng lượt tương tác trong cửa sổ 30 ngày kết thúc tại cutoff.',
  assessments_submitted_to_t: 'Số bài đánh giá đã được nộp đến cutoff.',
  late_submissions_to_t: 'Số bài đánh giá đã nộp nhưng quá hạn đến cutoff.',
  submission_rate: 'Tỷ lệ nộp bài theo các bài đánh giá thuộc phạm vi quan sát tại cutoff.',
};

export const DashboardGuide: React.FC = () => {
  const dialog = useRef<HTMLDialogElement>(null);
  const titleId = useId();
  return <>
    <button type="button" onClick={() => dialog.current?.showModal()}
      className="inline-flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-semibold text-brand-300 hover:bg-brand-500/10 focus-visible:outline focus-visible:outline-2 focus-visible:outline-brand-400">
      <BookOpen className="h-4 w-4" aria-hidden="true" /> Hướng dẫn
    </button>
    <dialog ref={dialog} aria-labelledby={titleId}
      onClick={event => {
        if (event.target !== event.currentTarget) return;
        const bounds = event.currentTarget.getBoundingClientRect();
        if (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom) dialog.current?.close();
      }}
      className="m-auto w-[calc(100%_-_2rem)] max-w-3xl max-h-[85dvh] overflow-hidden rounded-2xl border border-slate-700 bg-slate-900 p-0 text-slate-300 shadow-2xl backdrop:bg-slate-950/80 backdrop:backdrop-blur-sm">
    <div className="flex max-h-[85dvh] flex-col">
    <header className="flex shrink-0 items-center justify-between gap-3 border-b border-slate-800 px-5 py-4">
    <h2 id={titleId} className="flex items-center gap-2 text-sm font-semibold text-white">
      <BookOpen className="h-4 w-4 text-brand-400" aria-hidden="true" />
      Hướng dẫn &amp; giải thích chỉ số
    </h2>
    <button type="button" autoFocus onClick={() => dialog.current?.close()} aria-label="Đóng hướng dẫn"
      className="rounded-lg p-2 text-slate-400 hover:bg-slate-800 hover:text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-brand-400">
      <X className="h-5 w-5" aria-hidden="true" />
    </button>
    </header>
    <div className="min-h-0 overflow-y-auto overscroll-contain px-5 pb-5 text-xs leading-relaxed sm:text-sm">
    <ol className="mt-3 list-decimal space-y-2 pl-5">
      <li>Chọn mẫu SV hoặc nhập hồ sơ qua cả ba tab. Sử dụng thông tin đã có tại mốc 75% thời lượng học phần.</li>
      <li>Nhấn <strong className="text-white">Phân tích nguy cơ học tập</strong>. Kết quả bên phải và Radar sử dụng hồ sơ của lần phân tích đó; sửa đầu vào thì cần nhấn phân tích lại.</li>
      <li>Đọc xác suất nguy cơ, đối chiếu các chiều Radar và xem gợi ý. Lịch sử bên dưới giúp xem lại các lần phân tích; gợi ý cần người phụ trách xem xét trước khi áp dụng.</li>
    </ol>

    <details className="mt-4 border-t border-slate-800 pt-3">
      <summary className="cursor-pointer font-semibold text-brand-300 focus-visible:outline focus-visible:outline-2 focus-visible:outline-brand-400">Hiểu kết quả và các chỉ số model</summary>
      <dl className="mt-3 space-y-3">
        <div><dt className="font-semibold text-slate-100">LightGBM · Xác suất nguy cơ</dt><dd>Model ước lượng nguy cơ trượt hoặc bỏ học từ hồ sơ OULAD. Ví dụ 70% là xác suất nguy cơ model trả về, không phải độ chính xác 70% và không bảo đảm kết quả của sinh viên.</dd></div>
        <div><dt className="font-semibold text-slate-100">Accuracy · Precision · Recall · F1</dt><dd>Accuracy là tỷ lệ dự đoán đúng trên tập đánh giá. Precision cho biết trong các hồ sơ bị cảnh báo có bao nhiêu hồ sơ thực sự thuộc nhóm nguy cơ. Recall cho biết model phát hiện được bao nhiêu trong số hồ sơ nguy cơ thực tế. F1 cân bằng Precision và Recall.</dd></div>
        <div><dt className="font-semibold text-slate-100">ROC-AUC · AP (Average Precision)</dt><dd>ROC-AUC đánh giá khả năng phân biệt hai nhóm qua nhiều ngưỡng; AP tổng hợp quan hệ Precision–Recall cho nhóm nguy cơ. Đây là chỉ số trên một tập đánh giá, không phải điểm của hồ sơ đang nhập.</dd></div>
        <div><dt className="font-semibold text-slate-100">Radar · % mốc tham khảo</dt><dd>Radar so sánh 6 chỉ số hành vi với mốc tham khảo, giới hạn hiển thị 100%. Chỉ số dưới 25% mốc có màu đỏ; đây là quy ước hiển thị, không phải phân loại rủi ro của model. Thiếu dữ liệu không đồng nghĩa với điểm 0.</dd></div>
      </dl>
      <p className="mt-3 text-slate-400">Kết quả đánh giá trên OULAD chưa chứng minh độ chính xác trên dữ liệu HUIT. Nhãn dưới ngưỡng cảnh báo không bảo đảm sinh viên không cần hỗ trợ.</p>
    </details>

    <details className="mt-3 border-t border-slate-800 pt-3">
      <summary className="cursor-pointer font-semibold text-brand-300 focus-visible:outline focus-visible:outline-2 focus-visible:outline-brand-400">Hiểu {FIELDS.length} đặc trưng đầu vào</summary>
      <p className="mt-3">Các lượt click và bài nộp được tính đến cutoff; cửa sổ 7/30 ngày cũng kết thúc tại cutoff. Tỷ lệ nhập từ 0 đến 1 (0,5 = 50%); không dùng dữ liệu phát sinh sau mốc quan sát.</p>
      <p className="mt-2 text-slate-400">Ngày đăng ký âm nghĩa là trước khai giảng. Số bài nộp muộn không vượt số bài đã nộp. Tín chỉ và nhóm học vấn dùng định nghĩa OULAD, chưa quy đổi sang HUIT.</p>
      <dl className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-2">
        {FIELDS.map(field => (
          <div key={field.key} className="min-w-0 rounded-lg border border-slate-800 p-2.5">
            <dt className="font-semibold text-slate-100">{field.label}</dt>
            <dd className="mt-1 text-slate-300">{featureDescriptions[field.key]}</dd>
            <dd className="mt-1 break-words text-slate-400">{field.hint}</dd>
            <dd className="mt-1 break-all font-mono text-[10px] text-slate-500">{field.key}</dd>
          </div>
        ))}
      </dl>
    </details>
    </div>
    </div>
    </dialog>
  </>;
};
