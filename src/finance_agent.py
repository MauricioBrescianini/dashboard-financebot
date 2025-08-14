import os
import json
from datetime import datetime, date, timedelta
import pytz
from typing import List, Dict, Any
import pandas as pd
from dotenv import load_dotenv
import re
from data_collector import DataCollector
from analyzer import DataAnalyzer
from memory_manager import FinanceBotMemory

load_dotenv()

class FinanceBot:
    """
    FinanceBot com Sistema de Memória Inteligente e Consulta Dinâmica
    """
    
    def __init__(self):
        try:
            print("🤖 Inicializando FinanceBot com memória...")
            self.api_key = os.getenv('GROQ_API_KEY')
            if not self.api_key:
                raise ValueError("❌ GROQ_API_KEY não encontrada")
            
            print(f"🔑 API Key encontrada: {self.api_key[:20]}...")
            
            # Configurar timezone Brasil
            self.timezone = pytz.timezone('America/Sao_Paulo')
            
            # Importar e criar cliente Groq direto
            from groq import Groq
            self.client = Groq(api_key=self.api_key)
            self.data_collector = DataCollector()
            
            # Sistema de Memória
            self.memory = FinanceBotMemory()
            
            self.chat_history = []
            
            print("✅ FinanceBot inicializado com SUCESSO!")
        except Exception as e:
            print(f"❌ Erro: {e}")
            raise

    def _get_current_time(self):
        """Retorna horário atual no timezone do Brasil"""
        return datetime.now(self.timezone)

    def _parse_date_query(self, message: str) -> Dict[str, Any]:
        """Extrai informações de data da mensagem do usuário"""
        message_lower = message.lower().strip()
        now = self._get_current_time()
        
        # Detectar mês e ano específicos - sem caracteres especiais
        months_pt = {
            'janeiro': 1, 'jan': 1,
            'fevereiro': 2, 'fev': 2,
            'marco': 3, 'mar': 3,  # sem acento para evitar problemas
            'abril': 4, 'abr': 4,
            'maio': 5, 'mai': 5,
            'junho': 6, 'jun': 6,
            'julho': 7, 'jul': 7,
            'agosto': 8, 'ago': 8,
            'setembro': 9, 'set': 9,
            'outubro': 10, 'out': 10,
            'novembro': 11, 'nov': 11,
            'dezembro': 12, 'dez': 12
        }
        
        # Padrão: mês de ano (ex: "janeiro de 2024")
        for month_name, month_num in months_pt.items():
            if f"{month_name} de 2024" in message_lower or f"{month_name}/2024" in message_lower:
                return {
                    'type': 'specific_month',
                    'month': month_num,
                    'year': 2024,
                    'description': f"{month_name.capitalize()} de 2024"
                }
        
        # Padrão: MM/YYYY (ex: "01/2024")
        import re
        pattern = r"(\d{1,2})/(\d{4})"
        match = re.search(pattern, message_lower)
        if match:
            month = int(match.group(1))
            year = int(match.group(2))
            if 1 <= month <= 12:
                months_names = ['', 'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
                            'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
                return {
                    'type': 'specific_month',
                    'month': month,
                    'year': year,
                    'description': f"{months_names[month]} de {year}"
                }
        
        # Default: mês atual
        return {
            'type': 'current_month',
            'month': now.month,
            'year': now.year,
            'description': 'este mês'
        }

    
    def _query_expenses_by_period(self, period_info: Dict[str, Any]) -> pd.DataFrame:
        """Consulta gastos no banco para o período solicitado"""
        try:
            df = self.data_collector.load_from_database()
            if df.empty:
                return df

            period_type = period_info.get('type')

            if period_type == 'specific_month':
                month = period_info.get('month')
                year = period_info.get('year')
                filtered = df[(df['data'].dt.month == month) & (df['data'].dt.year == year)]
                return filtered

            elif period_type == 'current_month':
                now = self._get_current_time()
                filtered = df[(df['data'].dt.month == now.month) & (df['data'].dt.year == now.year)]
                return filtered

            elif period_type == 'last_month':
                month = period_info.get('month')
                year = period_info.get('year')
                filtered = df[(df['data'].dt.month == month) & (df['data'].dt.year == year)]
                return filtered

            elif period_type == 'last_7_days':
                now = self._get_current_time()
                seven_days_ago = now - timedelta(days=7)
                filtered = df[df['data'] >= seven_days_ago.date()]
                return filtered

            elif period_type == 'current_year':
                year = period_info.get('year')
                filtered = df[df['data'].dt.year == year]
                return filtered

            else:
                return df

        except Exception as e:
            print(f"❌ Erro ao consultar gastos por período: {e}")
            return pd.DataFrame()

    
    def _get_financial_advice(self) -> str:
        """Conselhos financeiros personalizados de forma natural"""
        # Atualizar memória
        self.memory.update_memory()
        
        categoria_dominante = self.memory.user_profile.get('categoria_favorita', '')
        media_mensal = self.memory.user_profile.get('media_mensal', 0)
        
        if categoria_dominante == 'Alimentação':
            advice = "Vejo que você gasta bastante com alimentação. Uma dica que funciona muito bem é cozinhar mais em casa - pode economizar até 40%! "
            advice += "Também vale fazer uma lista antes de ir ao supermercado para não comprar por impulso."
            
            if media_mensal > 1000:
                meta = media_mensal * 0.15
                advice += f"\n\nUma meta legal seria economizar uns R$ {meta:.0f} por mês, que dá {meta*12:.0f} reais no ano!"
                
        elif categoria_dominante == 'Transporte':
            advice = "Seus maiores gastos são com transporte. Que tal considerar alternativas como transporte público, bike ou até carona compartilhada? "
            advice += "Se usar carro próprio, manter ele sempre revisado ajuda a economizar combustível."
            
        elif categoria_dominante == 'Lazer':
            advice = "Vi que você gosta de se divertir, o que é super importante! Uma dica é definir um valor fixo por mês para lazer. "
            advice += "Assim você se diverte sem comprometer o orçamento. Também dá para explorar atividades gratuitas na cidade."
            
        else:
            advice = "Algumas dicas que sempre funcionam:\n\n"
            advice += "• A regra 50/30/20: 50% para necessidades, 30% para desejos, 20% para poupança\n"
            advice += "• Esperar 24 horas antes de fazer compras acima de R$ 100\n"
            advice += "• Revisar os gastos toda semana para manter o controle"
        
        return advice
    
    def _add_expense(self, valor: float, categoria: str, descricao: str) -> str:
        """Cadastra novo gasto com resposta simples"""
        try:
            if valor <= 0:
                return "O valor precisa ser maior que zero."
            
            # Mapear categorias
            categoria_map = {
                "comida": "Alimentação", "food": "Alimentação", "supermercado": "Alimentação",
                "gasolina": "Transporte", "uber": "Transporte", "onibus": "Transporte",
                "cinema": "Lazer", "streaming": "Lazer", "diversão": "Lazer",
                "médico": "Saúde", "farmacia": "Saúde", "remedio": "Saúde"
            }
            
            categoria_final = categoria_map.get(categoria.lower(), categoria)
            if categoria_final not in ["Alimentação", "Transporte", "Lazer", "Saúde", "Roupas", "Mensalidades", "Outros"]:
                categoria_final = "Outros"
            
            novo_gasto = pd.DataFrame([{
                'data': date.today(),
                'valor': float(valor),
                'categoria': categoria_final,
                'descricao': descricao,
                'forma_pagamento': 'FinanceBot'
            }])
            
            success = self.data_collector.insert_new_expense(novo_gasto)
            
            if success:
                # Atualizar memória
                self.memory.update_memory()
                
                # Resposta simples
                data_hoje = date.today().strftime('%d/%m')
                
                if descricao != "Gasto via FinanceBot":
                    response = f"✅ Registrado: R$ {valor:,.2f} em {categoria_final} ({descricao}) - {data_hoje}"
                else:
                    response = f"✅ Registrado: R$ {valor:,.2f} em {categoria_final} - {data_hoje}"
                
                # Dica simples baseada no valor
                if valor > 200:
                    response += "\n\n💡 Gasto alto! Quer ver o total do mês?"
                elif valor < 20:
                    response += "\n\n👍 Continue registrando os pequenos gastos!"
                
                return response
            else:
                return "❌ Não consegui salvar. Tente novamente."
        except Exception as e:
            return f"❌ Erro ao salvar: {str(e)}"

    def _generate_dynamic_analysis(self, user_message: str) -> str:
        """Gera análise dinâmica com formatação limpa e otimizada"""
        try:
            # Função utilitária para converter para float
            def safe_float(value):
                try:
                    return float(value)
                except:
                    if hasattr(value, 'iloc'):
                        return float(value.iloc[0])
                    elif isinstance(value, (list, tuple)) and len(value) > 0:
                        return float(value)
                    else:
                        return 0.0
            
            # Extrair informações de período da mensagem
            period_info = self._parse_date_query(user_message)
            
            # Consultar dados do período
            df_period = self._query_expenses_by_period(period_info)
            
            period_description = period_info.get('description', 'período solicitado')
            
            if df_period.empty:
                return f"Não encontrei gastos registrados para {period_description}.\n\nQue tal cadastrar alguns gastos? Posso te ajudar! 😊"
            
            # Análise detalhada dos dados encontrados
            analyzer = DataAnalyzer(df_period)
            stats = analyzer.get_estatisticas_basicas()
            categoria_gastos = analyzer.gastos_por_categoria()
            
            # Resposta limpa e formatada
            total = safe_float(stats['total_gastos'])
            transacoes = int(stats['total_transacoes'])
            media = safe_float(stats['media_gastos'])
            
            # Resposta principal - identificar o mês correto
            if "01/2024" in period_description or "janeiro" in period_description.lower():
                response = f"Em janeiro de 2024 você gastou R$ {total:.2f} no total."
            elif "02/2024" in period_description or "fevereiro" in period_description.lower():
                response = f"Em fevereiro de 2024 você gastou R$ {total:.2f} no total."
            elif "03/2024" in period_description or "março" in period_description.lower():
                response = f"Em março de 2024 você gastou R$ {total:.2f} no total."
            else:
                response = f"Em {period_description} você gastou R$ {total:.2f} no total."
            
            # Informações sobre transações - simplificada
            if transacoes == 1:
                response += " Foi apenas 1 transação."
            else:
                response += f" Foram {transacoes} transações (média R$ {media:.2f} cada)."
            
            # Mostrar apenas as 2 principais categorias
            if not categoria_gastos.empty:
                categorias_ordenadas = categoria_gastos.sort_values(ascending=False)
                
                # Primeira categoria (principal)
                categoria_principal = categorias_ordenadas.index[0]
                valor_principal = safe_float(categorias_ordenadas.iloc)
                percentual_principal = (valor_principal / total) * 100
                
                response += f"\n\nPrincipal categoria: {categoria_principal} - R$ {valor_principal:.2f} ({percentual_principal:.0f}%)"
                
                # Segunda categoria (apenas se significativa)
                if len(categorias_ordenadas) > 1:
                    segunda_categoria = categorias_ordenadas.index[1]
                    segundo_valor = safe_float(categorias_ordenadas.iloc[1])
                    segundo_percentual = (segundo_valor / total) * 100
                    
                    # Só mostrar se for pelo menos 10% do total
                    if segundo_percentual >= 10:
                        response += f"\nSegunda maior: {segunda_categoria} - R$ {segundo_valor:.2f} ({segundo_percentual:.0f}%)"
            
            # Dica personalizada simples
            if total > 4000:
                response += "\n\n💡 Mês com gastos altos. Considere revisar o orçamento."
            elif total > 2000:
                response += "\n\n👍 Gastos dentro da média. Continue acompanhando!"
            else:
                response += "\n\n✅ Mês econômico! Parabéns pelo controle."
            
            return response
            
        except Exception as e:
            return f"Não consegui analisar os dados. Tente novamente."



    def _generate_dynamic_analysis(self, user_message: str) -> str:
        """Gera análise dinâmica baseada na consulta do usuário"""
        try:
            # Função utilitária para converter para float
            def safe_float(value):
                try:
                    return float(value)
                except:
                    if hasattr(value, 'iloc'):
                        return float(value.iloc[0])
                    elif isinstance(value, (list, tuple)) and len(value) > 0:
                        return float(value)
                    else:
                        return 0.0
            
            # Extrair informações de período da mensagem
            period_info = self._parse_date_query(user_message)
            
            # Consultar dados do período
            df_period = self._query_expenses_by_period(period_info)
            
            period_description = period_info.get('description', 'período solicitado')
            
            if df_period.empty:
                return f"""Não encontrei nenhum gasto registrado para {period_description}.

    Que tal cadastrar seus gastos desse período? Posso ajudar você a fazer isso! 😊"""
            
            # Análise detalhada dos dados encontrados
            analyzer = DataAnalyzer(df_period)
            stats = analyzer.get_estatisticas_basicas()
            categoria_gastos = analyzer.gastos_por_categoria()
            
            # Resposta humanizada - convertendo valores para float
            total = safe_float(stats['total_gastos'])
            transacoes = int(stats['total_transacoes'])
            media = safe_float(stats['media_gastos'])
            
            # Início da resposta natural
            if period_description == "01/2024" or "janeiro" in period_description.lower():
                response = f"Em janeiro de 2024 você gastou **R$ {total:,.2f}** no total."
            else:
                response = f"Em {period_description} você gastou **R$ {total:,.2f}** no total."
            
            # Adicionar contexto sobre número de transações
            if transacoes == 1:
                response += f" Foi apenas 1 transação."
            else:
                response += f" Foram {transacoes} transações, com média de R$ {media:.2f} por gasto."
            
            # Mostrar distribuição por categoria de forma natural
            if not categoria_gastos.empty:
                categorias_ordenadas = categoria_gastos.sort_values(ascending=False)
                categoria_principal = categorias_ordenadas.index[0]
                valor_principal = safe_float(categorias_ordenadas.iloc)
                percentual_principal = (valor_principal / total) * 100
                
                response += f"\n\nO que mais pesou foi **{categoria_principal}** com R$ {valor_principal:,.2f} ({percentual_principal:.0f}% do total)."
                
                # Mostrar outras categorias se houver mais de uma
                if len(categorias_ordenadas) > 1:
                    outras_categorias = []
                    for categoria, valor in categorias_ordenadas.iloc[1:].items():
                        valor_float = safe_float(valor)
                        percentual = (valor_float / total) * 100
                        if percentual >= 10:  # Só mostrar se for relevante (>=10%)
                            outras_categorias.append(f"{categoria} R$ {valor_float:,.2f}")
                    
                    if outras_categorias:
                        if len(outras_categorias) == 1:
                            response += f" Também teve {outras_categorias[0]}."
                        else:
                            outras_str = ", ".join(outras_categorias[:-1]) + f" e {outras_categorias[-1]}"
                            response += f" Também teve {outras_str}."
            
            # Mostrar o maior gasto se for significativo
            maior_gasto = safe_float(stats['maior_gasto'])
            if maior_gasto > media * 2:  # Só mencionar se for bem acima da média
                top_gastos = analyzer.get_top_gastos(1)
                if not top_gastos.empty:
                    gasto = top_gastos.iloc[0]
                    data_gasto = gasto['data'].strftime('%d/%m')
                    response += f"\n\nO maior gasto foi R$ {maior_gasto:,.2f} em {gasto['categoria']} no dia {data_gasto}."
            
            # Insight personalizado da memória (se houver)
            alerts = self.memory.user_profile.get('alertas_ativos', [])
            recommendations = self.memory.user_profile.get('recomendacoes', [])
            
            if alerts:
                alert = alerts[0]  # Pegar só o primeiro alerta
                if "concentrado" in alert.lower():
                    response += f"\n\n💡 {alert}"
            
            if recommendations and len(recommendations) > 0:
                rec = recommendations  # Pegar só a primeira recomendação
                response += f"\n\n{rec}"
            
            return response
            
        except Exception as e:
            return f"Tive um problema para analisar seus gastos: {str(e)}"


    def _call_groq(self, message: str, system_prompt: str = None) -> str:
        """Chama a API do Groq diretamente com contexto da memória"""
        try:
            # Limpar mensagem de caracteres especiais
            clean_message = message.encode('ascii', 'ignore').decode('ascii')
            
            messages = []
            
            # Contexto com timezone correto
            current_time = self._get_current_time().strftime('%d/%m/%Y %H:%M:%S')
            
            if system_prompt:
                # Enriquecer prompt do sistema com dados da memória
                user_context = self.memory.get_personalized_context()
                enhanced_prompt = f"""{system_prompt}

                CONTEXTO TEMPORAL:
                Data/Hora atual (Brasil): {current_time}

                {user_context}

                IMPORTANTE: Use SEMPRE os dados reais do banco de dados. Formate números como R$ XXX.XX sem caracteres especiais."""
                messages.append({"role": "system", "content": enhanced_prompt})
            
            # Adicionar histórico recente
            for msg in self.chat_history[-4:]:
                messages.append(msg)
            
            # Adicionar mensagem atual limpa
            messages.append({"role": "user", "content": clean_message})
            
            completion = self.client.chat.completions.create(
                messages=messages,
                model="llama-3.1-8b-instant",
                temperature=0.3,
                max_tokens=1000
            )
            
            return completion.choices[0].message.content
        except Exception as e:
            return f"Erro na chamada da API: {str(e)}"

    def chat(self, message: str) -> str:
        """Processa mensagem com consulta dinâmica aos dados"""
        try:
            # Adicionar mensagem do usuário ao histórico
            self.chat_history.append({"role": "user", "content": message})
            
            # Atualizar memória
            self.memory.update_memory()
            
            message_lower = message.lower()
            
            # Detectar se é uma consulta sobre gastos/análise
            analysis_keywords = [
                'quanto', 'gastei', 'gasto', 'gastos', 'análise', 'analise',
                'resumo', 'relatório', 'janeiro', 'fevereiro', 'março', 'abril',
                'maio', 'junho', 'julho', 'agosto', 'setembro', 'outubro',
                'novembro', 'dezembro', 'mês', 'ano', 'período', '2024', '2025'
            ]
            
            is_analysis_query = any(keyword in message_lower for keyword in analysis_keywords)
            
            if is_analysis_query:
                # Gerar análise dinâmica baseada nos dados reais
                result = self._generate_dynamic_analysis(message)
            else:
                # Processar normalmente com classificação de intenção
                intent_prompt = f"""Analise a mensagem do usuário e determine a ação:

                MENSAGEM: "{message}"

                AÇÕES POSSÍVEIS:
                1. CADASTRAR_GASTO - se menciona gastar dinheiro com algo
                2. ANALISAR_GASTOS - se pede análise, relatório ou resumo dos gastos
                3. CONSELHOS - se pede dicas, conselhos ou ajuda financeira
                4. CONVERSAR - para outras mensagens

                FORMATO DE RESPOSTA:
                - Se CADASTRAR_GASTO: ACAO:CADASTRAR|VALOR:XX|CATEGORIA:YY|DESCRICAO:ZZ
                - Se outra ação: ACAO:NOME_DA_ACAO

                Responda apenas a classificação:"""

                intent_response = self._call_groq(intent_prompt)
                
                if "ACAO:CADASTRAR" in intent_response:
                    # Processar cadastro de gasto
                    try:
                        parts = intent_response.split("|")
                        valor_str = [p for p in parts if p.startswith("VALOR:")][0].replace("VALOR:", "")
                        categoria_parts = [p for p in parts if p.startswith("CATEGORIA:")]
                        descricao_parts = [p for p in parts if p.startswith("DESCRICAO:")]
                        
                        categoria = categoria_parts[0].replace("CATEGORIA:", "") if categoria_parts else "Outros"
                        descricao = descricao_parts.replace("DESCRICAO:", "") if descricao_parts else "Gasto via FinanceBot"
                        
                        valor_match = re.findall(r'\d+(?:[.,]\d+)?', valor_str)
                        if valor_match:
                            valor = float(valor_match[0].replace(',', '.'))
                        else:
                            valor = 0.0
                        
                        result = self._add_expense(valor, categoria, descricao)
                    except Exception as ex:
                        result = f"❌ Erro ao extrair dados: {str(ex)}. Tente: 'Gastei X reais com Y'"
                        
                elif "ACAO:ANALISAR_GASTOS" in intent_response:
                    result = self._generate_dynamic_analysis(message)
                    
                elif "ACAO:CONSELHOS" in intent_response:
                    result = self._get_financial_advice()
                    
                else:
                    # Conversa normal
                    system_prompt = f"""Você é o FinanceBot, um assistente financeiro amigável e prestativo.

                    PERSONALIDADE:
                    - Amigável e encorajador
                    - Usa emojis naturalmente
                    - Fala português brasileiro
                    - Foca em educação financeira
                    - USA SEMPRE dados reais do banco de dados

                    IMPORTANTE: 
                    - Nunca invente dados financeiros
                    - Consulte sempre os dados reais do usuário
                    - Use o horário correto do Brasil (timezone: America/Sao_Paulo)

                    Seja sempre motivador e ofereça ajuda prática baseada nos dados reais! 💰"""

                    result = self._call_groq(message, system_prompt)
            
            # Adicionar resposta ao histórico
            self.chat_history.append({"role": "assistant", "content": result})
            
            # Manter histórico limitado
            if len(self.chat_history) > 10:
                self.chat_history = self.chat_history[-10:]
            
            return result
        except Exception as e:
            error_msg = f"❌ Erro ao processar: {str(e)}"
            self.chat_history.append({"role": "assistant", "content": error_msg})
            return error_msg

    # ... resto dos métodos permanecem iguais
