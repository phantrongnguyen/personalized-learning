import assert from 'node:assert/strict'
import { after, before, test } from 'node:test'
import { readFile } from 'node:fs/promises'
import { runInNewContext } from 'node:vm'
import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { createServer } from 'vite'
import { supportReport } from '../src/services/support-report.js'

let server
let SupportResult
let EvidenceEditor
let Prediction
let App
let AppBoundary
const samples = JSON.parse(await readFile(new URL('../../research_outputs/ket_qua_demo.json', import.meta.url), 'utf8'))

before(async () => {
  server = await createServer({ cacheDir: 'node_modules/.cache/clht-tests', server: { middlewareMode: true, hmr: false, watch: null }, appType: 'custom' })
  SupportResult = (await server.ssrLoadModule('/src/pages/support/SupportResult.jsx')).default
  EvidenceEditor = (await server.ssrLoadModule('/src/pages/support/EvidenceEditor.jsx')).default
  Prediction = (await server.ssrLoadModule('/src/pages/prediction/Prediction.jsx')).default
  App = (await server.ssrLoadModule('/src/App.jsx')).default
  AppBoundary = (await server.ssrLoadModule('/src/AppBoundary.jsx')).default
})
after(async () => { if (server) await server.close() })

test('all entry routes render the application shell', () => {
  const previousWindow = globalThis.window
  try {
    for (const hash of ['#goi-y', '#tong-quan', '#du-doan', '#phuong-phap']) {
      globalThis.window = { location: { hash } }
      const html = renderToStaticMarkup(createElement(App))
      assert.ok(html.includes('Góc học tập'))
      assert.ok(html.includes('main-content'))
      assert.ok(!html.includes('App này đang dùng gì?'))
      assert.ok(!html.includes('Mỗi lời khuyên đều có căn cứ.'))
    }
  } finally {
    if (previousWindow === undefined) delete globalThis.window
    else globalThis.window = previousWindow
  }
})

test('render failure provides readable, escaped recovery instructions', () => {
  const boundary = new AppBoundary({})
  boundary.state = AppBoundary.getDerivedStateFromError(new Error('<script>bad</script>'))
  const html = renderToStaticMarkup(boundary.render())
  assert.ok(html.includes('Giao diện gặp lỗi'))
  assert.ok(html.includes('Tải lại trang'))
  assert.ok(!html.includes('<script>bad</script>'))
})

test('startup status handles ready, delayed loading and script errors', async () => {
  const source = await readFile(new URL('../public/startup.js', import.meta.url), 'utf8')
  const status = { hidden: false }
  const message = { textContent: '' }
  const handlers = {}
  let onTimeout
  runInNewContext(source, {
    document: { getElementById: (id) => id === 'startup-status' ? status : message },
    window: {
      setTimeout(callback) { onTimeout = callback; return 1 },
      clearTimeout() {},
      addEventListener(name, callback) { handlers[name] = callback },
    },
  })
  onTimeout()
  assert.ok(message.textContent.includes('chưa tải xong'))
  handlers['clht:ready']()
  assert.equal(status.hidden, true)
  handlers.error({ target: { tagName: 'SCRIPT' } })
  assert.equal(status.hidden, false)
  assert.ok(message.textContent.includes('tệp chương trình không tải được'))
  handlers.unhandledrejection({ reason: new Error('module unavailable') })
  assert.ok(message.textContent.includes('module unavailable'))
  handlers['clht:ready']()
  assert.equal(status.hidden, false)
})

test('all seven API outputs render without claiming score improvement', () => {
  for (const result of samples) {
    const html = renderToStaticMarkup(createElement(SupportResult, { result }))
    assert.ok(html.includes('Kết quả dự báo và gợi ý'))
    assert.ok(html.includes('chưa được chứng minh làm tăng điểm'))
    assert.ok(html.includes('Tải phiếu kết quả'))
  }
})

test('missing-data result is not rendered as a zero-percent prediction', () => {
  const result = samples.find((item) => item.case_id === 'thieu-bang-chung')
  const html = renderToStaticMarkup(createElement(SupportResult, { result }))
  assert.ok(html.includes('Chưa chạy'))
  assert.ok(!html.includes('<strong>0%'))
  assert.ok(html.includes('Chưa đủ căn cứ'))
})

test('actual early-submission example shows evidence despite low predicted risk', () => {
  const result = samples.find((item) => item.case_id === 'nop-som')
  assert.ok(result.prediction.probability_risk < .5)
  const html = renderToStaticMarkup(createElement(SupportResult, { result }))
  assert.ok(html.includes('G01'))
  assert.ok(html.includes('bài nộp sớm, hạn sau cutoff'))
  assert.ok(html.includes('Căn cứ của gợi ý'))
})

test('downloaded report includes rules, limitations and true abstention state', () => {
  for (const result of samples) {
    const report = supportReport(result)
    assert.ok(report.startsWith('# Phiếu dự báo'))
    assert.ok(report.includes(result.notice))
    for (const item of result.suggestions) assert.ok(report.includes(item.rule_id))
    if (!result.prediction) assert.ok(report.includes('Chưa chạy model'))
    assert.ok(!report.includes('id_student'))
  }
})

test('manual evidence starts unconfirmed with no fabricated records', () => {
  const value = { enrollment_active: null, feature_data_confirmed: false, activity_complete: false, assessments_complete: false, assessments: [] }
  const html = renderToStaticMarkup(createElement(EvidenceEditor, { value, onChange() {}, cutoffDay: 196 }))
  assert.ok(html.includes('Chưa xác nhận'))
  assert.ok(!html.includes('checked=""'))
})

test('manual entry still renders the original three-step form', () => {
  const catalog = [{ code_module: 'BBB', code_presentation: '2014J', cutoff_day: 196, module_presentation_length: 262 }]
  const html = renderToStaticMarkup(createElement(Prediction, { catalog, model: null, selectedModule: 'BBB' }))
  assert.ok(html.includes('Học phần &amp; hồ sơ'))
  assert.ok(html.includes('form-fields-lock'))
})

test('evidence is escaped when rendered, never inserted as HTML', () => {
  const result = structuredClone(samples[0])
  result.suggestions[0].observation = '<script>alert(1)</script>'
  const html = renderToStaticMarkup(createElement(SupportResult, { result }))
  assert.ok(!html.includes('<script>alert(1)</script>'))
  assert.ok(html.includes('&lt;script&gt;'))
})
