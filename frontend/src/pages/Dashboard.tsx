import { useState, useEffect } from 'react'
import axios from 'axios'
import './Dashboard.css'

const API = 'https://ubiquitous-doodle-px7prv6rvx627vrx-8000.app.github.dev'
const formatBRL = (v: number) => v.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })

const tipoIcon: Record<string, string> = {
  deposito: '↓', saque: '↑', transferencia_enviada: '→',
  transferencia_recebida: '←', investimento_aporte: '📈', investimento_resgate: '💰',
}

const tipoLabel: Record<string, string> = {
  deposito: 'Depósito', saque: 'Saque',
  transferencia_enviada: 'Transferência enviada', transferencia_recebida: 'Transferência recebida',
  investimento_aporte: 'Aporte', investimento_resgate: 'Resgate',
}

const isPositivo = (tipo: string) => ['deposito', 'transferencia_recebida', 'investimento_resgate'].includes(tipo)

export default function Dashboard({ cliente: ci, onLogout }: { cliente: any, onLogout: () => void }) {
  const [cliente, setCliente] = useState(ci)
  const [aba, setAba] = useState('inicio')
  const [transacoes, setTransacoes] = useState<any[]>([])
  const [investimentos, setInvestimentos] = useState<any[]>([])
  const [clientes, setClientes] = useState<any[]>([])
  const [valor, setValor] = useState('')
  const [descricao, setDescricao] = useState('')
  const [destinatario, setDestinatario] = useState('')
  const [tipoInv, setTipoInv] = useState('CDB')
  const [msg, setMsg] = useState<{ texto: string, tipo: 'success' | 'error' } | null>(null)
  const [loading, setLoading] = useState(false)

  const refresh = async () => {
    const [c, t, i] = await Promise.all([
      axios.get(`${API}/clientes/${cliente.id}`),
      axios.get(`${API}/clientes/${cliente.id}/extrato`),
      axios.get(`${API}/investimentos/${cliente.id}`),
    ])
    setCliente(c.data)
    setTransacoes(t.data.transacoes)
    setInvestimentos(i.data.investimentos)
  }

  useEffect(() => { refresh() }, [])
  useEffect(() => {
    axios.get(`${API}/clientes`).then(r => setClientes(r.data.clientes.filter((c: any) => c.id !== cliente.id)))
  }, [])

  const showMsg = (texto: string, tipo: 'success' | 'error') => {
    setMsg({ texto, tipo })
    setTimeout(() => setMsg(null), 3000)
  }

  const act = async (fn: () => Promise<any>) => {
    setLoading(true)
    try { await fn(); await refresh() }
    catch (e: any) { showMsg(e.response?.data?.detail || 'Erro ao processar', 'error') }
    finally { setLoading(false) }
  }

  const handleDeposito = () => act(async () => {
    await axios.post(`${API}/transacoes/depositar`, { cliente_id: cliente.id, valor: parseFloat(valor), descricao })
    showMsg('Depósito realizado!', 'success'); setValor(''); setDescricao('')
  })

  const handleSaque = () => act(async () => {
    await axios.post(`${API}/transacoes/sacar`, { cliente_id: cliente.id, valor: parseFloat(valor), descricao })
    showMsg('Saque realizado!', 'success'); setValor(''); setDescricao('')
  })

  const handleTransferencia = () => act(async () => {
    await axios.post(`${API}/transacoes/transferir`, { remetente_id: cliente.id, destinatario_id: parseInt(destinatario), valor: parseFloat(valor), descricao })
    showMsg('Transferência realizada!', 'success'); setValor(''); setDescricao(''); setDestinatario('')
  })

  const handleAporte = () => act(async () => {
    await axios.post(`${API}/investimentos/aportar`, { cliente_id: cliente.id, tipo: tipoInv, valor: parseFloat(valor) })
    showMsg('Aporte realizado!', 'success'); setValor('')
  })

  const handleResgate = (id: number) => act(async () => {
    await axios.post(`${API}/investimentos/resgatar/${id}`)
    showMsg('Resgate realizado!', 'success')
  })

  const totalInvestido = investimentos.reduce((acc, i) => acc + i.valor, 0)

  const navItems = [
    { id: 'inicio', label: 'Início', icon: '◉' },
    { id: 'deposito', label: 'Depositar', icon: '↓' },
    { id: 'saque', label: 'Sacar', icon: '↑' },
    { id: 'transferencia', label: 'Transferir', icon: '→' },
    { id: 'investimentos', label: 'Investimentos', icon: '📈' },
    { id: 'extrato', label: 'Extrato', icon: '≡' },
  ]

  return (
    <div className="dash">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="sidebar-logo">LB</div>
          <span className="playfair">LucasBank</span>
        </div>
        <nav className="sidebar-nav">
          {navItems.map(item => (
            <button key={item.id} className={`nav-item ${aba === item.id ? 'active' : ''}`} onClick={() => setAba(item.id)}>
              <span className="nav-icon">{item.icon}</span>
              <span>{item.label}</span>
            </button>
          ))}
        </nav>
        <button className="logout-btn" onClick={onLogout}>Sair</button>
      </aside>

      <main className="main">
        {msg && <div className={`toast toast-${msg.tipo}`}>{msg.texto}</div>}

        {aba === 'inicio' && (
          <div className="page">
            <div className="page-header">
              <p className="greeting">Bem-vindo,</p>
              <h1 className="playfair">{cliente.nome}</h1>
              <p className="client-id">ID do cliente: #{cliente.id}</p>
            </div>
            <div className="saldo-card">
              <div className="saldo-label">Saldo disponível</div>
              <div className="saldo-valor playfair">{formatBRL(cliente.saldo)}</div>
              <div className="saldo-decoration" />
            </div>
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-label">Total investido</div>
                <div className="stat-valor">{formatBRL(totalInvestido)}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Investimentos ativos</div>
                <div className="stat-valor">{investimentos.length}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Transações</div>
                <div className="stat-valor">{transacoes.length}</div>
              </div>
            </div>
            <div className="recent-section">
              <h3 className="section-title">Últimas movimentações</h3>
              <div className="transacoes-list">
                {transacoes.slice(0, 5).map(t => (
                  <div key={t.id} className="transacao-item">
                    <div className={`transacao-icon ${isPositivo(t.tipo) ? 'positive' : 'negative'}`}>{tipoIcon[t.tipo] || '•'}</div>
                    <div className="transacao-info">
                      <div className="transacao-desc">{t.descricao}</div>
                      <div className="transacao-tipo">{tipoLabel[t.tipo]}</div>
                    </div>
                    <div className={`transacao-valor ${isPositivo(t.tipo) ? 'positive' : 'negative'}`}>
                      {isPositivo(t.tipo) ? '+' : '-'}{formatBRL(t.valor)}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {(aba === 'deposito' || aba === 'saque') && (
          <div className="page">
            <div className="page-header">
              <h1 className="playfair">{aba === 'deposito' ? 'Depositar' : 'Sacar'}</h1>
            </div>
            <div className="form-card">
              <div className="form-field">
                <label>Valor</label>
                <div className="input-prefix">
                  <span>R$</span>
                  <input type="number" placeholder="0,00" value={valor} onChange={e => setValor(e.target.value)} min="0" step="0.01" />
                </div>
              </div>
              <div className="form-field">
                <label>Descrição (opcional)</label>
                <input type="text" placeholder="Ex: Salário..." value={descricao} onChange={e => setDescricao(e.target.value)} />
              </div>
              <div className="saldo-atual">Saldo atual: <strong>{formatBRL(cliente.saldo)}</strong></div>
              <button className="action-btn" disabled={!valor || loading} onClick={aba === 'deposito' ? handleDeposito : handleSaque}>
                {loading ? 'Processando...' : aba === 'deposito' ? 'Confirmar depósito' : 'Confirmar saque'}
              </button>
            </div>
          </div>
        )}

        {aba === 'transferencia' && (
          <div className="page">
            <div className="page-header"><h1 className="playfair">Transferir</h1></div>
            <div className="form-card">
              <div className="form-field">
                <label>Destinatário</label>
                <select value={destinatario} onChange={e => setDestinatario(e.target.value)}>
                  <option value="">Selecione o destinatário</option>
                  {clientes.map(c => <option key={c.id} value={c.id}>{c.nome} (#{c.id})</option>)}
                </select>
              </div>
              <div className="form-field">
                <label>Valor</label>
                <div className="input-prefix">
                  <span>R$</span>
                  <input type="number" placeholder="0,00" value={valor} onChange={e => setValor(e.target.value)} min="0" step="0.01" />
                </div>
              </div>
              <div className="form-field">
                <label>Descrição (opcional)</label>
                <input type="text" placeholder="Ex: Aluguel..." value={descricao} onChange={e => setDescricao(e.target.value)} />
              </div>
              <div className="saldo-atual">Saldo atual: <strong>{formatBRL(cliente.saldo)}</strong></div>
              <button className="action-btn" disabled={!valor || !destinatario || loading} onClick={handleTransferencia}>
                {loading ? 'Processando...' : 'Confirmar transferência'}
              </button>
            </div>
          </div>
        )}

        {aba === 'investimentos' && (
          <div className="page">
            <div className="page-header"><h1 className="playfair">Investimentos</h1></div>
            <div className="form-card">
              <h3 className="form-section-title">Novo aporte</h3>
              <div className="form-field">
                <label>Tipo de investimento</label>
                <div className="inv-tipos">
                  {['CDB', 'LCI', 'LCA', 'Tesouro Direto', 'Fundos'].map(t => (
                    <button key={t} className={`tipo-chip ${tipoInv === t ? 'active' : ''}`} onClick={() => setTipoInv(t)}>{t}</button>
                  ))}
                </div>
              </div>
              <div className="form-field">
                <label>Valor do aporte</label>
                <div className="input-prefix">
                  <span>R$</span>
                  <input type="number" placeholder="0,00" value={valor} onChange={e => setValor(e.target.value)} min="0" step="0.01" />
                </div>
              </div>
              <button className="action-btn" disabled={!valor || loading} onClick={handleAporte}>
                {loading ? 'Processando...' : 'Realizar aporte'}
              </button>
            </div>
            {investimentos.length > 0 && (
              <div className="inv-lista">
                <h3 className="section-title">Investimentos ativos</h3>
                {investimentos.map(inv => (
                  <div key={inv.id} className="inv-item">
                    <div className="inv-info">
                      <div className="inv-tipo">{inv.tipo}</div>
                      <div className="inv-valor">{formatBRL(inv.valor)}</div>
                    </div>
                    <button className="resgatar-btn" onClick={() => handleResgate(inv.id)} disabled={loading}>Resgatar</button>
                  </div>
                ))}
                <div className="inv-total">Total investido: <strong>{formatBRL(totalInvestido)}</strong></div>
              </div>
            )}
          </div>
        )}

        {aba === 'extrato' && (
          <div className="page">
            <div className="page-header"><h1 className="playfair">Extrato</h1></div>
            <div className="transacoes-list full">
              {transacoes.length === 0
                ? <div className="empty-state">Nenhuma transação encontrada</div>
                : transacoes.map(t => (
                  <div key={t.id} className="transacao-item">
                    <div className={`transacao-icon ${isPositivo(t.tipo) ? 'positive' : 'negative'}`}>{tipoIcon[t.tipo] || '•'}</div>
                    <div className="transacao-info">
                      <div className="transacao-desc">{t.descricao}</div>
                      <div className="transacao-tipo">{tipoLabel[t.tipo]} • Saldo: {formatBRL(t.saldo_posterior)}</div>
                    </div>
                    <div className={`transacao-valor ${isPositivo(t.tipo) ? 'positive' : 'negative'}`}>
                      {isPositivo(t.tipo) ? '+' : '-'}{formatBRL(t.valor)}
                    </div>
                  </div>
                ))}
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
