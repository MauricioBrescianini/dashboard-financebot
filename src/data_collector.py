import pandas as pd
import requests
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

load_dotenv()

class DataCollector:
    def __init__(self):
        self.db_url = os.getenv('DATABASE_URL', 
                               'postgresql://user:password@localhost:5432/analytics')
        self.engine = create_engine(self.db_url)
    
    def collect_sample_data(self):
        """Coleta dados de exemplo para o dashboard"""
        # Simulando dados de vendas (em produção, seria uma API real)
        data = {
            'data': pd.date_range('2024-01-01', periods=100, freq='D'),
            'vendas': pd.Series([100 + i*2 + (i%7)*10 for i in range(100)]),
            'produto': ['Produto A', 'Produto B', 'Produto C'] * 34 + ['Produto A', 'Produto B'],
            'regiao': ['Norte', 'Sul', 'Centro', 'Leste', 'Oeste'] * 20
        }
        return pd.DataFrame(data)
    
    def save_to_database(self, df, table_name):
        """Salva dados no PostgreSQL"""
        df.to_sql(table_name, self.engine, if_exists='replace', index=False)
        print(f"Dados salvos na tabela {table_name}")
