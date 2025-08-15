import streamlit as st
import pandas as pd
from data_collector import DataCollector
from analyzer import DataAnalyzer
from datetime import datetime, date
import plotly.express as px
import plotly.graph_objects as go
import traceback

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
    """Dashboard principal REDESENHADO - Interface moderna e intuitiva"""
    
    # 🎯 HEADER PRINCIPAL COM DESTAQUE
    st.markdown("""
    <div style="background: linear-gradient(90deg, #1f4068 0%, #2d5a87 100%); 
                padding: 3rem 2rem; margin: -1rem -1rem 2rem -1rem; 
                border-radius: 15px; text-align: center; color: white;">
        <h1 style="margin: 0; font-size: 3rem; font-weight: 700;">💰 Dashboard Financeiro</h1>
        <p style="margin: 0.5rem 0 0 0; font-size: 1.2rem; opacity: 0.9;">
            Controle inteligente dos seus gastos com análise em tempo real
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Carregar dados
    df = load_data()
    if df is None or df.empty:
        st.error("❌ Não foi possível carregar os dados!")
        return

    # Filtros na sidebar
    st.sidebar.header("🔍 Filtros")
    
    # Filtro por período
    periodo = st.sidebar.selectbox(
        "📅 Período:",
        ["Últimos 30 dias", "Últimos 7 dias", "Este mês", "Últimos 3 meses", "Este ano", "Todos"],
        index=0
    )
    
    # Filtro por categoria
    categorias = st.sidebar.multiselect(
        "🏷️ Categorias:",
        options=sorted(df['categoria'].unique()),
        default=df['categoria'].unique()
    )
    
    # Aplicar filtros
    df_filtrado = df[df['categoria'].isin(categorias)]
    
    # Filtro por período
    if periodo != "Todos":
        hoje = pd.Timestamp.now()
        if periodo == "Últimos 7 dias":
            data_limite = hoje - pd.Timedelta(days=7)
        elif periodo == "Últimos 30 dias":
            data_limite = hoje - pd.Timedelta(days=30)
        elif periodo == "Este mês":
            data_limite = pd.Timestamp(hoje.year, hoje.month, 1)
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

    # 🎯 MÉTRICAS PRINCIPAIS - CARDS DESTACADOS
    st.markdown("### 📈 Resumo Financeiro")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_gastos = stats.get('total_gastos', 0)
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 1.5rem; border-radius: 15px; text-align: center; color: white; margin-bottom: 1rem;">
            <h3 style="margin: 0; font-size: 1.1rem; opacity: 0.9;">💸 Total Gasto</h3>
            <h2 style="margin: 0.5rem 0 0 0; font-size: 2rem; font-weight: bold;">
                R$ {total_gastos:,.2f}
            </h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        total_transacoes = stats.get('total_transacoes', 0)
        media_gastos = stats.get('media_gastos', 0)
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
                    padding: 1.5rem; border-radius: 15px; text-align: center; color: white; margin-bottom: 1rem;">
            <h3 style="margin: 0; font-size: 1.1rem; opacity: 0.9;">📊 Transações</h3>
            <h2 style="margin: 0.5rem 0 0 0; font-size: 2rem; font-weight: bold;">
                {total_transacoes}
            </h2>
            <p style="margin: 0.2rem 0 0 0; font-size: 0.9rem; opacity: 0.8;">
                Média: R$ {media_gastos:.2f}
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        categoria_top = stats.get('categoria_mais_gasta', 'N/A')
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); 
                    padding: 1.5rem; border-radius: 15px; text-align: center; color: white; margin-bottom: 1rem;">
            <h3 style="margin: 0; font-size: 1.1rem; opacity: 0.9;">🏆 Categoria Top</h3>
            <h2 style="margin: 0.5rem 0 0 0; font-size: 1.5rem; font-weight: bold;">
                {categoria_top}
            </h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        maior_gasto = stats.get('maior_gasto', 0)
        menor_gasto = stats.get('menor_gasto', 0)
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); 
                    padding: 1.5rem; border-radius: 15px; text-align: center; color: white; margin-bottom: 1rem;">
            <h3 style="margin: 0; font-size: 1.1rem; opacity: 0.9;">💰 Maior Gasto</h3>
            <h2 style="margin: 0.5rem 0 0 0; font-size: 1.6rem; font-weight: bold;">
                R$ {maior_gasto:.2f}
            </h2>
            <p style="margin: 0.2rem 0 0 0; font-size: 0.9rem; opacity: 0.8;">
                Menor: R$ {menor_gasto:.2f}
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # 🎯 GRÁFICOS PRINCIPAIS - LAYOUT OTIMIZADO
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 📈 Evolução dos Gastos no Tempo")
        try:
            gastos_diarios = df_filtrado.groupby('data')['valor'].sum().reset_index()
            
            fig_linha = px.line(
                gastos_diarios,
                x='data',
                y='valor',
                title='',
                labels={'valor': 'Valor (R$)', 'data': 'Data'},
                color_discrete_sequence=['#667eea']
            )
            
            fig_linha.update_layout(
                height=400,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#333'),
                xaxis=dict(showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.1)'),
                yaxis=dict(showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.1)')
            )
            
            fig_linha.update_traces(
                line=dict(width=3),
                hovertemplate='<b>%{x}</b><br>R$ %{y:,.2f}<extra></extra>'
            )
            
            st.plotly_chart(fig_linha, use_container_width=True)
        except Exception as e:
            st.error(f"Erro ao criar gráfico de linha: {e}")
    
    with col2:
        st.markdown("### 🥧 Distribuição por Categoria")
        try:
            categoria_gastos = analyzer.gastos_por_categoria()
            
            colors = ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe', '#00f2fe', '#fa709a', '#fee140']
            
            fig_pizza = px.pie(
                values=categoria_gastos.values,
                names=categoria_gastos.index,
                title='',
                color_discrete_sequence=colors
            )
            
            fig_pizza.update_layout(
                height=400,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#333'),
                showlegend=True,
                legend=dict(
                    orientation="v",
                    yanchor="middle",
                    y=0.5,
                    xanchor="left",
                    x=1.05
                )
            )
            
            fig_pizza.update_traces(
                textposition='inside',
                textinfo='percent',
                hovertemplate='<b>%{label}</b><br>R$ %{value:,.2f}<br>%{percent}<extra></extra>'
            )
            
            st.plotly_chart(fig_pizza, use_container_width=True)
        except Exception as e:
            st.error(f"Erro ao criar gráfico de pizza: {e}")

    # 🎯 SEÇÃO DE INSIGHTS
    st.markdown("### 🎯 Insights e Recomendações")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 💸 Maiores Gastos do Período")
        top_gastos = analyzer.get_top_gastos(5)
        if not top_gastos.empty:
            for idx, gasto in top_gastos.iterrows():
                data_formatada = gasto['data'].strftime('%d/%m/%Y')
                st.markdown(f"""
                <div style="background: #f8f9fa; padding: 1rem; margin: 0.5rem 0; 
                           border-radius: 10px; border-left: 4px solid #667eea;">
                    <strong>R$ {gasto['valor']:,.2f}</strong> - {gasto['categoria']}<br>
                    <small style="color: #666;">{gasto['descricao']} • {data_formatada}</small>
                </div>
                """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("#### 📊 Resumo por Categoria")
        categoria_resumo = df_filtrado.groupby('categoria').agg({
            'valor': ['sum', 'count', 'mean']
        }).round(2)
        categoria_resumo.columns = ['Total (R$)', 'Qtd', 'Média (R$)']
        categoria_resumo = categoria_resumo.sort_values('Total (R$)', ascending=False)
        
        # Exibir como cards
        for categoria, row in categoria_resumo.head().iterrows():
            percentual = (row['Total (R$)'] / total_gastos) * 100
            st.markdown(f"""
            <div style="background: #f8f9fa; padding: 1rem; margin: 0.5rem 0; 
                       border-radius: 10px; border-left: 4px solid #f5576c;">
                <strong>{categoria}</strong><br>
                <span style="color: #667eea; font-weight: bold;">R$ {row['Total (R$)']:,.2f}</span> 
                ({percentual:.1f}%)<br>
                <small style="color: #666;">{int(row['Qtd'])} gastos • Média R$ {row['Média (R$)']:.2f}</small>
            </div>
            """, unsafe_allow_html=True)

    # 🎯 CALL TO ACTION
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("➕ Adicionar Novo Gasto", use_container_width=True, type="primary"):
            st.switch_page("pages/novo_gasto.py")  # Navegar para página de novo gasto
    
    with col2:
        if st.button("🤖 Chat com FinanceBot", use_container_width=True):
            st.switch_page("pages/financebot.py")  # Navegar para chat
    
    with col3:
        if st.button("📈 Ver Relatórios Completos", use_container_width=True):
            st.switch_page("pages/relatorios.py")  # Navegar para relatórios

    # 🎯 ALERTAS E DICAS PERSONALIZADAS
    st.markdown("### 💡 Dicas Personalizadas")
    
    # Análise inteligente dos gastos
    if total_gastos > 0:
        categoria_dominante = stats.get('categoria_mais_gasta', '')
        if categoria_dominante:
            categoria_valor = df_filtrado[df_filtrado['categoria'] == categoria_dominante]['valor'].sum()
            categoria_pct = (categoria_valor / total_gastos) * 100
            
            if categoria_pct > 40:
                st.info(f"💡 **Dica:** {categoria_pct:.0f}% dos seus gastos são em {categoria_dominante}. "
                        f"Considere revisar esses gastos para encontrar oportunidades de economia!")
            
            if maior_gasto > media_gastos * 3:
                st.warning(f"⚠️ **Atenção:** Você teve um gasto de R$ {maior_gasto:.2f}, bem acima da sua média. "
                          f"Monitore gastos altos para manter o controle!")
            
            # Dica baseada no período
            if periodo == "Últimos 30 dias" and total_gastos > 3000:
                economia_sugerida = total_gastos * 0.1
                st.success(f"🎯 **Meta:** Tente economizar R$ {economia_sugerida:.2f} no próximo mês "
                          f"(10% dos gastos atuais) para melhorar sua saúde financeira!")

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
elif page == "🤖 FinanceBot":
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
st.markdown("""
<div style="text-align: center; padding: 2rem; background: #f8f9fa; 
           border-radius: 10px; margin-top: 2rem;">
    <p style="margin: 0; color: #666; font-size: 0.9rem;">
        💰 <strong>Controle de Gastos</strong> | 
        Desenvolvido com ❤️ usando Python + Streamlit + IA<br>
        <strong>Maurício Brescianini Marques</strong> | Projeto Portfolio 2024
    </p>
</div>
""", unsafe_allow_html=True)