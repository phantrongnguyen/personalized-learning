async function request(path, options = {}) {
  const response = await fetch(`/api/v1/${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  const content = await response.json().catch(() => ({}))
  if (!response.ok) {
    const detail = content.detail
    const message = typeof detail === 'string'
      ? detail
      : Array.isArray(detail)
        ? detail.map((item) => item.msg.replace(/^Value error, /, '')).join(' · ')
        : 'Không thể kết nối dịch vụ dự đoán.'
    throw new Error(message)
  }
  return content
}

export const getCatalog = () => request('catalog')
export const getModel = () => request('model')
export const getSupportCases = () => request('support/cases')
export const evaluateCase = (caseId) => request('support/cases/' + encodeURIComponent(caseId), { method: 'POST' })
export const evaluateSupport = (payload) => request('support', { method: 'POST', body: JSON.stringify(payload) })
export const predict = (payload) => request('predict', {
  method: 'POST',
  body: JSON.stringify(payload),
})
