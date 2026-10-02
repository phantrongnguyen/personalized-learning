import { Component, useEffect } from 'react'

export function AppReady() {
  useEffect(() => { window.dispatchEvent(new Event('clht:ready')) }, [])
  return null
}

export default class AppBoundary extends Component {
  state = { error: null }

  static getDerivedStateFromError(error) {
    return { error }
  }

  render() {
    if (this.state.error) {
      return <section role="alert" style={{ maxWidth: 640, margin: '64px auto', padding: 24, fontFamily: 'system-ui' }}>
        <h1>Giao diện gặp lỗi</h1>
        <p>Bạn chụp lại thông báo bên dưới để mình kiểm tra nhé. Không cần chạy lại model.</p>
        <pre style={{ whiteSpace: 'pre-wrap' }}>{this.state.error.message || 'Không thể hiển thị trang.'}</pre>
        <button type="button" onClick={() => window.location.reload()}>Tải lại trang</button>
      </section>
    }
    return this.props.children
  }
}
