import { useState } from 'react'
import axios from 'axios'
import './Login.css'

interface Props { onLogin: (cliente: any) => void }

export default function Login({ onLogin }: Props) {
  const [login, setLogin] = useState('')
  const [senha, setSenha] = useState('')
  const [erro, setErro] = useState('')
  const [loading, setLoading] = useState(false)

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setErro('')
    try {
      const res = await axios.post('https://ubiquitous-doodle-px7prv6rvx627vrx-8000.app.github.dev/auth/login', { login, senha })
      onLogin(res.data.cliente)
    } catch { setErro('Login ou senha incorretos') }
    finally { setLoading(false) }
  }

  return (
    <div className="login-bg">
      <div className="login-left">
        <div className="login-brand">
          <div className="login-logo">LB</div>
          <h1 className="playfair">Lucas<span>Bank</span></h1>
          <p>O banco que entende o seu futuro financeiro</p>
        </div>
        <div className="deco-circle deco-1" />
        <div className="deco-circle deco-2" />
        <div className="deco-line" />
      </div>
      <div className="login-right">
        <form className="login-form" onSubmit={handleLogin}>
          <div className="login-form-header">
            <h2 className="playfair">Bem-vindo</h2>
            <p>Acesse sua conta LucasBank</p>
          </div>
          <div className="login-field">
            <label>Login</label>
            <input type="text" placeholder="seu login" value={login} onChange={e => setLogin(e.target.value)} required />
          </div>
          <div className="login-field">
            <label>Senha</label>
            <input type="password" placeholder="••••••••" value={senha} onChange={e => setSenha(e.target.value)} required />
          </div>
          {erro && <div className="login-erro">{erro}</div>}
          <button type="submit" className="login-btn" disabled={loading}>
            {loading ? 'Entrando...' : 'Acessar conta'}
          </button>
          <div className="login-hint">
            <span>Contas disponíveis:</span>
            <div className="login-accounts">
              {['lucas', 'ana', 'joao', 'yanne'].map(u => (
                <button key={u} type="button" className="account-chip"
                  onClick={() => { setLogin(u); setSenha(u) }}>{u}</button>
              ))}
            </div>
          </div>
        </form>
      </div>
    </div>
  )
}
