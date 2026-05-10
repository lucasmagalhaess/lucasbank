-- Tabela de clientes
CREATE TABLE IF NOT EXISTS clientes (
    id INTEGER PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    login VARCHAR(50) UNIQUE NOT NULL,
    senha VARCHAR(100) NOT NULL,
    saldo DECIMAL(15,2) NOT NULL DEFAULT 0,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de transacoes
CREATE TABLE IF NOT EXISTS transacoes (
    id SERIAL PRIMARY KEY,
    cliente_id INTEGER REFERENCES clientes(id),
    tipo VARCHAR(50) NOT NULL,
    valor DECIMAL(15,2) NOT NULL,
    descricao TEXT,
    saldo_anterior DECIMAL(15,2),
    saldo_posterior DECIMAL(15,2),
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de investimentos
CREATE TABLE IF NOT EXISTS investimentos (
    id SERIAL PRIMARY KEY,
    cliente_id INTEGER REFERENCES clientes(id),
    tipo VARCHAR(50) NOT NULL,
    valor DECIMAL(15,2) NOT NULL,
    status VARCHAR(20) DEFAULT 'ativo',
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de transferencias
CREATE TABLE IF NOT EXISTS transferencias (
    id SERIAL PRIMARY KEY,
    remetente_id INTEGER REFERENCES clientes(id),
    destinatario_id INTEGER REFERENCES clientes(id),
    valor DECIMAL(15,2) NOT NULL,
    descricao TEXT,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Inserindo os 4 clientes
INSERT INTO clientes (id, nome, login, senha, saldo) VALUES
    (1001, 'Lucas Magalhães', 'lucas', 'lucas', 15000.00),
    (1002, 'Ana Luiza', 'ana', 'ana', 8500.00),
    (1003, 'João Pedro', 'joao', 'joao', 12300.00),
    (1004, 'Yanne Silva', 'yanne', 'yanne', 6750.00)
ON CONFLICT (id) DO NOTHING;
