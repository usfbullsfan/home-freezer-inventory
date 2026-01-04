import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import { updateManifest } from './utils/manifestUpdater'

// Update PWA manifest based on environment (dev vs prod)
updateManifest()

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
