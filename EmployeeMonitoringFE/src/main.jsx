import { createRoot } from 'react-dom/client'
import Login from './components/login-component/step1-login-component.jsx'
import './style/main.css'
import { BrowserRouter, Routes, Route } from 'react-router'
import About from './components/about-component/About.jsx'


createRoot(document.getElementById('root')).render(
  <BrowserRouter>
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/about" element={<About/>} />
    </Routes>
  </BrowserRouter>,
)
