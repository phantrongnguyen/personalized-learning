import { useEffect, useState } from 'react'
import { ArrowRight, FileCheck2, Info } from 'lucide-react'
import { evaluateCase, getSupportCases } from '../../services/api.js'
import SupportResult from './SupportResult.jsx'

export default function Support() {
  const [cases, setCases] = useState([])
  const [selected, setSelected] = useState('')
  const [result, setResult] = useState(null)
  const [pending, setPending] = useState(false)
  const [error, setError] = useState('')
  const current = cases.find((item) => item.id === selected)

  useEffect(() => {
    let active = true
    getSupportCases().then((items) => { if (active) { setCases(items); setSelected(items[0]?.id ?? '') } })
      .catch((failure) => { if (active) setError(failure.message) })
    return () => { active = false }
  }, [])

  async function analyze() {
    setPending(true)
    setError('')
    setResult(null)
    try { setResult(await evaluateCase(selected)) }
    catch (failure) { setError(failure.message) }
    finally { setPending(false) }
  }

  return <div className="support-page page-enter">
    <div className="inner-header"><span className="eyebrow">PHÂN TÍCH HỒ SƠ</span><h1>Dự báo và gợi ý học tập</h1><p>Chọn một hồ sơ minh họa, xem dữ liệu được phép biết rồi chạy dự báo và đối chiếu bằng chứng. Không dùng kết quả cuối kỳ để đưa ra lời khuyên.</p></div>
    <div className="support-steps" aria-label="Quy trình"><span>01 · Chọn hồ sơ</span><ArrowRight size={16} /><span>02 · Kiểm tra bằng chứng</span><ArrowRight size={16} /><span>03 · Dự báo & gợi ý</span></div>
    {error && <p className="form-error" role="alert">{error}</p>}
    <section className="case-workspace no-print">
      <div className="case-picker"><label htmlFor="case-select">Hồ sơ để trình diễn</label><select id="case-select" value={selected} disabled={pending || !cases.length} onChange={(event) => { setSelected(event.target.value); setResult(null); setError('') }}>{cases.map((item) => <option key={item.id} value={item.id}>{item.title}</option>)}</select>
        {current && <><span className="status-chip cool">{current.source_kind === 'synthetic_test' ? 'Tình huống kiểm thử tổng hợp' : 'Trích rút dữ liệu train'}</span><h2>{current.title}</h2><p>{current.summary}</p><p className="evidence-caption">{current.source_notice}</p></>}
        <button type="button" className="button button-primary" disabled={!current || pending} onClick={analyze}>{pending ? 'Đang đối chiếu và dự báo…' : 'Phân tích hồ sơ'}<ArrowRight size={18} /></button>
        <a className="manual-link" href="#du-doan">Hoặc nhập dữ liệu của bạn →</a>
      </div>
      {current && <div className="case-evidence"><span className="eyebrow">DỮ LIỆU TẠI THỜI ĐIỂM QUAN SÁT</span><h2>{current.payload.features.code_module} · {current.payload.features.code_presentation}</h2>
        <div className="case-metrics"><div><strong>{current.payload.evidence.snapshot_day}</strong><span>ngày cutoff</span></div><div><strong>{current.payload.features.clicks_recent_7}</strong><span>click / 7 ngày</span></div><div><strong>{current.payload.features.clicks_recent_30}</strong><span>click / 30 ngày</span></div></div>
        <details><summary><FileCheck2 size={17} /> Xem từng bài đánh giá ({current.payload.evidence.assessments.length})</summary>
          <div className="evidence-table" role="region" aria-label="Chi tiết bài đánh giá" tabIndex="0"><table><thead><tr><th>Mã minh họa</th><th>Hạn ngày</th><th>Nộp ngày</th><th>Ghi chú</th></tr></thead><tbody>{current.payload.evidence.assessments.map((record) => <tr key={record.assessment_id}><td>{record.assessment_id}</td><td>{record.due_day ?? 'Chưa biết'}</td><td>{record.submitted_day ?? 'Chưa có bản ghi'}</td><td>{record.is_banked ? 'Bảo lưu' : record.due_day > current.payload.evidence.snapshot_day ? 'Hạn sau cutoff' : '—'}</td></tr>)}</tbody></table></div>
        </details><details><summary>Xem các số liệu đầu vào model</summary><dl className="feature-list">{Object.entries(current.payload.features).map(([name, value]) => <div key={name}><dt>{name}</dt><dd>{value ?? 'Thiếu dữ liệu'}</dd></div>)}</dl></details>
        <p className="evidence-caption"><Info size={15} /> Dữ liệu ví dụ đã được rút gọn; không có tên, mã sinh viên, điểm cuối kỳ hay nhãn nguy cơ thật.</p>
      </div>}
    </section>
    {result && <SupportResult key={selected + result.runtime_ms} result={result} />}
    {!result && !pending && <div className="support-placeholder"><ShieldNote />Chọn “Phân tích hồ sơ” để chạy model thật và xem gợi ý. Chưa có kết quả tính toán ở bước này.</div>}
  </div>
}

function ShieldNote() { return <FileCheck2 size={24} aria-hidden="true" /> }
