import streamlit as st
import pandas as pd
from data_collector import DataCollector
from analyzer import DataAnalyzer
from datetime import datetime, date
import plotly.express as px
import traceback # ← ADICIONAR PARA DEBUG

# Configuração da página
st.set_page_config(
    page_title="Controle de Gastos",
    page_icon="💰",
    layout="wide"
)

# === IMPORTAÇÃO COM TRATAMENTO DE ERRO ===
try:
    from chat_interface import show_chat_interface
    CHAT_AVAILABLE = True
    st.sidebar.success("✅ FinanceBot carregado!")
except Exception as e:
    CHAT_AVAILABLE = False
    st.sidebar.error(f"❌ Erro ao carregar FinanceBot: {str(e)}")
    st.sidebar.code(traceback.format_exc())

# Inicializar data collector
@st.cache_resource
def get_data_collector():
    return DataCollector()

data_collector = get_data_collector()

# Sidebar para navegação
st.sidebar.title("💰 Controle de Gastos")

# === SIDEBAR COM VERIFICAÇÃO ===
if CHAT_AVAILABLE:
    opcoes = ["📊 Dashboard", "➕ Novo Gasto", "📋 Histórico", "📈 Relatórios", "🤖 FinanceBot"]
else:
    opcoes = ["📊 Dashboard", "➕ Novo Gasto", "📋 Histórico", "📈 Relatórios"]
    st.sidebar.warning("⚠️ FinanceBot indisponível")

page = st.sidebar.selectbox("Escolha uma página:", opcoes)

# Cache para dados
@st.cache_data
def load_data():
    """Carrega dados do banco ou fallback"""
    try:
        df = data_collector.load_from_database()
        if not df.empty:
            st.sidebar.success(f"✅ {len(df)} gastos carregados")
        return df
    except Exception as e:
        st.sidebar.warning("⚠️ Usando dados de exemplo")
        return data_collector.collect_sample_data()

def show_dashboard():
    """Página principal do dashboard"""
    st.title("📊 Dashboard de Controle de Gastos")
    
    # Carregar dados
    df = load_data()
    
    if df is None or df.empty:
        st.error("❌ Não foi possível carregar os dados!")
        return
    
    # Filtros na sidebar
    st.sidebar.header("🔍 Filtros")
    
    # Filtro por categoria
    categorias = st.sidebar.multiselect(
        "Categorias:",
        options=sorted(df['categoria'].unique()),
        default=df['categoria'].unique()
    )
    
    # Filtro por forma de pagamento
    if 'forma_pagamento' in df.columns:
        formas_pagamento = st.sidebar.multiselect(
            "Forma de Pagamento:",
            options=sorted(df['forma_pagamento'].unique()),
            default=df['forma_pagamento'].unique()
        )
    else:
        formas_pagamento = []
    
    # Filtro por período
    periodo = st.sidebar.selectbox(
        "Período:",
        ["Todos", "Últimos 7 dias", "Último mês", "Últimos 3 meses", "Este ano"]
    )
    
    # Aplicar filtros
    df_filtrado = df[df['categoria'].isin(categorias)]
    
    if formas_pagamento and 'forma_pagamento' in df.columns:
        df_filtrado = df_filtrado[df_filtrado['forma_pagamento'].isin(formas_pagamento)]
    
    # Filtro por período
    if periodo != "Todos":
        hoje = pd.Timestamp.now()
        if periodo == "Últimos 7 dias":
            data_limite = hoje - pd.Timedelta(days=7)
        elif periodo == "Último mês":
            data_limite = hoje - pd.Timedelta(days=30)
        elif periodo == "Últimos 3 meses":
            data_limite = hoje - pd.Timedelta(days=90)
        elif periodo == "Este ano":
            data_limite = pd.Timestamp(hoje.year, 1, 1)
        
        df_filtrado = df_filtrado[df_filtrado['data'] >= data_limite]
    
    if df_filtrado.empty:
        st.warning("⚠️ Nenhum gasto encontrado com os filtros selecionados!")
        return
    
    # Análise dos dados
    analyzer = DataAnalyzer(df_filtrado)
    stats = analyzer.get_estatisticas_basicas()
    
    # Métricas principais
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="💸 Total de Gastos",
            value=f"R$ {stats.get('total_gastos', 0):,.2f}",
            delta=f"Média: R$ {stats.get('media_gastos', 0):.2f}"
        )
    
    with col2:
        st.metric(
            label="📊 Total de Transações",
            value=stats.get('total_transacoes', 0)
        )
    
    with col3:
        st.metric(
            label="🏆 Categoria Top",
            value=stats.get('categoria_mais_gasta', 'N/A')
        )
    
    with col4:
        st.metric(
            label="💰 Maior Gasto",
            value=f"R$ {stats.get('maior_gasto', 0):.2f}",
            delta=f"Menor: R$ {stats.get('menor_gasto', 0):.2f}"
        )
    
    st.markdown("---")
    
    # Gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Evolução dos Gastos")
        try:
            fig_linha = analyzer.criar_grafico_linha()
            st.plotly_chart(fig_linha, use_container_width=True)
        except Exception as e:
            st.error(f"Erro ao criar gráfico: {e}")
    
    with col2:
        st.subheader("🥧 Gastos por Categoria")
        try:
            fig_pizza = analyzer.criar_grafico_pizza()
            st.plotly_chart(fig_pizza, use_container_width=True)
        except Exception as e:
            st.error(f"Erro ao criar gráfico: {e}")
    
    # Gráfico adicional
    st.subheader("📊 Comparativo por Categoria")
    try:
        fig_barras = analyzer.criar_grafico_barras_categoria()
        st.plotly_chart(fig_barras, use_container_width=True)
    except Exception as e:
        st.error(f"Erro ao criar gráfico: {e}")
    
    st.markdown("---")
    
    # Top gastos
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💸 Maiores Gastos")
        top_gastos = analyzer.get_top_gastos(10)
        if not top_gastos.empty:
            top_gastos_display = top_gastos.copy()
            top_gastos_display['data'] = top_gastos_display['data'].dt.strftime('%d/%m/%Y')
            top_gastos_display['valor'] = top_gastos_display['valor'].apply(lambda x: f"R$ {x:,.2f}")
            st.dataframe(top_gastos_display, use_container_width=True, hide_index=True)
    
    with col2:
        st.subheader("📋 Resumo por Categoria")
        categoria_resumo = df_filtrado.groupby('categoria').agg({
            'valor': ['sum', 'count', 'mean']
        }).round(2)
        categoria_resumo.columns = ['Total (R$)', 'Qtd', 'Média (R$)']
        categoria_resumo = categoria_resumo.sort_values('Total (R$)', ascending=False)
        st.dataframe(categoria_resumo, use_container_width=True)

def show_cadastro():
    """Página de cadastro de novos gastos"""
    st.title("➕ Cadastro de Novo Gasto")
    st.markdown("Registre seus gastos para manter o controle financeiro:")
    
    # Formulário de cadastro
    with st.form("form_cadastro_gasto", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            # Data do gasto
            data_gasto = st.date_input(
                "📅 Data do Gasto:",
                value=date.today(),
                max_value=date.today(),
                help="Data em que o gasto foi realizado"
            )
            
            # Categoria
            categoria = st.selectbox(
                "🏷️ Categoria:",
                options=["Alimentação", "Transporte", "Lazer", "Saúde", "Roupas", "Mensalidades", "Outros"],
                help="Selecione a categoria do gasto"
            )
            
            # Descrição
            descricao = st.text_input(
                "📝 Descrição:",
                max_chars=200,
                help="Descreva brevemente o gasto"
            )
        
        with col2:
            # Valor do gasto
            valor_gasto = st.number_input(
                "💰 Valor (R$):",
                min_value=0.01,
                max_value=999999.99,
                value=10.00,
                step=0.01,
                help="Valor gasto em reais"
            )
            
            # Forma de pagamento
            forma_pagamento = st.selectbox(
                "💳 Forma de Pagamento:",
                options=["Dinheiro", "Cartão Crédito", "Cartão Débito", "PIX", "Débito Automático", "Outros"],
                help="Como foi realizado o pagamento"
            )
        
        # Observações adicionais
        observacoes = st.text_area(
            "📋 Observações (opcional):",
            max_chars=300,
            help="Informações adicionais sobre o gasto"
        )
        
        # Botão de submissão
        submitted = st.form_submit_button(
            "💾 Registrar Gasto",
            use_container_width=True,
            type="primary"
        )
        
        if submitted:
            # Validações
            if not categoria or not descricao:
                st.error("❌ Categoria e descrição são obrigatórios!")
                return
            
            if valor_gasto <= 0:
                st.error("❌ O valor deve ser maior que zero!")
                return
            
            # Preparar dados para salvar
            novo_gasto = {
                'data': data_gasto,
                'valor': float(valor_gasto),
                'categoria': categoria,
                'descricao': descricao,
                'forma_pagamento': forma_pagamento
            }
            
            # Tentar salvar no banco
            try:
                df_novo = pd.DataFrame([novo_gasto])
                success = data_collector.insert_new_expense(df_novo)
                
                if success:
                    st.success("✅ Gasto registrado com sucesso!")
                    st.balloons()
                    
                    # Mostrar resumo
                    st.info(f"""
                    **📋 Gasto Registrado:**
                    - **Data:** {data_gasto.strftime('%d/%m/%Y')}
                    - **Categoria:** {categoria}
                    - **Valor:** R$ {valor_gasto:,.2f}
                    - **Descrição:** {descricao}
                    - **Forma de Pagamento:** {forma_pagamento}
                    {f"- **Observações:** {observacoes}" if observacoes else ""}
                    """)
                    
                    # Limpar cache
                    st.cache_data.clear()
                else:
                    st.error("❌ Erro ao registrar o gasto. Tente novamente.")
                    
            except Exception as e:
                st.error(f"❌ Erro ao processar registro: {str(e)}")

def show_historico():
    """Página de histórico completo"""
    st.title("📋 Histórico de Gastos")
    
    df = load_data()
    
    if df is None or df.empty:
        st.error("❌ Nenhum gasto encontrado!")
        return
    
    # Estatísticas gerais
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📊 Total de Registros", len(df))
    with col2:
        st.metric("💰 Total Gasto", f"R$ {df['valor'].sum():,.2f}")
    with col3:
        st.metric("📅 Primeiro Registro", df['data'].min().strftime('%d/%m/%Y'))
    with col4:
        st.metric("📅 Último Registro", df['data'].max().strftime('%d/%m/%Y'))
    
    st.markdown("---")
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    
    with col1:
        categorias_hist = st.multiselect(
            "Filtrar por Categoria:",
            options=sorted(df['categoria'].unique()),
            default=df['categoria'].unique()
        )
    
    with col2:
        if 'forma_pagamento' in df.columns:
            pagamentos_hist = st.multiselect(
                "Forma de Pagamento:",
                options=sorted(df['forma_pagamento'].unique()),
                default=df['forma_pagamento'].unique()
            )
        else:
            pagamentos_hist = []
    
    with col3:
        periodo_hist = st.selectbox(
            "Período:",
            ["Todos", "Últimos 30 dias", "Últimos 90 dias", "Este ano"]
        )
    
    # Aplicar filtros
    df_filtrado = df[df['categoria'].isin(categorias_hist)]
    
    if pagamentos_hist and 'forma_pagamento' in df.columns:
        df_filtrado = df_filtrado[df_filtrado['forma_pagamento'].isin(pagamentos_hist)]
    
    # Filtro por período
    if periodo_hist != "Todos":
        hoje = pd.Timestamp.now()
        if periodo_hist == "Últimos 30 dias":
            data_limite = hoje - pd.Timedelta(days=30)
        elif periodo_hist == "Últimos 90 dias":
            data_limite = hoje - pd.Timedelta(days=90)
        elif periodo_hist == "Este ano":
            data_limite = pd.Timestamp(hoje.year, 1, 1)
        
        df_filtrado = df_filtrado[df_filtrado['data'] >= data_limite]
    
    # Ordenar por data
    df_filtrado = df_filtrado.sort_values('data', ascending=False)
    
    st.subheader(f"📊 Exibindo {len(df_filtrado)} registros")
    
    # Paginação
    registros_por_pagina = st.selectbox("Registros por página:", [10, 25, 50])
    
    if len(df_filtrado) > registros_por_pagina:
        total_paginas = (len(df_filtrado) // registros_por_pagina) + 1
        pagina = st.number_input("Página:", 1, total_paginas, 1)
        
        inicio = (pagina - 1) * registros_por_pagina
        fim = inicio + registros_por_pagina
        df_exibir = df_filtrado.iloc[inicio:fim]
        
        st.write(f"Página {pagina} de {total_paginas}")
    else:
        df_exibir = df_filtrado
    
    # Formatar para exibição
    df_display = df_exibir.copy()
    df_display['data'] = df_display['data'].dt.strftime('%d/%m/%Y')
    df_display['valor'] = df_display['valor'].apply(lambda x: f"R$ {x:,.2f}")
    
    st.dataframe(df_display, use_container_width=True, hide_index=True)
    
    # Download
    if not df_filtrado.empty:
        csv = df_filtrado.to_csv(index=False)
        st.download_button(
            label="📥 Download dos Dados (CSV)",
            data=csv,
            file_name=f'gastos_{datetime.now().strftime("%Y%m%d_%H%M")}.csv',
            mime='text/csv'
        )

def show_relatorios():
    """Página de relatórios avançados"""
    st.title("📈 Relatórios Avançados")
    
    df = load_data()
    
    if df is None or df.empty:
        st.error("❌ Nenhum dado para gerar relatórios!")
        return
    
    analyzer = DataAnalyzer(df)
    
    # Relatório mensal
    st.subheader("📅 Gastos Mensais por Categoria")
    try:
        fig_mensal = analyzer.criar_grafico_mensal()
        st.plotly_chart(fig_mensal, use_container_width=True)
    except Exception as e:
        st.error(f"Erro ao gerar gráfico mensal: {e}")
    
    st.markdown("---")
    
    # Comparativo por forma de pagamento
    if 'forma_pagamento' in df.columns:
        st.subheader("💳 Gastos por Forma de Pagamento")
        pagamento_gastos = analyzer.gastos_por_forma_pagamento()
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig_pagamento = px.pie(
                values=pagamento_gastos.values,
                names=pagamento_gastos.index,
                title="Distribuição por Forma de Pagamento"
            )
            st.plotly_chart(fig_pagamento, use_container_width=True)
        
        with col2:
            st.write("**Resumo por Forma de Pagamento:**")
            pagamento_resumo = pd.DataFrame({
                'Total (R$)': pagamento_gastos.values,
                'Percentual (%)': (pagamento_gastos.values / pagamento_gastos.sum() * 100).round(1)
            }, index=pagamento_gastos.index)
            st.dataframe(pagamento_resumo.sort_values('Total (R$)', ascending=False))
    
    st.markdown("---")
    
    # Resumo estatístico
    st.subheader("📊 Resumo Estatístico")
    stats = analyzer.get_estatisticas_basicas()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("💸 Gasto Total", f"R$ {stats.get('total_gastos', 0):,.2f}")
        st.metric("📊 Total de Transações", stats.get('total_transacoes', 0))
    
    with col2:
        st.metric("📈 Gasto Médio", f"R$ {stats.get('media_gastos', 0):.2f}")
        st.metric("🎯 Gasto Mediano", f"R$ {stats.get('mediana_gastos', 0):.2f}")
    
    with col3:
        st.metric("🔝 Maior Gasto", f"R$ {stats.get('maior_gasto', 0):,.2f}")
        st.metric("🔻 Menor Gasto", f"R$ {stats.get('menor_gasto', 0):.2f}")

# === ROTEAMENTO COMPLETO COM FINANCEBOT ===
if page == "📊 Dashboard":
    show_dashboard()
elif page == "➕ Novo Gasto":
    show_cadastro()
elif page == "📋 Histórico":
    show_historico()
elif page == "📈 Relatórios":
    show_relatorios()
elif page == "🤖 FinanceBot":  # ← ESTA LINHA ESTAVA FALTANDO!
    st.sidebar.info("🤖 Carregando FinanceBot...")
    if CHAT_AVAILABLE:
        try:
            show_chat_interface()
        except Exception as e:
            st.error(f"❌ Erro ao executar FinanceBot: {str(e)}")
            st.code(traceback.format_exc())
            st.info("💡 Verifique se configurou GROQ_API_KEY no arquivo .env")
    else:
        st.error("❌ FinanceBot não está disponível")
        st.info("💡 Verifique os logs de erro na sidebar")

# Footer
st.markdown("---")
st.markdown("**💰 Controle de Gastos | Desenvolvido com ❤️ usando Streamlit + Python | Maurício Brescianini Marques**")