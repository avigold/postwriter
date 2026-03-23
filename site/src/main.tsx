import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import Reader from './Reader.tsx'

const isReader = window.location.pathname === '/read'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    {isReader ? <Reader /> : <App />}
  </StrictMode>,
)
