import { useState } from 'react'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import './index.css'

export default function App() {
  const [cliente, setCliente] = useState<any>(null)
  return cliente
    ? <Dashboard cliente={cliente} onLogout={() => setCliente(null)} />
    : <Login onLogin={setCliente} />
}
