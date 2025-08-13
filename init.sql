-- Criar tabela de gastos
CREATE TABLE IF NOT EXISTS gastos (
    id SERIAL PRIMARY KEY,
    data DATE NOT NULL,
    valor DECIMAL(10,2) NOT NULL,
    categoria VARCHAR(50) NOT NULL,
    descricao VARCHAR(200),
    forma_pagamento VARCHAR(50) DEFAULT 'Dinheiro',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Limpar dados existentes (para evitar duplicação)
TRUNCATE TABLE gastos RESTART IDENTITY;

-- Inserir dados de exemplo
-- INSERT INTO gastos (data, valor, categoria, descricao, forma_pagamento) VALUES


-- Criar índices para performance
CREATE INDEX IF NOT EXISTS idx_gastos_data ON gastos(data);
CREATE INDEX IF NOT EXISTS idx_gastos_categoria ON gastos(categoria);
CREATE INDEX IF NOT EXISTS idx_gastos_forma_pagamento ON gastos(forma_pagamento);
