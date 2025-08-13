import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

class DataAnalyzer:
    def __init__(self, df):
        self.df = df
    
    def vendas_por_mes(self):
        """Análise de vendas por mês"""
        monthly = self.df.groupby(self.df['data'].dt.month)['vendas'].sum()
        return monthly
    
    def vendas_por_produto(self):
        """Análise de vendas por produto"""
        produto_vendas = self.df.groupby('produto')['vendas'].sum()
        return produto_vendas
    
    def criar_grafico_linha(self):
        """Gráfico de linha temporal"""
        fig = px.line(self.df, x='data', y='vendas', 
                     title='Evolução das Vendas no Tempo')
        return fig
    
    def criar_grafico_pizza(self):
        """Gráfico de pizza por produto"""
        produto_vendas = self.vendas_por_produto()
        fig = px.pie(values=produto_vendas.values, 
                    names=produto_vendas.index,
                    title='Distribuição de Vendas por Produto')
        return fig
