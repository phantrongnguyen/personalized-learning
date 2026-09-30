import React from 'react'
import { createRoot } from 'react-dom/client'
import App from './App.jsx'
import AppBoundary, { AppReady } from './AppBoundary.jsx'
import './styles/app.css'
import './styles/details.css'
import './styles/responsive.css'
import './styles/support.css'

createRoot(document.getElementById('root')).render(
  <React.StrictMode><AppBoundary><App /><AppReady /></AppBoundary></React.StrictMode>,
)
