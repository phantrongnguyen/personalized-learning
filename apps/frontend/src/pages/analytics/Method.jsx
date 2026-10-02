import { ArrowDown, BookOpenCheck, CircleHelp, Database, GitMerge, Layers3, ShieldAlert } from 'lucide-react'

const tables = [
  ['courses', 'Học phần, kỳ học, độ dài môn'],
  ['studentInfo', 'Thông tin người học, kết quả cuối'],
  ['studentRegistration', 'Thời điểm đăng ký / rút môn'],
  ['assessments', 'Danh sách bài đánh giá'],
  ['studentAssessment', 'Các lần nộp bài và điểm'],
  ['vle', 'Loại tài nguyên học trực tuyến'],
  ['studentVle', 'Tương tác theo ngày của người học'],
]

export default function Method({ model }) {
  const reference = model?.validation_reference_train_only
  return <div className="page-enter method-page">
    <div className="inner-header"><span className="eyebrow">PHƯƠNG PHÁP · BẰNG CHỨNG VÀ GIỚI HẠN</span><h1>Quy trình xử lý và cơ sở phương pháp</h1><p>Đi từ bảy bảng OULAD đến một lần dự đoán. Phần này giải thích đúng những gì app đang làm — và cả những gì nó chưa làm được.</p></div>

    <section className="method-feature">
      <div><span className="method-icon"><Database size={25} /></span><span className="eyebrow">BƯỚC 01</span><h2>Bắt đầu từ bảy bảng dữ liệu</h2><p>Thông tin được gộp theo một lượt học: <strong>id_student + code_module + code_presentation</strong>. App không hỏi mã sinh viên vì demo chỉ dùng đặc trưng đã tổng hợp, không tra cứu hồ sơ cá nhân.</p></div>
      <div className="table-chips">{tables.map(([name, detail]) => <div key={name}><strong>{name}</strong><span>{detail}</span></div>)}</div>
    </section>

    <div className="method-arrow"><ArrowDown size={22} aria-hidden="true" /></div>
    <div className="method-two">
      <section className="method-card"><span className="method-icon peach-icon"><Layers3 size={24} /></span><span className="eyebrow">BƯỚC 02</span><h2>Cắt đúng thời điểm</h2><p>Cutoff 75% = <strong>⌊0,75 × số ngày của học phần⌋</strong>. Với BBB · 2014J dài 262 ngày, app tính mốc <strong>ngày 196</strong>. Đây là 75% <em>thời lượng</em>, không phải lấy 75% hàng dữ liệu.</p><p>Click và bài nộp sau mốc này không được dùng; nếu không, model sẽ “nhìn thấy tương lai”.</p></section>
      <section className="method-card"><span className="method-icon mint-icon"><GitMerge size={24} /></span><span className="eyebrow">BƯỚC 03</span><h2>Chọn cột và dự đoán</h2><p>HCO–VNLS chọn một mask <strong>17/38 đặc trưng</strong> ở seed 41. Pipeline điền giá trị thiếu, mã hóa cột phân loại rồi dùng <strong>LightGBM 80 cây</strong> để ước lượng nguy cơ Fail hoặc Withdrawn.</p><p>Đổi học phần/kỳ học sẽ đổi ngày cutoff; model chỉ hợp lệ tại mốc 75% này.</p></section>
    </div>

    <section className="method-card"><span className="eyebrow">BƯỚC 04 · PHẦN GỢI Ý</span><h2>Từ bằng chứng đến hành động</h2><p>Đối chiếu từng mã bài để tìm bài đến hạn chưa có bản ghi; không lấy bài nộp sớm bù cho bài thiếu. G01–G04 còn xem bài từng nộp trễ và các cửa sổ không ghi nhận tương tác 7/30 ngày.</p><p><strong>Đây là bộ quy tắc, không phải chiến lược do HCO–VNLS trực tiếp tối ưu.</strong> Chưa có đánh giá cho thấy gợi ý làm tăng điểm. Nếu dữ liệu chưa đủ hoặc không khớp tình huống, hệ thống không tự tạo lời khuyên.</p><a href="#goi-y">Xem hồ sơ và giải thích từng bước →</a></section>

    <section className="method-results"><div className="section-title"><div><span className="eyebrow">BẰNG CHỨNG</span><h2>So sánh kết quả lựa chọn đặc trưng</h2></div></div>
      <div className="comparison-table" role="region" aria-label="So sánh kết quả validation" tabIndex="0">
        <table><thead><tr><th>Cấu hình LightGBM</th><th>Số cột</th><th>AP nguy cơ</th><th>Accuracy</th><th>Recall nguy cơ</th></tr></thead>
          <tbody><tr><th>Dùng tất cả cột</th><td>38</td><td>0,8970</td><td>0,8735</td><td>0,6898</td></tr><tr className="highlight-row"><th>HCO–VNLS chọn cột</th><td>17</td><td>{reference ? reference.average_precision_risk.toFixed(4).replace('.', ',') : '0,8968'}</td><td>{reference ? reference.accuracy.toFixed(4).replace('.', ',') : '0,8741'}</td><td>{reference ? reference.recall_risk.toFixed(4).replace('.', ',') : '0,6898'}</td></tr></tbody>
        </table>
      </div><p className="method-caption">Cùng cutoff 75%, cùng LightGBM 80 cây; số trên validation của thí nghiệm fit trên train. Model đóng gói cho app đã fit lại train + validation nên không nhận các số này làm đánh giá mới.</p>
    </section>

    <div className="method-two bottom-method">
      <section className="method-card"><span className="method-icon"><BookOpenCheck size={23} /></span><h2>Ý nghĩa các chỉ số đánh giá</h2><p><strong>AP</strong> nói về chất lượng xếp các trường hợp nguy cơ lên đầu danh sách. <strong>Recall nguy cơ</strong> là tỷ lệ ca thật sự nguy cơ được cảnh báo ở ngưỡng 0,5. <strong>Accuracy</strong> là tỷ lệ dự đoán đúng chung ở ngưỡng ấy.</p></section>
      <section className="method-card caution-card"><span className="method-icon peach-icon"><ShieldAlert size={23} /></span><h2>Giới hạn áp dụng</h2><p>Mask được chọn không chứng minh từng cột là nguyên nhân. Validation và test lịch sử đã từng được xem; chưa có kỳ học mới độc lập. Chưa kiểm tra công bằng theo giới và nhóm tuổi. Xác suất chưa hiệu chỉnh cho can thiệp thực tế; không dùng app để tự động quyết định học vụ.</p></section>
    </div>
    <div className="method-footer"><CircleHelp size={20} /><span>Trang Hồ sơ & gợi ý dùng sáu bản trích rút train đã bỏ mã sinh viên, nhãn cuối kỳ và đổi mã bài, cùng một tình huống kiểm thử tổng hợp. Không coi đó là bảo đảm ẩn danh tuyệt đối.</span></div>
  </div>
}
