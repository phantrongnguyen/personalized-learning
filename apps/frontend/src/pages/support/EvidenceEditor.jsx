import { Plus, Trash2 } from 'lucide-react'

export function blankEvidence() {
  return { enrollment_active: null, feature_data_confirmed: false, activity_complete: false,
    assessments_complete: false, assessments: [] }
}

export default function EvidenceEditor({ value, onChange, cutoffDay }) {
  function update(name, next) { onChange({ ...value, [name]: next }) }
  function updateRecord(index, name, next) {
    update('assessments', value.assessments.map((record, current) => current === index ? { ...record, [name]: next } : record))
  }
  function addRecord() {
    let identifier = value.assessments.length + 1
    while (value.assessments.some((record) => record.assessment_id === 'M' + identifier)) identifier += 1
    update('assessments', [...value.assessments, { assessment_id: 'M' + identifier, due_day: '', submitted_day: '', is_banked: false, is_exempt: false }])
  }
  return <section className="evidence-editor">
    <h3>Xác nhận bằng chứng tại ngày {cutoffDay}</h3>
    <p>Không điền thay những gì bạn chưa biết. Dự báo dùng số tổng hợp; lời khuyên về bài nộp cần đối chiếu từng mã bài.</p>
    <label className="field"><span className="field-label">Tình trạng theo học tại cutoff</span><select value={value.enrollment_active === null ? 'unknown' : String(value.enrollment_active)} onChange={(event) => update('enrollment_active', event.target.value === 'unknown' ? null : event.target.value === 'true')}><option value="unknown">Chưa xác nhận</option><option value="true">Còn theo học</option><option value="false">Đã rút / không còn theo học</option></select></label>
    <label className="evidence-check"><input type="checkbox" checked={value.feature_data_confirmed} onChange={(event) => update('feature_data_confirmed', event.target.checked)} /><span>Tôi xác nhận các số tổng hợp chỉ dùng dữ liệu đã biết đến cutoff, đúng định nghĩa model.</span></label>
    <label className="evidence-check"><input type="checkbox" checked={value.activity_complete} onChange={(event) => update('activity_complete', event.target.checked)} /><span>Log tương tác đã được kiểm tra đầy đủ đến cutoff; số 0 không phải do thiếu dữ liệu.</span></label>
    <details><summary>Bổ sung từng bài để nhận gợi ý về tiến độ</summary>
      <p>Nhập cả bài có hạn sau cutoff nếu đã biết trong lịch. Chỉ ghi ngày nộp đã xảy ra, không nhập điểm. Mã bài chỉ cần phân biệt trong hồ sơ này.</p>
      {value.assessments.map((record, index) => <div className="assessment-record" key={record.assessment_id}>
        <strong>{record.assessment_id}</strong>
        <label>Hạn ngày<input type="number" min="-1000" max="2000" value={record.due_day} placeholder="Chưa biết" onChange={(event) => updateRecord(index, 'due_day', event.target.value)} /></label>
        <label>Nộp ngày<input type="number" min="-1000" max={cutoffDay} value={record.submitted_day} placeholder="Chưa ghi nhận" onChange={(event) => updateRecord(index, 'submitted_day', event.target.value)} /></label>
        <label className="evidence-check"><input type="checkbox" checked={record.is_banked} onChange={(event) => updateRecord(index, 'is_banked', event.target.checked)} />Bảo lưu</label>
        <label className="evidence-check"><input type="checkbox" checked={record.is_exempt} onChange={(event) => updateRecord(index, 'is_exempt', event.target.checked)} />Miễn bài</label>
        <button type="button" className="button button-quiet" aria-label={'Bỏ bài ' + record.assessment_id} onClick={() => update('assessments', value.assessments.filter((item, current) => current !== index))}><Trash2 size={17} /></button>
      </div>)}
      <button type="button" className="button button-outline" onClick={addRecord} disabled={value.assessments.length >= 200}><Plus size={17} /> Thêm bài</button>
      <label className="evidence-check"><input type="checkbox" checked={value.assessments_complete} onChange={(event) => update('assessments_complete', event.target.checked)} /><span>Danh sách trên đầy đủ cho học phần/kỳ; ngày nộp chỉ tính đến cutoff. Tôi đã kiểm tra trường hợp bảo lưu và miễn bài.</span></label>
    </details>
  </section>
}
