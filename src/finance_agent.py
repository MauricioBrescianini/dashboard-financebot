import os
import json
from datetime import datetime, date, timedelta
import pytz
from typing import List, Dict, Any, Optional
import pandas as pd
from dotenv import load_dotenv
import re
from data_collector import DataCollector
from analyzer import DataAnalyzer
from memory_manager import FinanceBotMemory

load_dotenv()

class FinanceBot:
    """FinanceBot Inteligente - Usa IA para parsing e menos lógica condicional"""
    
    def __init__(self):
        self.api_key = os.getenv('GROQ_API_KEY')
        if not self.api_key:
            raise ValueError("❌ GROQ_API_KEY não encontrada")
        
        self.timezone = pytz.timezone('America/Sao_Paulo')
        
        from groq import Groq
        self.client = Groq(api_key=self.api_key)
        self.data_collector = DataCollector()
        self.memory = FinanceBotMemory()
        self.chat_history = []
        
        # Configurações do bot
        self.FINANCE_TOPICS = [
            'gastos', 'despesas', 'receitas', 'orçamento', 'economia', 'dinheiro',
            'categorias', 'análise', 'relatório', 'planejamento', 'investimento'
        ]
        
        print("✅ FinanceBot inicializado com SUCESSO!")

    def _call_groq_ai(self, prompt: str, max_tokens: int = 500) -> str:
        """Chamada simplificada para IA"""
        try:
            completion = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.1-8b-instant",
                temperature=0.3,
                max_tokens=max_tokens
            )
            return completion.choices[0].message.content
        except Exception as e:
            return f"Erro: {str(e)}"

    def _ai_parse_date(self, message: str) -> Dict[str, Any]:
        """IA analisa e extrai período da mensagem"""
        current_date = datetime.now(self.timezone).strftime('%d/%m/%Y')
        
        prompt = f"""
        Analise esta mensagem e extraia informações de período: "{message}"
        Data atual: {current_date}
        
        Retorne APENAS no formato JSON:
        {{
            "type": "specific_month|current_month|date_range|current_year",
            "month": número_mês_ou_null,
            "year": número_ano_ou_null,
            "description": "descrição_amigável"
        }}
        
        Exemplos:
        - "janeiro de 2024" → {{"type": "specific_month", "month": 1, "year": 2024, "description": "janeiro de 2024"}}
        - "01/2024" → {{"type": "specific_month", "month": 1, "year": 2024, "description": "janeiro de 2024"}}
        - "este mês" → {{"type": "current_month", "month": null, "year": null, "description": "este mês"}}
        """
        
        ai_response = self._call_groq_ai(prompt, 200)
        
        try:
            # Extrair JSON da resposta da IA
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        # Fallback para mês atual
        now = datetime.now(self.timezone)
        return {
            "type": "current_month",
            "month": now.month,
            "year": now.year,
            "description": "este mês"
        }

    def _ai_classify_intent(self, message: str) -> Dict[str, Any]:
        """IA classifica a intenção do usuário"""
        prompt = f"""
        Classifique esta mensagem financeira: "{message}"
        
        Retorne APENAS no formato JSON:
        {{
            "intent": "analyze|register|advice|chat",
            "confidence": 0.0_a_1.0,
            "data": {{"valor": null, "categoria": null, "descricao": null}}
        }}
        
        Intenções:
        - analyze: usuário quer ver/analisar gastos existentes
        - register: usuário quer cadastrar um novo gasto
        - advice: usuário quer dicas/conselhos financeiros  
        - chat: conversa geral sobre finanças
        
        Se register, extraia dados do gasto no campo "data".
        """
        
        ai_response = self._call_groq_ai(prompt, 300)
        
        try:
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        # Fallback
        return {"intent": "chat", "confidence": 0.5, "data": {}}

    def _query_expenses_by_period(self, period_info: Dict[str, Any]) -> pd.DataFrame:
        """Consulta gastos do banco baseado no período"""
        df = self.data_collector.load_from_database()
        if df.empty:
            return df
        
        period_type = period_info.get('type')
        now = datetime.now(self.timezone)
        
        filters = {
            'specific_month': lambda: (
                (df['data'].dt.month == period_info.get('month')) & 
                (df['data'].dt.year == period_info.get('year'))
            ),
            'current_month': lambda: (
                (df['data'].dt.month == now.month) & 
                (df['data'].dt.year == now.year)
            ),
            'current_year': lambda: df['data'].dt.year == period_info.get('year', now.year)
        }
        
        filter_func = filters.get(period_type, lambda: df.index >= 0)
        return df[filter_func()]

    def _generate_analysis(self, user_message: str) -> str:
        """Gera análise usando IA + dados reais"""
        try:
            # IA parseia o período solicitado
            period_info = self._ai_parse_date(user_message)
            
            # Consulta dados reais
            df_period = self._query_expenses_by_period(period_info)
            
            if df_period.empty:
                return f"Não encontrei gastos para {period_info.get('description', 'esse período')}.\n\nQue tal cadastrar alguns gastos? 😊"
            
            # Calcular métricas
            total = float(df_period['valor'].sum())
            transacoes = len(df_period)
            media = float(df_period['valor'].mean())
            
            # Top categorias
            top_categories = df_period.groupby('categoria')['valor'].sum().sort_values(ascending=False)
            
            # IA gera resposta natural baseada nos dados
            data_summary = {
                'periodo': period_info.get('description'),
                'total': total,
                'transacoes': transacoes,
                'media': media,
                'categorias': [(cat, float(val)) for cat, val in top_categories.head(3).items()]
            }
            
            ai_prompt = f"""
            Com base nestes DADOS REAIS dos gastos do usuário, gere uma análise natural e humanizada:
            
            Dados: {json.dumps(data_summary, ensure_ascii=False)}
            
            Regras:
            - Use linguagem natural e amigável
            - Destaque os pontos mais importantes
            - Inclua os valores exatos dos dados
            - Seja conciso mas informativo
            - Adicione uma dica prática ao final
            
            Formato de resposta desejado:
            "Em [período] você gastou R$ [total] no total. Foram [transacoes] transações...
            [análise das categorias principais]
            [dica personalizada]"
            """
            
            return self._call_groq_ai(ai_prompt, 600)
            
        except Exception as e:
            return f"Não consegui analisar os dados. Erro: {str(e)}"

    def _register_expense(self, expense_data: Dict) -> str:
        """Registra novo gasto no banco"""
        try:
            valor = float(expense_data.get('valor', 0))
            if valor <= 0:
                return "O valor precisa ser maior que zero."
            
            categoria = expense_data.get('categoria', 'Outros')
            descricao = expense_data.get('descricao', 'Gasto via FinanceBot')
            
            # Mapear categoria para padrão
            categoria_map = {
                'comida': 'Alimentação', 'alimentacao': 'Alimentação',
                'transporte': 'Transporte', 'uber': 'Transporte',
                'lazer': 'Lazer', 'diversao': 'Lazer',
                'saude': 'Saúde', 'medico': 'Saúde'
            }
            
            categoria_final = categoria_map.get(categoria.lower(), categoria.title())
            if categoria_final not in ["Alimentação", "Transporte", "Lazer", "Saúde", "Roupas", "Mensalidades", "Outros"]:
                categoria_final = "Outros"
            
            novo_gasto = pd.DataFrame([{
                'data': date.today(),
                'valor': valor,
                'categoria': categoria_final,
                'descricao': descricao,
                'forma_pagamento': 'FinanceBot'
            }])
            
            success = self.data_collector.insert_new_expense(novo_gasto)
            
            if success:
                self.memory.update_memory()
                data_hoje = date.today().strftime('%d/%m')
                
                # IA gera resposta personalizada
                ai_prompt = f"""
                Gere uma confirmação amigável para este gasto registrado:
                Valor: R$ {valor:.2f}
                Categoria: {categoria_final}
                Descrição: {descricao}
                Data: {data_hoje}
                
                Inclua uma dica contextual baseada no valor (se alto >200, médio 50-200, baixo <50).
                Seja conciso e motivador.
                """
                
                return self._call_groq_ai(ai_prompt, 300)
            else:
                return "❌ Não consegui salvar no banco. Tente novamente."
                
        except Exception as e:
            return f"❌ Erro ao processar: {str(e)}"

    def _get_advice(self) -> str:
        """IA gera conselhos baseados no perfil do usuário"""
        self.memory.update_memory()
        
        # Dados do perfil para IA
        profile_data = {
            'categoria_dominante': self.memory.user_profile.get('categoria_favorita', 'N/A'),
            'media_mensal': self.memory.user_profile.get('media_mensal', 0),
            'total_gastos': self.memory.user_profile.get('total_gastos', 0),
            'alertas': self.memory.user_profile.get('alertas_ativos', [])[:2],
            'recomendacoes': self.memory.user_profile.get('recomendacoes', [])[:2]
        }
        
        ai_prompt = f"""
        Com base no perfil financeiro real do usuário, gere conselhos personalizados:
        
        Perfil: {json.dumps(profile_data, ensure_ascii=False)}
        
        Gere dicas práticas e específicas baseadas nos dados reais.
        Se não há dados suficientes, dê conselhos gerais de educação financeira.
        Use linguagem amigável e motivadora.
        Máximo 4 dicas.
        """
        
        return self._call_groq_ai(ai_prompt, 500)

    def _is_finance_related(self, message: str) -> bool:
        """Verifica se mensagem é sobre finanças usando IA"""
        prompt = f"""
        Esta mensagem é sobre finanças pessoais? "{message}"
        
        Tópicos financeiros: gastos, despesas, dinheiro, orçamento, economia, investimento, poupança, cartão, banco, pagamento, receita, categoria, planejamento.
        
        Responda apenas: SIM ou NAO
        """
        
        ai_response = self._call_groq_ai(prompt, 50)
        return "SIM" in ai_response.upper()

    def _handle_off_topic(self) -> str:
        """Resposta para assuntos não financeiros"""
        responses = [
            "Sou especialista em finanças pessoais! Como posso ajudar com seus gastos ou orçamento?",
            "Prefiro focar em suas finanças. Quer analisar seus gastos?",
            "Que tal falarmos sobre como está seu controle financeiro?",
            "Minha especialidade são finanças! Posso ajudar com dicas de economia?"
        ]
        import random
        return random.choice(responses)

    def chat(self, message: str) -> str:
        """Método principal - processamento inteligente"""
        try:
            # Verificar se é sobre finanças
            if not self._is_finance_related(message):
                return self._handle_off_topic()
            
            # IA classifica intenção
            intent_result = self._ai_classify_intent(message)
            intent = intent_result.get('intent', 'chat')
            
            # Roteamento baseado na intenção
            handlers = {
                'analyze': lambda: self._generate_analysis(message),
                'register': lambda: self._register_expense(intent_result.get('data', {})),
                'advice': lambda: self._get_advice(),
                'chat': lambda: self._general_finance_chat(message)
            }
            
            handler = handlers.get(intent, handlers['chat'])
            result = handler()
            
            # Manter histórico
            self.chat_history.append({"role": "user", "content": message})
            self.chat_history.append({"role": "assistant", "content": result})
            
            # Limitar histórico
            if len(self.chat_history) > 10:
                self.chat_history = self.chat_history[-10:]
            
            return result
            
        except Exception as e:
            return f"Estou aqui para ajudar com suas finanças! Erro: {str(e)}"

    def _general_finance_chat(self, message: str) -> str:
        """Chat geral sobre finanças usando IA"""
        context = self.memory.get_personalized_context()
        current_time = datetime.now(self.timezone).strftime('%d/%m/%Y %H:%M:%S')
        
        ai_prompt = f"""
        Você é o FinanceBot, assistente financeiro amigável.
        
        Contexto do usuário:
        {context}
        
        Data/Hora atual (Brasil): {current_time}
        
        Mensagem do usuário: "{message}"
        
        Regras:
        - Responda APENAS sobre finanças pessoais
        - Use dados reais do contexto quando relevante
        - Seja amigável e motivador
        - Ofereça ajuda prática
        - Use português brasileiro
        - Máximo 3 parágrafos
        """
        
        try:
            completion = self.client.chat.completions.create(
                messages=[{"role": "system", "content": ai_prompt}],
                model="llama-3.1-8b-instant",
                temperature=0.4,
                max_tokens=400
            )
            return completion.choices[0].message.content
        except:
            return "Como posso ajudar você a controlar melhor suas finanças? 💰"

    def clear_history(self):
        """Limpa histórico de chat"""
        self.chat_history = []
