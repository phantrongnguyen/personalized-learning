import { useEffect, useState } from 'react'
import { BookOpen, ChartNoAxesColumn, FlaskConical, Menu, ShieldCheck } from 'lucide-react'
import { getCatalog, getModel } from './services/api.js'
import Dashboard from './pages/dashboard/Dashboard.jsx'
import Prediction from './pages/prediction/Prediction.jsx'
import Method from './pages/analytics/Method.jsx'
import Support from './pages/support/Support.jsx'

const pages = [
  { id: 'tong-quan', label: 'Tổng quan', Icon: BookOpen },
  { id: 'goi-y', label: 'Hồ sơ & gợi ý', Icon: ShieldCheck },
  { id: 'du-doan', label: 'Đánh giá', Icon: ChartNoAxesColumn },
  { id: 'phuong-phap', label: 'Phương pháp', Icon: FlaskConical },
]

function activePage() {
  const slug = window.location.hash.slice(1)
  return pages.some((page) => page.id === slug) ? slug : 'tong-quan'
}

export default function App() {
  const [page, setPage] = useState(activePage)
  const [catalog, setCatalog] = useState([])
  const [model, setModel] = useState(null)
  const [error, setError] = useState('')
  const [selectedModule, setSelectedModule] = useState('BBB')

  useEffect(() => {
    const onHashChange = () => setPage(activePage())
    window.addEventListener('hashchange', onHashChange)
    Promise.all([getCatalog(), getModel()])
      .then(([courses, info]) => { setCatalog(courses); setModel(info); setError('') })
      .catch(() => setError('Không kết nối được API. Hãy khởi động backend để dùng tính năng dự đoán.'))
    return () => window.removeEventListener('hashchange', onHashChange)
  }, [])

  function navigate(destination) {
    window.location.hash = destination
    setPage(destination)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  function start(moduleCode) {
    if (moduleCode) setSelectedModule(moduleCode)
    navigate(moduleCode ? 'du-doan' : 'goi-y')
  }

  const navigation = (className) => (
    <nav className={className} aria-label="Điều hướng chính">
      {pages.map(({ id, label, Icon }) => (
        <button type="button" key={id} onClick={() => navigate(id)}
          className={`nav-item ${page === id ? 'is-active' : ''}`}
          aria-current={page === id ? 'page' : undefined}>
          <Icon size={20} strokeWidth={1.9} aria-hidden="true" />
          <span>{label}</span>
        </button>
      ))}
    </nav>
  )

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <button type="button" className="brand" onClick={() => navigate('tong-quan')} aria-label="Về tổng quan">
          <span className="brand-mark"><BookOpen size={22} aria-hidden="true" /></span>
          <span><strong>Góc học tập</strong><small>CLHT · Bản thử nghiệm</small></span>
        </button>
        <p className="sidebar-caption">ĐIỀU HƯỚNG</p>
        {navigation('side-nav')}
        <div className="sidebar-note">
          <ShieldCheck size={22} aria-hidden="true" />
          <strong>Không tạo hồ sơ người học</strong>
          <span>Dữ liệu nhập được gửi tới API để tính rồi không lưu vào cơ sở dữ liệu.</span>
        </div>
      </aside>

      <div className="main-area">
        <header className="topbar">
          <button type="button" className="brand mobile-brand" onClick={() => navigate('tong-quan')} aria-label="Về tổng quan">
            <span className="brand-mark"><BookOpen size={20} aria-hidden="true" /></span>
            <strong>Góc học tập</strong>
          </button>
          <span className="topbar-label"><Menu size={16} aria-hidden="true" /> OULAD · cutoff 75%</span>
          <span className="demo-pill">Bản demo nghiên cứu</span>
        </header>
        <main id="main-content" className="content">
          {error && <div className="connection-error" role="alert">{error}</div>}
          {page === 'tong-quan' && <Dashboard catalog={catalog} model={model} onStart={start} />}
          {page === 'goi-y' && <Support />}
          {page === 'du-doan' && <Prediction catalog={catalog} model={model} selectedModule={selectedModule} />}
          {page === 'phuong-phap' && <Method model={model} />}
        </main>
      </div>
      {navigation('bottom-nav')}
    </div>
  )
}
