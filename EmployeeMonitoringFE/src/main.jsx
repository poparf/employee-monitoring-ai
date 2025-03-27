import { createRoot } from 'react-dom/client'
import './style/main.css'
import { UserProvider } from './context/UserContext.jsx'
import { App } from './App.jsx'
createRoot(document.getElementById('root')).render(
  <UserProvider>
    <App/>
  </UserProvider>
)
