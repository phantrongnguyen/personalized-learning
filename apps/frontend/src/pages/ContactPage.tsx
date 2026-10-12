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
    addToast(`Cảm ơn bạn ${name}! Đội ngũ chuyên gia EduRisk AI sẽ liên hệ lại trong vòng 24 giờ làm việc.`, 'success');
    setName('');
    setEmail('');
    setMessage('');
  };

  const faqs = [
    {
      q: 'Hệ thống EduRisk AI tích hợp với các nền tảng LMS hiện có như thế nào?',
      a: 'EduRisk AI hỗ trợ chuẩn kết nối giáo dục quốc tế IMS LTI 1.3 và RESTful API. Hệ thống có thể tích hợp hai chiều liền mạch với Canvas LMS, Moodle, Blackboard, hoặc các hệ thống SIS/LMS nội bộ của cơ sở đào tạo mà không làm gián đoạn vận hành.',
    },
    {
      q: 'Chính sách bảo mật dữ liệu người học và quyền riêng tư (Privacy)?',
      a: 'Hệ thống tuân thủ nghiêm ngặt các quy định bảo vệ dữ liệu giáo dục (FERPA, GDPR và Nghị định 13/2023/NĐ-CP). Dữ liệu được mã hóa chuẩn AES-256 khi lưu trữ và TLS 1.3 trong quá trình truyền tải. Các mô hình máy học chỉ suy luận trên vector đặc trưng hành vi ẩn danh.',
    },
    {
      q: 'Cơ sở đào tạo có thể triển khai Private Cloud hoặc On-Premise không?',
      a: 'Hoàn toàn có thể. Bên cạnh mô hình Cloud SaaS, EduRisk AI hỗ trợ đóng gói trọn gói qua Docker / Kubernetes để triển khai trực tiếp trên hạ tầng Private Cloud hoặc cụm máy chủ nội bộ của quý đơn vị với đầy đủ cam kết SLA 99.9%.',
    },
    {
      q: 'Ý nghĩa của mốc Cutoff 75% đối với công tác quản trị rủi ro đào tạo?',
      a: 'Mốc 75% học kỳ là "thời điểm vàng" để can thiệp: lượng dữ liệu tương tác LMS đủ phong phú để mô hình đạt độ chính xác >93%, đồng thời vẫn còn đủ từ 3 đến 4 tuần trước kỳ thi để cố vấn học tập và giảng viên triển khai các kế hoạch can thiệp sư phạm cá nhân hóa.',
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
                  <div className="text-slate-400">Khu Công nghệ Cao TP.HCM (SHTP), TP. Hồ Chí Minh, Việt Nam</div>
                </div>
              </div>

              <div className="flex items-start gap-2.5">
                <PhoneCall className="w-4 h-4 text-slate-500 shrink-0 mt-0.5" />
                <div>
                  <div className="font-semibold text-slate-100">Tổng đài Hỗ trợ Doanh nghiệp:</div>
                  <div className="text-slate-400 font-mono">
                    Hotline: <strong className="text-slate-200">1900 888 668</strong> &bull; Tel: <strong className="text-slate-200">(+84) 28 7300 8866</strong>
                  </div>
                </div>
              </div>

              <div className="flex items-start gap-2.5">
                <Mail className="w-4 h-4 text-slate-500 shrink-0 mt-0.5" />
                <div>
                  <div className="font-semibold text-slate-100">Kênh liên hệ trực tuyến:</div>
                  <div className="text-slate-400">
                    &bull; Tư vấn giải pháp: <code className="text-brand-400">enterprise@edurisk.ai</code>
                  </div>
                  <div className="text-slate-400">
                    &bull; Hỗ trợ kỹ thuật &amp; API: <code className="text-brand-400">support@edurisk.ai</code>
                  </div>
                </div>
              </div>

              <div className="flex items-start gap-2.5">
                <Clock className="w-4 h-4 text-slate-500 shrink-0 mt-0.5" />
                <div>
                  <div className="font-semibold text-slate-100">Thời gian làm việc:</div>
                  <div className="text-slate-400">Thứ Hai – Thứ Sáu: 08:00 – 17:30 (Hỗ trợ 24/7 đối với gói Enterprise SLA)</div>
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
              <span>Đăng Ký Tư Vấn &amp; Trải Nghiệm Demo</span>
            </h3>

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
              <span>Gửi yêu cầu tư vấn</span>
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
