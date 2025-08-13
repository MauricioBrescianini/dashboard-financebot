import pandas as pd
import requests
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv
import time

load_dotenv()

class DataCollector:
    def __init__(self):
        self.db_url = os.getenv('DATABASE_URL', 
                               'postgresql://admin:admin@postgres:5432/analytics')
        self.engine = None
        self._connect_with_retry()
    
    def _connect_with_retry(self, max_retries=5):
        """Conecta ao banco com retry (importante para Docker)"""
        for attempt in range(max_retries):
            try:
                self.engine = create_engine(self.db_url)
                with self.engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                print("✅ Conectado ao banco de dados!")
                return
            except Exception as e:
                print(f"❌ Tentativa {attempt + 1} falhou: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                else:
                    raise
    
    def load_from_database(self, table_name='gastos'):
        """Carrega dados do PostgreSQL"""
        try:
            query = f"SELECT * FROM {table_name} ORDER BY data DESC"
            df = pd.read_sql(query, self.engine)
            df['data'] = pd.to_datetime(df['data'])
            return df
        except Exception as e:
            print(f"Erro ao carregar dados: {e}")
            return self.collect_sample_data()
    
    def insert_new_expense(self, df_novo_gasto, table_name='gastos'):
        """Insere novo gasto no banco de dados"""
        try:
            df_novo_gasto.to_sql(
                table_name, 
                self.engine, 
                if_exists='append', 
                index=False,
                method='multi'
            )
            print(f"✅ Novo gasto inserido na tabela {table_name}")
            return True
        except Exception as e:
            print(f"❌ Erro ao inserir novo gasto: {e}")
            return False
    
    def collect_sample_data(self):
        """Dados de fallback caso o banco não esteja disponível"""
        import random
        from datetime import datetime, timedelta
        
        categorias = ['Alimentação', 'Transporte', 'Lazer', 'Saúde', 'Roupas', 'Mensalidades']
        formas_pagamento = ['Dinheiro', 'Cartão Crédito', 'Cartão Débito', 'PIX', 'Débito Automático']
        
        # Gerar dados de exemplo para os últimos 30 dias
        data_base = datetime.now() - timedelta(days=30)
        dados = []
        
        for i in range(50):
            dados.append({
                'data': data_base + timedelta(days=random.randint(0, 30)),
                'valor': round(random.uniform(15.0, 300.0), 2),
                'categoria': random.choice(categorias),
                'descricao': f'Gasto exemplo {i+1}',
                'forma_pagamento': random.choice(formas_pagamento)
            })
        
        return pd.DataFrame(dados)
    
    def get_monthly_summary(self, table_name='gastos'):
        """Retorna resumo mensal dos gastos"""
        try:
            query = f"""
            SELECT 
                DATE_TRUNC('month', data) as mes,
                categoria,
                SUM(valor) as total_categoria,
                COUNT(*) as quantidade,
                AVG(valor) as media_categoria
            FROM {table_name}
            GROUP BY DATE_TRUNC('month', data), categoria
            ORDER BY mes DESC, total_categoria DESC
            """
            df = pd.read_sql(query, self.engine)
            return df
        except Exception as e:
            print(f"Erro ao obter resumo mensal: {e}")
            return pd.DataFrame()
    
    def get_category_summary(self, table_name='gastos'):
        """Retorna resumo por categoria"""
        try:
            query = f"""
            SELECT 
                categoria,
                SUM(valor) as total_gasto,
                COUNT(*) as total_transacoes,
                AVG(valor) as valor_medio,
                MIN(valor) as menor_gasto,
                MAX(valor) as maior_gasto
            FROM {table_name}
            GROUP BY categoria
            ORDER BY total_gasto DESC
            """
            df = pd.read_sql(query, self.engine)
            return df
        except Exception as e:
            print(f"Erro ao obter resumo por categoria: {e}")
            return pd.DataFrame()
    
    def get_database_stats(self, table_name='gastos'):
        """Retorna estatísticas da base de dados"""
        try:
            query = f"""
            SELECT 
                COUNT(*) as total_registros,
                SUM(valor) as total_gastos,
                AVG(valor) as media_gastos,
                MIN(data) as primeiro_gasto,
                MAX(data) as ultimo_gasto,
                COUNT(DISTINCT categoria) as total_categorias
            FROM {table_name}
            """
            stats = pd.read_sql(query, self.engine)
            return stats.iloc[0].to_dict()
        except Exception as e:
            print(f"Erro ao obter estatísticas: {e}")
            return {}
