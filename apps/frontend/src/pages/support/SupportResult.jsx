import { useState } from 'react'
import { CheckCircle2, Download, Info, ShieldCheck } from 'lucide-react'
import { supportReport } from '../../services/support-report.js'

export default function SupportResult({ result }) {
  const [expanded, setExpanded] = useState(false)
  const prediction = result.prediction
  const summary = result.assessment_summary
  const visible = expanded ? result.suggestions : result.suggestions.slice(0, 2)

  function download() {
    const url = URL.createObjectURL(new Blob([supportReport(result)], { type: 'text/markdown;charset=utf-8' }))
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = 'Phieu_du_bao_va_goi_y.md'
    anchor.click()
    setTimeout(() => URL.revokeObjectURL(url), 1000)
  }

  return <section className="support-result page-enter" aria-live="polite" aria-label="Kết quả dự báo và gợi ý">
    <div className="section-title"><div><span className="eyebrow">KẾT QUẢ TẠI NGÀY {result.cutoff_day}</span><h2>Kết quả dự báo và gợi ý</h2></div>
      <button type="button" className="button button-outline no-print" onClick={download}><Download size={17} /> Tải phiếu kết quả</button></div>
    <div className="support-risk">
      <div className="support-risk-number"><span>Dự báo nguy cơ</span><strong>{prediction ? (prediction.probability_risk * 100).toLocaleString('vi-VN', { maximumFractionDigits: 1 }) + '%' : 'Chưa chạy'}</strong><small>HCO–VNLS + LightGBM · cutoff 75%</small></div>
      <div><h3>{prediction ? (prediction.above_threshold ? 'Trên ngưỡng tham khảo' : 'Dưới ngưỡng tham khảo') : 'Cần xác nhận dữ liệu trước'}</h3>
        <p>{prediction ? 'Ước lượng khả năng thuộc nhóm Fail/Withdrawn, không phải điểm số hoặc kết luận học vụ. Ngưỡng demo: ' + (prediction.threshold * 100) + '%.' : 'Không suy đoán xác suất khi chưa xác nhận nguồn đặc trưng hoặc tình trạng theo học.'}</p>
        <p className="muted-small">Nguy cơ thấp vẫn có thể có bài cần kiểm tra. Các gợi ý bên dưới dựa vào bằng chứng, không cần vượt ngưỡng dự báo.</p></div>
    </div>
    {summary && <div className="support-facts" aria-label="Bài nộp đã đối chiếu theo mã">
      <div><strong>{summary.due}</strong><span>bài đến hạn</span></div>
      <div><strong>{summary.completed_due}</strong><span>bài đến hạn có bản ghi</span></div>
      <div><strong>{summary.missing}</strong><span>bài cần kiểm tra</span></div>
      <div><strong>{summary.early_future}</strong><span>bài nộp sớm, hạn sau cutoff</span></div>
    </div>}
    {summary && <p className="evidence-caption">Đối chiếu từng mã bài, không lấy tổng bài đã nộp để bù bài còn thiếu. Bài thiếu hạn hoặc được miễn có trạng thái riêng.</p>}
    <div className="section-title"><div><span className="eyebrow">GỢI Ý VÀ CĂN CỨ</span><h2>{result.suggestions.length ? 'Hành động đề xuất' : 'Chưa có gợi ý cụ thể'}</h2></div><span className="status-chip cool">{result.suggestions.length} tình huống khớp</span></div>
    {!result.suggestions.length && <div className="support-empty"><ShieldCheck size={26} /><div><h3>Chưa đủ căn cứ để đưa ra gợi ý.</h3><p>Điều này không đồng nghĩa người học chắc chắn không gặp khó khăn. Xem trạng thái dữ liệu bên dưới.</p></div></div>}
    <div className="suggestion-list">{visible.map((suggestion) => <article className="suggestion-card" key={suggestion.rule_id}>
      <div className="suggestion-heading"><span className="rule-badge">{suggestion.rule_id}</span><h3>{suggestion.title}</h3><CheckCircle2 size={20} aria-hidden="true" /></div>
      <p className="suggestion-observation">{suggestion.observation}</p>
      <div className="suggestion-action"><strong>Bước có thể làm</strong><p>{suggestion.action}</p></div>
      <details open><summary>Căn cứ của gợi ý</summary><ul>{suggestion.evidence.map((item) => <li key={item}>{item}</li>)}</ul></details>
      <p className="suggestion-limit"><Info size={16} aria-hidden="true" /><span>{suggestion.limitation}</span></p>
    </article>)}</div>
    {result.suggestions.length > 2 && <button className="button button-outline no-print" type="button" onClick={() => setExpanded(!expanded)}>{expanded ? 'Thu gọn' : 'Xem thêm tín hiệu (' + (result.suggestions.length - 2) + ')'}</button>}
    <div className="support-quality"><h3>Lưu ý khi diễn giải kết quả</h3><ul>{result.warnings.map((warning) => <li key={warning}>{warning}</li>)}<li>{result.notice}</li></ul>
      <p>{result.course} · Ngày {result.cutoff_day} · Quy tắc {result.rule_version} · Thời gian xử lý lần này: {result.runtime_ms} ms (không phải benchmark).</p>
      {result.source_notice && <p>{result.source_notice}</p>}</div>
  </section>
}
