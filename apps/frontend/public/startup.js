(() => {
  const status = document.getElementById('startup-status')
  const message = document.getElementById('startup-message')
  let failed = false
  const timeout = window.setTimeout(() => {
    if (!failed) message.textContent = 'Giao diện chưa tải xong. Nhấn Ctrl + Shift + R để tải lại. Nếu vẫn kẹt ở đây, chụp màn hình này để kiểm tra.'
  }, 15000)

  function showFailure(detail) {
    failed = true
    window.clearTimeout(timeout)
    status.hidden = false
    message.textContent = 'Không tải được giao diện: ' + detail + '. Bạn chụp lại thông báo này giúp mình nhé.'
  }

  window.addEventListener('error', (event) => {
    if (event.target?.tagName === 'SCRIPT') showFailure('tệp chương trình không tải được')
    else if (event.message) showFailure(event.message)
  }, true)
  window.addEventListener('unhandledrejection', (event) => {
    showFailure(event.reason?.message || 'lỗi khi tải hoặc chạy chương trình')
  })
  window.addEventListener('clht:ready', () => {
    window.clearTimeout(timeout)
    if (!failed) status.hidden = true
  }, { once: true })
})()
