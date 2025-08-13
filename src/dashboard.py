import streamlit as st
import pandas as pd
from data_collector import DataCollector
from analyzer import DataAnalyzer

# Configuração da página
st.set_page_config(
    page_title="Dashboard de Vendas",
    page_icon="📊",
    layout="wide"
)

# Título principal
st.title("📊 Dashboard de Análise de Vendas")

# Sidebar para controles
st.sidebar.header("Filtros")

@st.cache_data
def load_data():
    """Carrega dados com cache para performance"""
    collector = DataCollector()
    return collector.collect_sample_data()

# Carregar dados
df = load_data()

# Filtros na sidebar
produtos = st.sidebar.multiselect(
    "Selecione os Produtos:",
    options=df['produto'].unique(),
    default=df['produto'].unique()
)

regioes = st.sidebar.multiselect(
    "Selecione as Regiões:",
    options=df['regiao'].unique(),
    default=df['regiao'].unique()
)

# Filtrar dados baseado na seleção
df_filtrado = df[
    (df['produto'].isin(produtos)) & 
    (df['regiao'].isin(regioes))
]

# Métricas principais
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Total de Vendas",
        value=f"R$ {df_filtrado['vendas'].sum():,.0f}",
        delta=f"{df_filtrado['vendas'].mean():.1f} média"
    )

with col2:
    st.metric(
        label="Número de Registros",
        value=len(df_filtrado)
    )

with col3:
    st.metric(
        label="Produto Top",
        value=df_filtrado.groupby('produto')['vendas'].sum().idxmax()
    )

with col4:
    st.metric(
        label="Região Top",
        value=df_filtrado.groupby('regiao')['vendas'].sum().idxmax()
    )

# Análise e gráficos
analyzer = DataAnalyzer(df_filtrado)

# Layout em duas colunas
col1, col2 = st.columns(2)

with col1:
    st.subheader("Evolução Temporal das Vendas")
    fig_linha = analyzer.criar_grafico_linha()
    st.plotly_chart(fig_linha, use_container_width=True)

with col2:
    st.subheader("Distribuição por Produto")
    fig_pizza = analyzer.criar_grafico_pizza()
    st.plotly_chart(fig_pizza, use_container_width=True)

# Tabela de dados
st.subheader("Dados Detalhados")
st.dataframe(df_filtrado, use_container_width=True)

# Download dos dados
csv = df_filtrado.to_csv(index=False)
st.download_button(
    label="📥 Download dos Dados (CSV)",
    data=csv,
    file_name='dados_vendas.csv',
    mime='text/csv'
)
