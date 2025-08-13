-- Criar tabela de vendas
CREATE TABLE IF NOT EXISTS vendas (
    id SERIAL PRIMARY KEY,
    data DATE NOT NULL,
    vendas INTEGER NOT NULL,
    produto VARCHAR(50) NOT NULL,
    regiao VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Limpar dados existentes (para evitar duplicação)
TRUNCATE TABLE vendas RESTART IDENTITY;

-- Inserir dados de exemplo
INSERT INTO vendas (data, vendas, produto, regiao) VALUES
('2024-01-01', 150, 'Produto A', 'Norte'),
('2024-01-02', 200, 'Produto B', 'Sul'),
('2024-01-03', 175, 'Produto C', 'Centro'),
('2024-01-04', 300, 'Produto A', 'Leste'),
('2024-01-05', 250, 'Produto B', 'Oeste'),
('2024-01-06', 180, 'Produto C', 'Norte'),
('2024-01-07', 220, 'Produto A', 'Sul'),
('2024-01-08', 190, 'Produto B', 'Centro'),
('2024-01-09', 280, 'Produto C', 'Leste'),
('2024-01-10', 160, 'Produto A', 'Oeste'),
('2024-01-11', 320, 'Produto A', 'Norte'),
('2024-01-12', 290, 'Produto B', 'Sul'),
('2024-01-13', 210, 'Produto C', 'Centro'),
('2024-01-14', 380, 'Produto A', 'Leste'),
('2024-01-15', 270, 'Produto B', 'Oeste');

-- Criar índices para performance
CREATE INDEX IF NOT EXISTS idx_vendas_data ON vendas(data);
CREATE INDEX IF NOT EXISTS idx_vendas_produto ON vendas(produto);
CREATE INDEX IF NOT EXISTS idx_vendas_regiao ON vendas(regiao);
