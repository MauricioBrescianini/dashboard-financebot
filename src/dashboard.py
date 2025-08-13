import streamlit as st
import pandas as pd
from data_collector import DataCollector
from analyzer import DataAnalyzer
from datetime import datetime, date

# Configuração da página
st.set_page_config(
    page_title="Dashboard de Vendas",
    page_icon="📊",
    layout="wide"
)

# Inicializar data collector
@st.cache_resource
def get_data_collector():
    return DataCollector()

data_collector = get_data_collector()

# Sidebar para navegação
st.sidebar.title("🏠 Navegação")
page = st.sidebar.selectbox(
    "Escolha uma página:",
    ["📊 Dashboard", "➕ Cadastro", "📋 Histórico"]
)

# Cache para dados
@st.cache_data
def load_data():
    """Carrega dados do banco ou fallback"""
    try:
        df = data_collector.load_from_database()
        st.success(f"✅ Dados carregados do PostgreSQL: {len(df)} registros")
        return df
    except Exception as e:
        st.warning(f"⚠️ Usando dados de exemplo. Erro do banco: {str(e)}")
        return data_collector.collect_sample_data()

def show_dashboard():
    """Página principal do dashboard"""
    st.title("📊 Dashboard de Análise de Vendas")
    
    # Carregar dados
    df = load_data()
    
    if df is None or df.empty:
        st.error("❌ Não foi possível carregar os dados!")
        return
    
    # Filtros na sidebar
    st.sidebar.header("🔍 Filtros")
    
    produtos = st.sidebar.multiselect(
        "Selecione os Produtos:",
        options=sorted(df['produto'].unique()),
        default=df['produto'].unique()
    )
    
    regioes = st.sidebar.multiselect(
        "Selecione as Regiões:",
        options=sorted(df['regiao'].unique()),
        default=df['regiao'].unique()
    )
    
    # Verificar filtros
    if not produtos or not regioes:
        st.warning("⚠️ Selecione pelo menos um produto e uma região!")
        return
    
    # Filtrar dados
    df_filtrado = df[
        (df['produto'].isin(produtos)) & 
        (df['regiao'].isin(regioes))
    ]
    
    if df_filtrado.empty:
        st.warning("⚠️ Nenhum dado encontrado com os filtros selecionados!")
        return
    
    # Métricas principais
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="💰 Total de Vendas",
            value=f"R$ {df_filtrado['vendas'].sum():,.0f}",
            delta=f"Média: R$ {df_filtrado['vendas'].mean():.1f}"
        )
    
    with col2:
        st.metric(
            label="📊 Registros",
            value=len(df_filtrado)
        )
    
    with col3:
        try:
            produto_top = df_filtrado.groupby('produto')['vendas'].sum().idxmax()
            st.metric(label="🏆 Produto Top", value=produto_top)
        except:
            st.metric(label="🏆 Produto Top", value="N/A")
    
    with col4:
        try:
            regiao_top = df_filtrado.groupby('regiao')['vendas'].sum().idxmax()
            st.metric(label="🌍 Região Top", value=regiao_top)
        except:
            st.metric(label="🌍 Região Top", value="N/A")
    
    st.markdown("---")
    
    # Gráficos
    analyzer = DataAnalyzer(df_filtrado)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Evolução Temporal das Vendas")
        try:
            fig_linha = analyzer.criar_grafico_linha()
            st.plotly_chart(fig_linha, use_container_width=True)
        except Exception as e:
            st.error(f"Erro ao criar gráfico: {e}")
    
    with col2:
        st.subheader("🥧 Distribuição por Produto")
        try:
            fig_pizza = analyzer.criar_grafico_pizza()
            st.plotly_chart(fig_pizza, use_container_width=True)
        except Exception as e:
            st.error(f"Erro ao criar gráfico: {e}")
    
    st.markdown("---")
    
    # Tabela de dados
    st.subheader("📋 Dados Detalhados")
    st.dataframe(df_filtrado, use_container_width=True)
    
    # Download
    csv = df_filtrado.to_csv(index=False)
    st.download_button(
        label="📥 Download dos Dados (CSV)",
        data=csv,
        file_name=f'dados_vendas_{datetime.now().strftime("%Y%m%d_%H%M")}.csv',
        mime='text/csv'
    )

def show_cadastro():
    """Página de cadastro de novas vendas"""
    st.title("➕ Cadastro de Nova Venda")
    st.markdown("Preencha os campos abaixo para registrar uma nova venda:")
    
    # Formulário de cadastro
    with st.form("form_cadastro", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            # Data da venda
            data_venda = st.date_input(
                "📅 Data da Venda:",
                value=date.today(),
                max_value=date.today(),
                help="Selecione a data da venda"
            )
            
            # Produto
            produto = st.selectbox(
                "🛍️ Produto:",
                options=["Produto A", "Produto B", "Produto C", "Produto D"],
                help="Selecione o produto vendido"
            )
        
        with col2:
            # Valor da venda
            valor_venda = st.number_input(
                "💰 Valor da Venda (R$):",
                min_value=0.01,
                max_value=999999.99,
                value=100.00,
                step=0.01,
                help="Digite o valor da venda"
            )
            
            # Região
            regiao = st.selectbox(
                "🌍 Região:",
                options=["Norte", "Sul", "Centro", "Leste", "Oeste"],
                help="Selecione a região da venda"
            )
        
        # Observações (opcional)
        observacoes = st.text_area(
            "📝 Observações (opcional):",
            max_chars=200,
            help="Adicione observações sobre a venda"
        )
        
        # Botão de submissão
        submitted = st.form_submit_button(
            "💾 Salvar Venda",
            use_container_width=True,
            type="primary"
        )
        
        if submitted:
            # Validações
            if not produto or not regiao:
                st.error("❌ Todos os campos obrigatórios devem ser preenchidos!")
                return
            
            if valor_venda <= 0:
                st.error("❌ O valor da venda deve ser maior que zero!")
                return
            
            # Preparar dados para salvar
            nova_venda = {
                'data': data_venda,
                'vendas': int(valor_venda),
                'produto': produto,
                'regiao': regiao
            }
            
            # Tentar salvar no banco
            try:
                # Criar DataFrame com nova venda
                df_nova = pd.DataFrame([nova_venda])
                
                # Salvar no banco
                success = data_collector.insert_new_sale(df_nova)
                
                if success:
                    st.success("✅ Venda cadastrada com sucesso!")
                    st.balloons()  # Efeito visual
                    
                    # Mostrar resumo da venda cadastrada
                    st.info(f"""
                    **📋 Resumo da Venda Cadastrada:**
                    - **Data:** {data_venda.strftime('%d/%m/%Y')}
                    - **Produto:** {produto}
                    - **Valor:** R$ {valor_venda:,.2f}
                    - **Região:** {regiao}
                    {f"- **Observações:** {observacoes}" if observacoes else ""}
                    """)
                    
                    # Limpar cache para atualizar dados
                    st.cache_data.clear()
                    
                else:
                    st.error("❌ Erro ao salvar a venda. Tente novamente.")
                    
            except Exception as e:
                st.error(f"❌ Erro ao processar cadastro: {str(e)}")

def show_historico():
    """Página de histórico com todas as vendas"""
    st.title("📋 Histórico de Vendas")
    
    # Carregar dados
    df = load_data()
    
    if df is None or df.empty:
        st.error("❌ Não foi possível carregar o histórico!")
        return
    
    # Estatísticas rápidas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📊 Total Registros", len(df))
    with col2:
        st.metric("💰 Valor Total", f"R$ {df['vendas'].sum():,.0f}")
    with col3:
        st.metric("📅 Primeiro Registro", df['data'].min().strftime('%d/%m/%Y'))
    with col4:
        st.metric("📅 Último Registro", df['data'].max().strftime('%d/%m/%Y'))
    
    st.markdown("---")
    
    # Filtros para histórico
    col1, col2, col3 = st.columns(3)
    
    with col1:
        produtos_hist = st.multiselect(
            "Filtrar por Produto:",
            options=sorted(df['produto'].unique()),
            default=df['produto'].unique()
        )
    
    with col2:
        regioes_hist = st.multiselect(
            "Filtrar por Região:",
            options=sorted(df['regiao'].unique()),
            default=df['regiao'].unique()
        )
    
    with col3:
        # Filtro por período
        periodo = st.selectbox(
            "Período:",
            ["Todos", "Últimos 7 dias", "Último mês", "Últimos 3 meses"]
        )
    
    # Aplicar filtros
    df_filtrado = df[
        (df['produto'].isin(produtos_hist)) & 
        (df['regiao'].isin(regioes_hist))
    ]
    
    # Filtro por período
    if periodo != "Todos":
        hoje = pd.Timestamp.now()
        if periodo == "Últimos 7 dias":
            data_limite = hoje - pd.Timedelta(days=7)
        elif periodo == "Último mês":
            data_limite = hoje - pd.Timedelta(days=30)
        elif periodo == "Últimos 3 meses":
            data_limite = hoje - pd.Timedelta(days=90)
        
        df_filtrado = df_filtrado[df_filtrado['data'] >= data_limite]
    
    # Ordenar por data (mais recente primeiro)
    df_filtrado = df_filtrado.sort_values('data', ascending=False)
    
    # Mostrar tabela
    st.subheader(f"📊 Exibindo {len(df_filtrado)} registros")
    
    # Opção de paginação
    registros_por_pagina = st.selectbox("Registros por página:", [10, 25, 50, 100])
    
    if len(df_filtrado) > registros_por_pagina:
        total_paginas = (len(df_filtrado) // registros_por_pagina) + 1
        pagina = st.number_input("Página:", 1, total_paginas, 1)
        
        inicio = (pagina - 1) * registros_por_pagina
        fim = inicio + registros_por_pagina
        df_exibir = df_filtrado.iloc[inicio:fim]
        
        st.write(f"Página {pagina} de {total_paginas}")
    else:
        df_exibir = df_filtrado
    
    # Formatar dados para exibição
    df_display = df_exibir.copy()
    df_display['data'] = df_display['data'].dt.strftime('%d/%m/%Y')
    df_display['vendas'] = df_display['vendas'].apply(lambda x: f"R$ {x:,.2f}")
    
    st.dataframe(df_display, use_container_width=True)

# Roteamento de páginas
if page == "📊 Dashboard":
    show_dashboard()
elif page == "➕ Cadastro":
    show_cadastro()
elif page == "📋 Histórico":
    show_historico()

# Footer
st.markdown("---")
st.markdown("**Desenvolvido com ❤️ usando Streamlit + Python | Prof. Daniel Moreira**")
