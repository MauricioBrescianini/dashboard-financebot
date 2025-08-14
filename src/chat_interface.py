import streamlit as st
from finance_agent import FinanceBot
from datetime import datetime
import traceback
import os

def show_chat_interface():
    """Interface de chat com o FinanceBot - VERSÃO SEM LOOP"""
    st.title("💬 Chat com FinanceBot")
    st.markdown("🤖 Seu assistente financeiro pessoal!")
    
    # Verificar se já existe agente na sessão
    if 'finance_bot' not in st.session_state:
        try:
            with st.spinner("🤖 Inicializando FinanceBot..."):
                st.session_state.finance_bot = FinanceBot()
            st.success("✅ FinanceBot inicializado com sucesso!")
        except Exception as e:
            st.error(f"❌ Erro ao inicializar FinanceBot: {str(e)}")
            with st.expander("🔧 Diagnóstico Completo", expanded=True):
                st.code(f"Erro: {str(e)}")
                st.code(traceback.format_exc())
                
                # Verificações de ambiente
                st.write("**🔍 Verificações:**")
                groq_key = os.getenv('GROQ_API_KEY')
                if groq_key:
                    st.write("✅ GROQ_API_KEY configurada")
                else:
                    st.write("❌ GROQ_API_KEY não encontrada")
                
                # Banco de dados
                try:
                    from data_collector import DataCollector
                    collector = DataCollector()
                    st.write("✅ Conexão com banco OK")
                except:
                    st.write("❌ Problema na conexão com banco")
                
                st.info("""
                **💡 Soluções:**
                1. Verifique se GROQ_API_KEY está no arquivo .env
                2. Execute: `docker-compose restart dashboard`
                3. Confirme se PostgreSQL está rodando
                """)
            return
    
    # Inicializar histórico de chat
    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = []
        
        # Mensagem de boas-vindas APENAS uma vez
        welcome_message = """👋 **Olá! Eu sou o FinanceBot!**

🤖 **Posso ajudar você com:**
- 📊 **Analisar seus gastos** por período  
- ➕ **Cadastrar novos gastos** via chat
- 💡 **Dar conselhos financeiros** personalizados
- 💰 **Criar orçamentos** baseados no seu histórico

✨ **Exemplos do que você pode falar:**
- *"Gastei 50 reais com alimentação hoje"*
- *"Como estão meus gastos este mês?"*
- *"Me dê dicas para economizar"*
- *"Analise meus gastos dos últimos 7 dias"*

Como posso ajudar você hoje? 😊"""
        
        st.session_state.chat_messages.append({
            "role": "assistant",
            "content": welcome_message,
            "timestamp": datetime.now()
        })

    # Inicializar flag de processamento
    if 'processing_message' not in st.session_state:
        st.session_state.processing_message = False
    
    # Container do chat - exibir mensagens
    chat_container = st.container()
    
    with chat_container:
        for message in st.session_state.chat_messages:
            timestamp = message.get('timestamp', datetime.now()).strftime('%H:%M')
            
            if message["role"] == "user":
                st.markdown(f"""
                <div style='display: flex; justify-content: flex-end; margin: 10px 0;'>
                    <div style='background-color: #0066cc; color: white; padding: 10px; border-radius: 10px; max-width: 70%; word-wrap: break-word;'>
                        <strong>Você ({timestamp}):</strong><br>
                        {message["content"]}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style='display: flex; justify-content: flex-start; margin: 10px 0;'>
                    <div style='background-color: #f0f0f0; color: black; padding: 10px; border-radius: 10px; max-width: 70%; word-wrap: break-word;'>
                        <strong>🤖 FinanceBot ({timestamp}):</strong><br>
                        {message["content"]}
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    # Separador
    st.markdown("---")
    
    # Input do usuário - usar form para controlar melhor
    with st.form(key="chat_form", clear_on_submit=True):
        col1, col2, col3 = st.columns([6, 1, 1])
        
        with col1:
            user_input = st.text_input(
                "Digite sua mensagem:",
                placeholder="Ex: Gastei 30 reais com almoço hoje...",
                key="user_message_input"
            )
        
        with col2:
            send_button = st.form_submit_button("📤 Enviar")
        
        with col3:
            clear_button = st.form_submit_button("🗑️ Limpar")
    
    # Processar mensagem - EVITAR LOOP
    if send_button and user_input.strip() and not st.session_state.processing_message:
        # Marcar como processando para evitar loops
        st.session_state.processing_message = True
        
        # Adicionar mensagem do usuário
        st.session_state.chat_messages.append({
            "role": "user",
            "content": user_input.strip(),
            "timestamp": datetime.now()
        })
        
        # Obter resposta do bot
        with st.spinner("🤖 Pensando..."):
            try:
                response = st.session_state.finance_bot.chat(user_input.strip())
                st.session_state.chat_messages.append({
                    "role": "assistant", 
                    "content": response,
                    "timestamp": datetime.now()
                })
            except Exception as e:
                error_response = f"❌ Erro ao processar: {str(e)}"
                st.session_state.chat_messages.append({
                    "role": "assistant",
                    "content": error_response,
                    "timestamp": datetime.now()
                })
        
        # Resetar flag de processamento
        st.session_state.processing_message = False
        
        # Recarregar a página APENAS UMA VEZ
        st.rerun()
    
    # Limpar histórico
    if clear_button:
        st.session_state.chat_messages = []
        if 'finance_bot' in st.session_state:
            st.session_state.finance_bot.clear_history()
        st.session_state.processing_message = False
        st.rerun()
    
    # Estatísticas na sidebar
    if len(st.session_state.chat_messages) > 1:
        st.sidebar.markdown("### 💬 Estatísticas do Chat")
        st.sidebar.metric("Mensagens", len(st.session_state.chat_messages))
        st.sidebar.metric("Conversas do usuário", 
                         len([m for m in st.session_state.chat_messages if m["role"] == "user"]))
