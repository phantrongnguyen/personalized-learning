import { useEffect, useRef, useState } from 'react'
import { ArrowLeft, ArrowRight, Check, CircleHelp, Clock3, RotateCcw, Sparkles } from 'lucide-react'
import { evaluateSupport } from '../../services/api.js'
import SupportResult from '../support/SupportResult.jsx'
import EvidenceEditor, { blankEvidence } from '../support/EvidenceEditor.jsx'

const sample = {
  code_module: 'BBB', code_presentation: '2014J', gender: 'F',
  highest_education: 'A Level or Equivalent', age_band: '0-35',
  studied_credits: 60, date_registration: -53, total_clicks_to_t: 807,
  clicks_resource_to_t: 23, clicks_url_to_t: 9, active_days_to_t: 52,
  assessments_due_to_t: 5, assessments_submitted_to_t: 5,
  late_submissions_to_t: 1, last_activity_day: 194,
  clicks_recent_7: 2, clicks_recent_30: 53,
}

const initial = Object.fromEntries(Object.keys(sample).map((key) => [key, '']))
Object.assign(initial, {
  code_module: 'BBB', code_presentation: '2014J', gender: 'F',
  highest_education: 'A Level or Equivalent', age_band: '0-35',
})

const education = [
  ['A Level or Equivalent', 'A Level hoặc tương đương'],
  ['Lower Than A Level', 'Dưới A Level'],
  ['HE Qualification', 'Trình độ đại học'],
  ['Post Graduate Qualification', 'Sau đại học'],
  ['No Formal quals', 'Chưa có bằng chính quy'],
]
const ageBands = [['0-35', 'Dưới 35'], ['35-55', '35–55'], ['55<=', 'Từ 55 trở lên']]

function Field({ label, name, value, onChange, helper, optional = false, min = 0, max, step = '1' }) {
  return <label className="field">
    <span className="field-label">{label}{optional && <small> · không bắt buộc</small>}</span>
    <input name={name} type="number" inputMode="decimal" value={value} onChange={onChange}
      min={min} max={max} step={step} required={!optional} placeholder="Nhập số" />
    {helper && <span className="field-help">{helper}</span>}
  </label>
}

function SelectField({ label, name, value, onChange, options, helper }) {
  return <label className="field"><span className="field-label">{label}</span>
    <select name={name} value={value} onChange={onChange} required>
      {options.map(([key, caption]) => <option value={key} key={key}>{caption}</option>)}
    </select>
    {helper && <span className="field-help">{helper}</span>}
  </label>
}


export default function Prediction({ catalog, model, selectedModule }) {
  const [form, setForm] = useState(initial)
  const [step, setStep] = useState(0)
  const [result, setResult] = useState(null)
  const [pending, setPending] = useState(false)
  const [error, setError] = useState('')
  const [evidence, setEvidence] = useState(blankEvidence)
  const formRef = useRef(null)
  const modules = [...new Set(catalog.map((course) => course.code_module))]
  const presentations = catalog.filter((course) => course.code_module === form.code_module)
  const chosenCourse = presentations.find((course) => course.code_presentation === form.code_presentation)

  useEffect(() => {
    if (!catalog.length) return
    setForm((previous) => {
      const available = catalog.filter((course) => course.code_module === selectedModule)
      if (!available.length || previous.code_module === selectedModule) return previous
      return { ...previous, code_module: selectedModule, code_presentation: available[0].code_presentation }
    })
  }, [catalog, selectedModule])

  function change(event) {
    const { name, value } = event.target
    if (name === 'code_module' || name === 'code_presentation') setEvidence(blankEvidence())
    setForm((previous) => ({
      ...previous,
      [name]: value,
      ...(name === 'code_module' ? {
        code_presentation: catalog.find((course) => course.code_module === value)?.code_presentation ?? '',
      } : {}),
    }))
  }

  function useSample() {
    setForm(sample)
    setEvidence({ ...blankEvidence(), enrollment_active: true, feature_data_confirmed: true, activity_complete: true })
    setStep(0)
    setResult(null)
    setError('')
  }

  function next(event) {
    event.preventDefault()
    if (formRef.current?.reportValidity()) {
      setStep((current) => current + 1)
      setError('')
      window.scrollTo({ top: 0, behavior: 'smooth' })
    }
  }

  async function submit(event) {
    event.preventDefault()
    if (!formRef.current?.reportValidity()) return
    setPending(true)
    setError('')
    try {
      const payload = Object.fromEntries(Object.entries(form).map(([key, value]) => {
        if (['code_module', 'code_presentation', 'gender', 'highest_education', 'age_band'].includes(key)) return [key, value]
        return [key, value === '' ? null : Number(value)]
      }))
      const records = evidence.assessments.map((record) => ({ ...record,
        due_day: record.due_day === '' ? null : Number(record.due_day),
        submitted_day: record.submitted_day === '' ? null : Number(record.submitted_day),
      }))
      setResult(await evaluateSupport({ features: payload, evidence: { ...evidence, snapshot_day: chosenCourse.cutoff_day, assessments: records } }))
      window.scrollTo({ top: 0, behavior: 'smooth' })
    } catch (failure) {
      setError(failure.message)
    } finally {
      setPending(false)
    }
  }

  return <div className="page-enter">
    <div className="inner-header"><span className="eyebrow">ĐÁNH GIÁ NGUY CƠ · CUTOFF 75%</span><h1>Học đến đâu, nhìn lại đến đó.</h1><p>Chỉ nhập dữ liệu đã có trước hoặc tại mốc 75% tiến trình học phần. Không cần tên hay mã sinh viên.</p></div>
    {result ? <><SupportResult result={result} /><button type="button" className="button button-outline" onClick={() => { setResult(null); setStep(0) }}><RotateCcw size={17} /> Điều chỉnh dữ liệu</button></> : <>
      <div className="assessment-grid">
        <section className="form-card">
          <div className="form-topline"><div><span className="eyebrow">THÔNG TIN ĐẦU VÀO</span><h2>{['Học phần & hồ sơ', 'Hoạt động học tập', 'Bài đánh giá'][step]}</h2></div><span className="step-number">0{step + 1} / 03</span></div>
          <div className="step-track" aria-label={`Bước ${step + 1} trên 3`}><span style={{ width: `${(step + 1) * 100 / 3}%` }} /></div>
          <form ref={formRef} onSubmit={submit} aria-busy={pending}><fieldset disabled={pending} className="form-fields-lock">
            {step === 0 && <div className="fields-grid">
              <SelectField name="code_module" label="Mã học phần" value={form.code_module} onChange={change}
                options={modules.map((code) => [code, `Học phần ${code}`])} helper="OULAD chỉ công bố mã, không có tên học phần." />
              <SelectField name="code_presentation" label="Kỳ học" value={form.code_presentation} onChange={change}
                options={presentations.map((course) => [course.code_presentation, course.code_presentation])} />
              <SelectField name="gender" label="Giới tính trong dữ liệu" value={form.gender} onChange={change}
                options={[["F", "Nữ (F)"], ["M", "Nam (M)"]]} />
              <SelectField name="age_band" label="Nhóm tuổi" value={form.age_band} onChange={change} options={ageBands} />
              <SelectField name="highest_education" label="Trình độ học vấn" value={form.highest_education} onChange={change} options={education} />
              <Field name="studied_credits" label="Số tín chỉ đang học" value={form.studied_credits} onChange={change} />
              <Field name="date_registration" label="Ngày đăng ký so với ngày mở môn" value={form.date_registration} onChange={change}
                min={-1000} max={1000} optional helper="Số âm là đăng ký trước ngày bắt đầu; để trống nếu không biết." />
            </div>}
            {step === 1 && <div className="fields-grid">
              <Field name="total_clicks_to_t" label="Tổng lượt click đến cutoff" value={form.total_clicks_to_t} onChange={change} />
              <Field name="clicks_resource_to_t" label="Click tài nguyên học tập" value={form.clicks_resource_to_t} onChange={change} />
              <Field name="clicks_url_to_t" label="Click liên kết" value={form.clicks_url_to_t} onChange={change} />
              <Field name="active_days_to_t" label="Số ngày có hoạt động" value={form.active_days_to_t} onChange={change} />
              <Field name="last_activity_day" label="Ngày hoạt động gần nhất" value={form.last_activity_day} onChange={change} min={-1000} optional helper="Ngày âm là trước ngày mở môn; chỉ để trống khi không có lịch sử click. Nếu chưa biết ngày cuối, cần xác minh trước khi chạy model." />
              <Field name="clicks_recent_7" label="Click trong 7 ngày gần cutoff" value={form.clicks_recent_7} onChange={change} />
              <Field name="clicks_recent_30" label="Click trong 30 ngày gần cutoff" value={form.clicks_recent_30} onChange={change} />
            </div>}
            {step === 2 && <div className="fields-grid">
              <Field name="assessments_due_to_t" label="Số bài đến hạn trước cutoff" value={form.assessments_due_to_t} onChange={change} />
              <Field name="assessments_submitted_to_t" label="Số bài đã nộp trước cutoff" value={form.assessments_submitted_to_t} onChange={change} />
              <Field name="late_submissions_to_t" label="Số bài nộp trễ" value={form.late_submissions_to_t} onChange={change} />
              <div className="derived-note"><Sparkles size={18} /><span>App tự tính tỷ lệ ngày hoạt động, tỷ lệ nộp bài và số ngày từ lần hoạt động cuối. Bạn không cần nhập lại.</span></div>
            </div>}
            {step === 2 && <EvidenceEditor value={evidence} onChange={setEvidence} cutoffDay={chosenCourse?.cutoff_day} />}
            {error && <p className="form-error" role="alert">{error}</p>}
            <div className="form-actions">
              {step > 0 ? <button type="button" className="button button-quiet" onClick={() => { setStep(step - 1); setError('') }}><ArrowLeft size={17} /> Quay lại</button> : <button type="button" className="text-button" onClick={useSample}><Sparkles size={16} /> Điền ví dụ tổng hợp</button>}
              {step < 2 ? <button key="next" type="button" className="button button-primary" onClick={next}>Tiếp tục <ArrowRight size={18} /></button>
                : <button key="submit" type="submit" className="button button-primary" disabled={pending || !catalog.length}>{pending ? 'Đang tính...' : 'Xem kết quả'} <ArrowRight size={18} /></button>}
            </div>
          </fieldset></form>
        </section>
        <aside className="form-aside">
          <div className="aside-card blue-card"><Clock3 size={24} /><span className="eyebrow">THỜI ĐIỂM QUAN SÁT</span><strong>{chosenCourse ? `Ngày ${chosenCourse.cutoff_day}` : '75%'}</strong><p>{chosenCourse ? `75% của ${chosenCourse.module_presentation_length} ngày ở ${form.code_module} · ${form.code_presentation}.` : 'Chọn học phần và kỳ học để xác định cutoff.'}</p><div className="mini-progress"><i /></div></div>
          <div className="aside-card"><CircleHelp size={23} className="aside-icon" /><h3>Phạm vi dữ liệu đầu vào</h3><p>Chỉ tính bài nộp và tương tác diễn ra đến ngày cutoff. Kết quả cuối môn và hoạt động sau cutoff không được đưa vào model.</p></div>
          <div className="aside-card quiet-aside"><Check size={18} /> Ví dụ tổng hợp để thử giao diện, đã điều chỉnh cho nhất quán về thời gian; không phải hồ sơ một sinh viên thật.</div>
        </aside>
      </div>
    </>}
  </div>
}
