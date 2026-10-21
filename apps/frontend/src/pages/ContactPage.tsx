import React, { useState } from 'react';
import { useApp } from '../state/AppContext';
import { Mail, MapPin, Send, HelpCircle, ChevronDown, Building2, PhoneCall, Clock } from 'lucide-react';

export const ContactPage: React.FC = () => {
  const { addToast } = useApp();

  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');
  const [openFaq, setOpenFaq] = useState<number | null>(0);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    addToast(`Biểu mẫu minh họa chưa gửi thông tin của ${name} đến máy chủ. Vui lòng liên hệ nhóm dự án qua kênh đã xác minh.`, 'info');
    setName('');
    setEmail('');
    setMessage('');
  };

  const faqs = [
    {
      q: 'Hệ thống EduRisk AI tích hợp với các nền tảng LMS hiện có như thế nào?',
      a: 'Ứng dụng có API phục vụ các phân hệ nội bộ. Chưa kiểm chứng tích hợp hai chiều với Canvas, Moodle, Blackboard hoặc hệ thống LMS bên ngoài.',
    },
    {
      q: 'Chính sách bảo mật dữ liệu người học và quyền riêng tư (Privacy)?',
      a: 'Dữ liệu OULAD là dữ liệu nghiên cứu lịch sử. Chưa có đánh giá tuân thủ pháp lý, kiểm toán an toàn thông tin hoặc xác nhận triển khai trên dữ liệu HUIT. Không nhập thông tin cá nhân thật vào bản demo.',
    },
    {
      q: 'Cơ sở đào tạo có thể triển khai Private Cloud hoặc On-Premise không?',
      a: 'Repo có cấu hình Docker để chạy thử cục bộ. Chưa đánh giá triển khai Kubernetes, Private Cloud hoặc cam kết thời gian hoạt động.',
    },
    {
      q: 'Ý nghĩa của mốc Cutoff 75% đối với công tác quản trị rủi ro đào tạo?',
      a: 'Mốc 75% thời lượng học phần là mốc quan sát trong thí nghiệm OULAD. Không suy ra số tuần còn lại hoặc hiệu quả can thiệp ở một học kỳ thực tế; xem báo cáo đánh giá model để biết thước đo và giới hạn.',
    },
  ];

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 space-y-12">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-extrabold text-white tracking-tight">
          Liên Hệ Hợp Tác &amp; Tư Vấn Doanh Nghiệp
        </h1>
        <p className="text-sm text-slate-400 mt-2">
          Giải pháp Trí tuệ Nhân tạo Phân tích Học tập &amp; Quản trị Rủi ro Đào tạo dành cho Trường Đại học &amp; Doanh nghiệp
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Enterprise Office & Support Info */}
        <div className="lg:col-span-5 space-y-6">
          <div className="p-6 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-xl space-y-4">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <Building2 className="w-5 h-5 text-brand-400" />
              <span>Trung Tâm Giải Pháp Doanh Nghiệp</span>
            </h3>

            <div className="space-y-3.5 text-xs text-slate-300">
              <div className="flex items-start gap-2.5">
                <MapPin className="w-4 h-4 text-slate-500 shrink-0 mt-0.5" />
                <div>
                  <div className="font-semibold text-slate-100">
                    Trung tâm R&amp;D Giải pháp AI Giáo dục
                  </div>
                  <div className="text-slate-400">Thông tin địa chỉ liên hệ cần được nhóm dự án xác nhận trước khi công bố.</div>
                </div>
              </div>

              <div className="flex items-start gap-2.5">
                <PhoneCall className="w-4 h-4 text-slate-500 shrink-0 mt-0.5" />
                <div>
                  <div className="font-semibold text-slate-100">Tổng đài Hỗ trợ Doanh nghiệp:</div>
                  <div className="text-slate-400 font-mono">
                    Chưa thiết lập tổng đài hỗ trợ.
                  </div>
                </div>
              </div>

              <div className="flex items-start gap-2.5">
                <Mail className="w-4 h-4 text-slate-500 shrink-0 mt-0.5" />
                <div>
                  <div className="font-semibold text-slate-100">Kênh liên hệ trực tuyến:</div>
                  <div className="text-slate-400">
                    &bull; Tư vấn giải pháp: <code className="text-brand-400">Chưa thiết lập</code>
                  </div>
                  <div className="text-slate-400">
                    &bull; Hỗ trợ kỹ thuật &amp; API: <code className="text-brand-400">Chưa thiết lập</code>
                  </div>
                </div>
              </div>

              <div className="flex items-start gap-2.5">
                <Clock className="w-4 h-4 text-slate-500 shrink-0 mt-0.5" />
                <div>
                  <div className="font-semibold text-slate-100">Thời gian làm việc:</div>
                  <div className="text-slate-400">Chưa có lịch hỗ trợ chính thức.</div>
                </div>
              </div>
            </div>
          </div>

          {/* Consultation Request Form */}
          <form
            onSubmit={handleSubmit}
            className="p-6 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-xl space-y-4"
          >
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <Send className="w-4 h-4 text-brand-400" />
              <span>Xem thử biểu mẫu liên hệ</span>
            </h3>

            <p className="text-xs text-amber-300">Biểu mẫu chỉ minh họa, chưa gửi hoặc lưu dữ liệu. Không nhập thông tin cá nhân thật.</p>
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Họ và tên người đại diện:</label>
              <input
                type="text"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Nguyễn Văn A"
                className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-750 text-slate-100 text-xs focus:border-brand-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Email tổ chức / trường học:</label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="contact@university.edu.vn"
                className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-750 text-slate-100 text-xs focus:border-brand-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Nhu cầu triển khai hoặc câu hỏi:</label>
              <textarea
                required
                rows={3}
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="Ví dụ: Cần tích hợp dự báo nguy cơ học tập với hệ thống Moodle 4.x cho 15.000 sinh viên..."
                className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-750 text-slate-100 text-xs focus:border-brand-500 focus:outline-none"
              />
            </div>

            <button
              type="submit"
              className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-semibold text-xs shadow-lg shadow-brand-600/20 transition-all"
            >
              <span>Kiểm tra biểu mẫu (không gửi)</span>
            </button>
          </form>
        </div>

        {/* Enterprise FAQs */}
        <div className="lg:col-span-7 space-y-4">
          <div className="flex items-center gap-2 pb-2">
            <HelpCircle className="w-5 h-5 text-cyan-400" />
            <h3 className="text-base font-bold text-white">Câu Hỏi Thường Gặp Của Doanh Nghiệp &amp; Trường Học</h3>
          </div>

          <div className="space-y-3">
            {faqs.map((faq, idx) => {
              const isOpen = openFaq === idx;
              return (
                <div
                  key={idx}
                  className="rounded-2xl border border-slate-800 bg-slate-900/80 overflow-hidden transition-all"
                >
                  <button
                    type="button"
                    onClick={() => setOpenFaq(isOpen ? null : idx)}
                    className="w-full p-4 text-left flex items-center justify-between gap-3 text-xs sm:text-sm font-semibold text-slate-200 hover:text-white"
                  >
                    <span>{faq.q}</span>
                    <ChevronDown
                      className={`w-4 h-4 text-slate-400 shrink-0 transition-transform ${
                        isOpen ? 'transform rotate-180 text-brand-400' : ''
                      }`}
                    />
                  </button>

                  {isOpen && (
                    <div className="p-4 pt-0 text-xs text-slate-300 leading-relaxed border-t border-slate-800/60 bg-slate-950/40">
                      {faq.a}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};
