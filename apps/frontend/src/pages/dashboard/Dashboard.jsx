import { ArrowRight, BookOpenCheck, CircleHelp, MousePointerClick, ScanHeart, Sparkles } from 'lucide-react'

const swatches = ['indigo', 'peach', 'mint', 'lavender', 'butter', 'sky', 'coral']

function StudyVisual() {
  return (
    <div className="study-visual" aria-hidden="true">
      <div className="visual-orbit orbit-one" /><div className="visual-orbit orbit-two" />
      <div className="floating-card little-card"><span className="little-dot" /> Theo dõi tiến độ học tập</div>
      <div className="visual-phone">
        <div className="phone-notch" />
        <div className="phone-content">
          <span className="phone-eyebrow">HỌC PHẦN · BBB</span>
          <strong>Tiến độ học tập</strong>
          <span className="phone-line" />
          <div className="phone-mini-card"><BookOpenCheck size={22} /><span>Nhìn lại tiến độ<small>Thông tin tại cutoff</small></span></div>
          <div className="phone-chart"><i /><i /><i /><i /><i /><i /><i /></div>
          <div className="phone-navigation"><span /><span /><span /></div>
        </div>
      </div>
      <div className="floating-card chart-float"><Sparkles size={17} /> Gợi ý có căn cứ</div>
    </div>
  )
}

export default function Dashboard({ catalog, model, onStart }) {
  const modules = [...new Set(catalog.map((course) => course.code_module))]
  return (
    <div className="page-enter">
      <div className="page-heading"><span className="eyebrow">TỔNG QUAN</span><p>Theo dõi tiến độ và xem xét nhu cầu hỗ trợ học tập.</p></div>
      <section className="hero-card">
        <div className="hero-copy">
          <span className="hero-tag"><span className="pulse-dot" /> HỌC TẬP CÓ DỮ LIỆU</span>
          <h1>Dự báo nguy cơ.<br /><em>Gợi ý hỗ trợ học tập.</em></h1>
          <p>Nhìn lại dữ liệu ở mốc 75% học phần, dự báo nguy cơ và xem những bước hỗ trợ có căn cứ. Mỗi gợi ý đều chỉ rõ điều đã quan sát được và điều chưa thể kết luận.</p>
          <button type="button" className="button button-light" onClick={() => onStart()}>
            Khám phá hồ sơ & gợi ý <ArrowRight size={18} aria-hidden="true" />
          </button>
          <span className="hero-footnote">Không cần tài khoản · Không lưu dữ liệu bạn nhập</span>
        </div>
        <StudyVisual />
      </section>

      <div className="section-title"><div><span className="eyebrow">THÔNG TIN HỆ THỐNG</span><h2>Dữ liệu và mô hình</h2></div></div>
      <div className="stats-grid">
        <div className="stat-card"><span className="stat-icon icon-blue"><BookOpenCheck size={22} /></span><strong>07</strong><span>mã học phần OULAD</span><small>AAA đến GGG</small></div>
        <div className="stat-card"><span className="stat-icon icon-amber"><MousePointerClick size={22} /></span><strong>75%</strong><span>tiến trình môn học</span><small>Không phải 75% số dòng</small></div>
        <div className="stat-card"><span className="stat-icon icon-green"><ScanHeart size={22} /></span><strong>{model?.feature_count ?? '17'}</strong><span>đặc trưng được chọn</span><small>HCO–VNLS + LightGBM</small></div>
      </div>

      <div className="section-title module-heading"><div><span className="eyebrow">HỌC PHẦN</span><h2>Chọn học phần để bắt đầu</h2></div><span className="muted-small">Tên học phần chỉ có mã trong OULAD</span></div>
      {modules.length ? <div className="modules-grid">
        {modules.map((moduleCode, index) => {
          const count = catalog.filter((course) => course.code_module === moduleCode).length
          return <button type="button" className="module-card" key={moduleCode} onClick={() => onStart(moduleCode)}>
            <span className={`module-icon ${swatches[index]}`}><BookOpenCheck size={24} strokeWidth={1.8} aria-hidden="true" /></span>
            <span className="module-details"><strong>Học phần {moduleCode}</strong><small>{count} kỳ học trong dữ liệu</small></span>
            <ArrowRight size={17} aria-hidden="true" />
          </button>
        })}
      </div> : <div className="empty-card">Đang tải danh sách học phần từ backend…</div>}

      <div className="research-note"><CircleHelp size={22} aria-hidden="true" /><div><strong>Đây là demo nghiên cứu, không phải kết luận về người học.</strong><p>Xác suất dự báo không cho biết nguyên nhân. Gợi ý theo quy tắc chưa được chứng minh làm tăng điểm và không thay thế trao đổi với giảng viên.</p></div></div>
    </div>
  )
}
