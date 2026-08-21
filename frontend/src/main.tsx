import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'

const API_BASE = (window as any).TamilDictConfig?.apiBase
  || import.meta.env.VITE_API_BASE
  || 'http://localhost:8000'

;(window as any).__TAMIL_DICT_API__ = API_BASE

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
