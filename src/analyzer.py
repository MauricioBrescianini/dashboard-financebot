import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

class DataAnalyzer:
    def __init__(self, df):
        self.df = df
    
    def gastos_por_mes(self):
        """Análise de gastos por mês"""
        if 'data' in self.df.columns:
            monthly = self.df.groupby(self.df['data'].dt.to_period('M'))['valor'].sum()
            return monthly
        return pd.Series()
    
    def gastos_por_categoria(self):
        """Análise de gastos por categoria"""
        categoria_gastos = self.df.groupby('categoria')['valor'].sum()
        return categoria_gastos
    
    def gastos_por_forma_pagamento(self):
        """Análise de gastos por forma de pagamento"""
        if 'forma_pagamento' in self.df.columns:
            pagamento_gastos = self.df.groupby('forma_pagamento')['valor'].sum()
            return pagamento_gastos
        return pd.Series()
    
    def criar_grafico_linha(self):
        """Gráfico de linha temporal dos gastos"""
        # Agrupar por data
        gastos_diarios = self.df.groupby('data')['valor'].sum().reset_index()
        
        fig = px.line(
            gastos_diarios, 
            x='data', 
            y='valor',
            title='Evolução dos Gastos no Tempo',
            labels={'valor': 'Valor (R$)', 'data': 'Data'}
        )
        
        # Customizar layout
        fig.update_layout(
            xaxis_title="Data",
            yaxis_title="Valor (R$)",
            hovermode='x unified'
        )
        
        # Formatar valores no hover
        fig.update_traces(hovertemplate='R$ %{y:,.2f}<extra></extra>')
        
        return fig
    
    def criar_grafico_pizza(self):
        """Gráfico de pizza por categoria"""
        categoria_gastos = self.gastos_por_categoria()
        
        fig = px.pie(
            values=categoria_gastos.values,
            names=categoria_gastos.index,
            title='Distribuição de Gastos por Categoria'
        )
        
        # Customizar layout
        fig.update_traces(
            textposition='inside', 
            textinfo='percent+label',
            hovertemplate='<b>%{label}</b><br>R$ %{value:,.2f}<br>%{percent}<extra></extra>'
        )
        
        return fig
    
    def criar_grafico_barras_categoria(self):
        """Gráfico de barras horizontais por categoria"""
        categoria_gastos = self.gastos_por_categoria().sort_values(ascending=True)
        
        fig = px.bar(
            x=categoria_gastos.values,
            y=categoria_gastos.index,
            orientation='h',
            title='Total de Gastos por Categoria',
            labels={'x': 'Valor (R$)', 'y': 'Categoria'}
        )
        
        # Customizar layout
        fig.update_layout(
            xaxis_title="Valor (R$)",
            yaxis_title="Categoria"
        )
        
        # Formatar valores no hover
        fig.update_traces(hovertemplate='<b>%{y}</b><br>R$ %{x:,.2f}<extra></extra>')
        
        return fig
    
    def criar_grafico_mensal(self):
        """Gráfico de gastos mensais por categoria"""
        if len(self.df) == 0:
            return go.Figure()
        
        # Preparar dados mensais
        self.df['mes_ano'] = self.df['data'].dt.to_period('M').astype(str)
        gastos_mensais = self.df.groupby(['mes_ano', 'categoria'])['valor'].sum().reset_index()
        
        fig = px.bar(
            gastos_mensais,
            x='mes_ano',
            y='valor',
            color='categoria',
            title='Gastos Mensais por Categoria',
            labels={'valor': 'Valor (R$)', 'mes_ano': 'Mês/Ano', 'categoria': 'Categoria'}
        )
        
        fig.update_layout(
            xaxis_title="Mês/Ano",
            yaxis_title="Valor (R$)",
            legend_title="Categoria"
        )
        
        return fig
    
    def get_top_gastos(self, n=5):
        """Retorna os N maiores gastos"""
        if len(self.df) == 0:
            return pd.DataFrame()
        
        return self.df.nlargest(n, 'valor')[['data', 'categoria', 'valor', 'descricao']]
    
    def get_estatisticas_basicas(self):
        """Retorna estatísticas básicas dos gastos SEM conversões float()"""
        if len(self.df) == 0:
            return {}
        
        # Usar operações diretas do pandas sem conversões manuais
        return {
            'total_gastos': self.df['valor'].sum(),  # Já retorna float nativo
            'media_gastos': self.df['valor'].mean(),  # Já retorna float nativo
            'mediana_gastos': self.df['valor'].median(),  # Já retorna float nativo
            'maior_gasto': self.df['valor'].max(),  # Já retorna float nativo
            'menor_gasto': self.df['valor'].min(),  # Já retorna float nativo
            'total_transacoes': len(self.df),  # Já retorna int
            'categoria_mais_gasta': self.gastos_por_categoria().idxmax() if not self.gastos_por_categoria().empty else 'N/A'
        }

