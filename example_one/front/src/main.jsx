import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import NavigationBar from './NavigationBar.jsx'
import ChatBox from './ChatBox.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <NavigationBar/>
    <ChatBox/>
    {/* <App /> */}
  </StrictMode>,
)
