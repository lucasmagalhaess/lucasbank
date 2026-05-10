from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .database import get_connection
from datetime import datetime

app = FastAPI(title="LucasBank API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class LoginRequest(BaseModel):
    login: str
    senha: str

class TransacaoRequest(BaseModel):
    cliente_id: int
    valor: float
    descricao: str = ""

class TransferenciaRequest(BaseModel):
    remetente_id: int
    destinatario_id: int
    valor: float
    descricao: str = ""

class InvestimentoRequest(BaseModel):
    cliente_id: int
    tipo: str
    valor: float

@app.post("/auth/login")
def login(req: LoginRequest):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, nome, login, saldo FROM clientes WHERE login=%s AND senha=%s", (req.login, req.senha))
    cliente = cur.fetchone()
    conn.close()
    if not cliente:
        raise HTTPException(status_code=401, detail="Login ou senha incorretos")
    return {"success": True, "cliente": dict(cliente)}

@app.get("/clientes/{cliente_id}")
def get_cliente(cliente_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, nome, login, saldo FROM clientes WHERE id=%s", (cliente_id,))
    cliente = cur.fetchone()
    conn.close()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return dict(cliente)

@app.get("/clientes/{cliente_id}/extrato")
def get_extrato(cliente_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, tipo, valor, descricao, saldo_anterior, saldo_posterior, criado_em
        FROM transacoes WHERE cliente_id=%s
        ORDER BY criado_em DESC LIMIT 50
    """, (cliente_id,))
    transacoes = [dict(t) for t in cur.fetchall()]
    conn.close()
    return {"transacoes": transacoes}

@app.post("/transacoes/depositar")
def depositar(req: TransacaoRequest):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT saldo FROM clientes WHERE id=%s", (req.cliente_id,))
    cliente = cur.fetchone()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    saldo_anterior = float(cliente["saldo"])
    saldo_posterior = saldo_anterior + req.valor
    cur.execute("UPDATE clientes SET saldo=%s WHERE id=%s", (saldo_posterior, req.cliente_id))
    cur.execute("""
        INSERT INTO transacoes (cliente_id, tipo, valor, descricao, saldo_anterior, saldo_posterior)
        VALUES (%s, 'deposito', %s, %s, %s, %s)
    """, (req.cliente_id, req.valor, req.descricao or "Depósito", saldo_anterior, saldo_posterior))
    conn.commit()
    conn.close()
    return {"success": True, "saldo_anterior": saldo_anterior, "saldo_posterior": saldo_posterior}

@app.post("/transacoes/sacar")
def sacar(req: TransacaoRequest):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT saldo FROM clientes WHERE id=%s", (req.cliente_id,))
    cliente = cur.fetchone()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    saldo_anterior = float(cliente["saldo"])
    if req.valor > saldo_anterior:
        raise HTTPException(status_code=400, detail="Saldo insuficiente")
    saldo_posterior = saldo_anterior - req.valor
    cur.execute("UPDATE clientes SET saldo=%s WHERE id=%s", (saldo_posterior, req.cliente_id))
    cur.execute("""
        INSERT INTO transacoes (cliente_id, tipo, valor, descricao, saldo_anterior, saldo_posterior)
        VALUES (%s, 'saque', %s, %s, %s, %s)
    """, (req.cliente_id, req.valor, req.descricao or "Saque", saldo_anterior, saldo_posterior))
    conn.commit()
    conn.close()
    return {"success": True, "saldo_anterior": saldo_anterior, "saldo_posterior": saldo_posterior}

@app.post("/transacoes/transferir")
def transferir(req: TransferenciaRequest):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, nome, saldo FROM clientes WHERE id=%s", (req.remetente_id,))
    remetente = cur.fetchone()
    cur.execute("SELECT id, nome, saldo FROM clientes WHERE id=%s", (req.destinatario_id,))
    destinatario = cur.fetchone()
    if not remetente or not destinatario:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    saldo_remetente = float(remetente["saldo"])
    if req.valor > saldo_remetente:
        raise HTTPException(status_code=400, detail="Saldo insuficiente")
    novo_saldo_remetente = saldo_remetente - req.valor
    novo_saldo_destinatario = float(destinatario["saldo"]) + req.valor
    cur.execute("UPDATE clientes SET saldo=%s WHERE id=%s", (novo_saldo_remetente, req.remetente_id))
    cur.execute("UPDATE clientes SET saldo=%s WHERE id=%s", (novo_saldo_destinatario, req.destinatario_id))
    cur.execute("""
        INSERT INTO transacoes (cliente_id, tipo, valor, descricao, saldo_anterior, saldo_posterior)
        VALUES (%s, 'transferencia_enviada', %s, %s, %s, %s)
    """, (req.remetente_id, req.valor, f"Transferência para {destinatario['nome']}", saldo_remetente, novo_saldo_remetente))
    cur.execute("""
        INSERT INTO transacoes (cliente_id, tipo, valor, descricao, saldo_anterior, saldo_posterior)
        VALUES (%s, 'transferencia_recebida', %s, %s, %s, %s)
    """, (req.destinatario_id, req.valor, f"Transferência de {remetente['nome']}", float(destinatario["saldo"]), novo_saldo_destinatario))
    cur.execute("""
        INSERT INTO transferencias (remetente_id, destinatario_id, valor, descricao)
        VALUES (%s, %s, %s, %s)
    """, (req.remetente_id, req.destinatario_id, req.valor, req.descricao or "Transferência"))
    conn.commit()
    conn.close()
    return {"success": True, "saldo_anterior": saldo_remetente, "saldo_posterior": novo_saldo_remetente}

@app.post("/investimentos/aportar")
def aportar(req: InvestimentoRequest):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT saldo FROM clientes WHERE id=%s", (req.cliente_id,))
    cliente = cur.fetchone()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    saldo_anterior = float(cliente["saldo"])
    if req.valor > saldo_anterior:
        raise HTTPException(status_code=400, detail="Saldo insuficiente")
    saldo_posterior = saldo_anterior - req.valor
    cur.execute("UPDATE clientes SET saldo=%s WHERE id=%s", (saldo_posterior, req.cliente_id))
    cur.execute("""
        INSERT INTO investimentos (cliente_id, tipo, valor, status)
        VALUES (%s, %s, %s, 'ativo')
    """, (req.cliente_id, req.tipo, req.valor))
    cur.execute("""
        INSERT INTO transacoes (cliente_id, tipo, valor, descricao, saldo_anterior, saldo_posterior)
        VALUES (%s, 'investimento_aporte', %s, %s, %s, %s)
    """, (req.cliente_id, req.valor, f"Aporte em {req.tipo}", saldo_anterior, saldo_posterior))
    conn.commit()
    conn.close()
    return {"success": True, "saldo_anterior": saldo_anterior, "saldo_posterior": saldo_posterior}

@app.get("/investimentos/{cliente_id}")
def get_investimentos(cliente_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, tipo, valor, status, criado_em
        FROM investimentos WHERE cliente_id=%s AND status='ativo'
        ORDER BY criado_em DESC
    """, (cliente_id,))
    investimentos = [dict(i) for i in cur.fetchall()]
    conn.close()
    return {"investimentos": investimentos}

@app.post("/investimentos/resgatar/{investimento_id}")
def resgatar(investimento_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM investimentos WHERE id=%s AND status='ativo'", (investimento_id,))
    investimento = cur.fetchone()
    if not investimento:
        raise HTTPException(status_code=404, detail="Investimento não encontrado")
    cliente_id = investimento["cliente_id"]
    valor = float(investimento["valor"])
    cur.execute("SELECT saldo FROM clientes WHERE id=%s", (cliente_id,))
    cliente = cur.fetchone()
    saldo_anterior = float(cliente["saldo"])
    saldo_posterior = saldo_anterior + valor
    cur.execute("UPDATE clientes SET saldo=%s WHERE id=%s", (saldo_posterior, cliente_id))
    cur.execute("UPDATE investimentos SET status='resgatado' WHERE id=%s", (investimento_id,))
    cur.execute("""
        INSERT INTO transacoes (cliente_id, tipo, valor, descricao, saldo_anterior, saldo_posterior)
        VALUES (%s, 'investimento_resgate', %s, %s, %s, %s)
    """, (cliente_id, valor, f"Resgate de {investimento['tipo']}", saldo_anterior, saldo_posterior))
    conn.commit()
    conn.close()
    return {"success": True, "saldo_anterior": saldo_anterior, "saldo_posterior": saldo_posterior}

@app.get("/clientes")
def get_clientes():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, nome FROM clientes ORDER BY nome")
    clientes = [dict(c) for c in cur.fetchall()]
    conn.close()
    return {"clientes": clientes}
