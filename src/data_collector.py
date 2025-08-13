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
    
    def load_from_database(self, table_name='vendas'):
        """Carrega dados do PostgreSQL"""
        try:
            query = f"SELECT * FROM {table_name} ORDER BY data DESC"
            df = pd.read_sql(query, self.engine)
            df['data'] = pd.to_datetime(df['data'])
            return df
        except Exception as e:
            print(f"Erro ao carregar dados: {e}")
            return self.collect_sample_data()
    
    def insert_new_sale(self, df_nova_venda, table_name='vendas'):
        """Insere nova venda no banco de dados"""
        try:
            # Inserir no banco
            df_nova_venda.to_sql(
                table_name, 
                self.engine, 
                if_exists='append', 
                index=False,
                method='multi'
            )
            print(f"✅ Nova venda inserida na tabela {table_name}")
            return True
        except Exception as e:
            print(f"❌ Erro ao inserir nova venda: {e}")
            return False
    
    def collect_sample_data(self):
        """Dados de fallback caso o banco não esteja disponível"""
        data = {
            'data': pd.date_range('2024-01-01', periods=100, freq='D'),
            'vendas': [100 + i*2 + (i%7)*10 for i in range(100)],
            'produto': ['Produto A', 'Produto B', 'Produto C'] * 34 + ['Produto A', 'Produto B'],
            'regiao': ['Norte', 'Sul', 'Centro', 'Leste', 'Oeste'] * 20
        }
        return pd.DataFrame(data)
    
    def save_to_database(self, df, table_name='vendas'):
        """Salva dados no PostgreSQL (substitui tabela completa)"""
        try:
            df.to_sql(table_name, self.engine, if_exists='replace', index=False)
            print(f"✅ Dados salvos na tabela {table_name}")
        except Exception as e:
            print(f"❌ Erro ao salvar dados: {e}")
    
    def get_database_stats(self, table_name='vendas'):
        """Retorna estatísticas da base de dados"""
        try:
            query = f"""
            SELECT 
                COUNT(*) as total_registros,
                SUM(vendas) as total_vendas,
                AVG(vendas) as media_vendas,
                MIN(data) as primeira_venda,
                MAX(data) as ultima_venda
            FROM {table_name}
            """
            stats = pd.read_sql(query, self.engine)
            return stats.iloc[0].to_dict()
        except Exception as e:
            print(f"Erro ao obter estatísticas: {e}")
            return {}
