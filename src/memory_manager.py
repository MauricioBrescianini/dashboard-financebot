import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any
import json
from data_collector import DataCollector
from analyzer import DataAnalyzer

class FinanceBotMemory:
    """Sistema de memória inteligente para o FinanceBot"""
    
    def __init__(self):
        self.data_collector = DataCollector()
        self.user_profile = {}
        self.insights_cache = {}
        self.last_update = None
        self._load_user_profile()
    
    def _load_user_profile(self):
        """Carrega perfil do usuário baseado nos dados históricos"""
        try:
            df = self.data_collector.load_from_database()
            if not df.empty:
                self._analyze_spending_patterns(df)
                self.last_update = datetime.now()
        except Exception as e:
            print(f"❌ Erro ao carregar perfil: {e}")
    
    def _analyze_spending_patterns(self, df: pd.DataFrame):
        """Analisa padrões de gastos do usuário"""
        if df.empty:
            return
        
        analyzer = DataAnalyzer(df)
        stats = analyzer.get_estatisticas_basicas()
        
        # Padrões básicos
        self.user_profile = {
            'total_gastos': stats.get('total_gastos', 0),
            'media_mensal': self._get_monthly_average(df),
            'categoria_favorita': stats.get('categoria_mais_gasta', 'N/A'),
            'forma_pagamento_preferida': self._get_preferred_payment(df),
            'tendencia_gastos': self._get_spending_trend(df),
            'alertas_ativos': self._generate_spending_alerts(df, stats),
            'recomendacoes': self._generate_recommendations(df, stats)
        }
        
        # Padrões avançados
        self.insights_cache = {
            'gastos_por_categoria': analyzer.gastos_por_categoria().to_dict(),
            'gastos_recorrentes': self._identify_recurring_expenses(df),
            'metas_sugeridas': self._suggest_budget_goals(stats)
        }
    
    def _get_monthly_average(self, df: pd.DataFrame) -> float:
        """Calcula média mensal de gastos"""
        try:
            monthly_totals = df.groupby(df['data'].dt.to_period('M'))['valor'].sum()
            return monthly_totals.mean() if not monthly_totals.empty else 0.0
        except:
            return 0.0
    
    def _get_preferred_payment(self, df: pd.DataFrame) -> str:
        """Identifica forma de pagamento preferida"""
        try:
            if 'forma_pagamento' in df.columns:
                return df['forma_pagamento'].mode().iloc[0]
        except:
            pass
        return "N/A"
    
    def _get_spending_trend(self, df: pd.DataFrame) -> str:
        """Analisa tendência de gastos (crescente/decrescente)"""
        try:
            monthly_totals = df.groupby(df['data'].dt.to_period('M'))['valor'].sum()
            if len(monthly_totals) >= 2:
                recent = monthly_totals.tail(2).values
                if recent[-1] > recent[-2]:
                    return "Crescente"
                elif recent[-1] < recent[-2]:
                    return "Decrescente"
            return "Estável"
        except:
            return "Indefinido"
    
    def _generate_spending_alerts(self, df: pd.DataFrame, stats: Dict) -> List[str]:
        """Gera alertas baseados nos padrões de gastos"""
        alerts = []
        
        # Alert de gasto alto
        if stats.get('maior_gasto', 0) > stats.get('media_gastos', 0) * 3:
            alerts.append("⚠️ Detectado gasto atípico muito alto")
        
        # Alert de categoria dominante
        categoria_gastos = df.groupby('categoria')['valor'].sum()
        if not categoria_gastos.empty:
            max_categoria = categoria_gastos.max()
            total = categoria_gastos.sum()
            if max_categoria / total > 0.6:
                categoria_dominante = categoria_gastos.idxmax()
                alerts.append(f"📊 Gastos concentrados em {categoria_dominante} ({max_categoria/total*100:.1f}%)")
        
        return alerts
    
    def _generate_recommendations(self, df: pd.DataFrame, stats: Dict) -> List[str]:
        """Gera recomendações personalizadas"""
        recommendations = []
        
        # Recomendações baseadas na categoria dominante
        categoria_dominante = stats.get('categoria_mais_gasta', '')
        if categoria_dominante == 'Alimentação':
            recommendations.append("🍽️ Considere cozinhar mais em casa para economizar")
            recommendations.append("📝 Faça listas de compras para evitar gastos desnecessários")
        elif categoria_dominante == 'Lazer':
            recommendations.append("🎯 Defina um orçamento mensal para entretenimento")
            recommendations.append("🏠 Explore atividades gratuitas ou de baixo custo")
        elif categoria_dominante == 'Transporte':
            recommendations.append("🚗 Considere alternativas de transporte mais econômicas")
            recommendations.append("⛽ Monitore o consumo de combustível")
        
        return recommendations
    
    def _identify_recurring_expenses(self, df: pd.DataFrame) -> List[Dict]:
        """Identifica gastos recorrentes"""
        try:
            recurring = []
            for categoria in df['categoria'].unique():
                cat_df = df[df['categoria'] == categoria]
                value_counts = cat_df['valor'].value_counts()
                frequent_values = value_counts[value_counts >= 2]
                
                for valor in frequent_values.index:
                    occurrences = len(cat_df[cat_df['valor'] == valor])
                    recurring.append({
                        'categoria': categoria,
                        'valor': valor,
                        'frequencia': occurrences,
                        'ultima_ocorrencia': cat_df[cat_df['valor'] == valor]['data'].max()
                    })
            
            return sorted(recurring, key=lambda x: x['frequencia'], reverse=True)[:5]
        except:
            return []
    
    def _suggest_budget_goals(self, stats: Dict) -> Dict:
        """Sugere metas de orçamento"""
        total = stats.get('total_gastos', 0)
        if total == 0:
            return {}
        
        return {
            'meta_economia_mensal': total * 0.1 / 12,  # 10% de economia anual
            'meta_categoria_limite': stats.get('media_gastos', 0) * 1.5,  # 150% da média
            'meta_emergencia': total * 0.05  # 5% para emergências
        }
    
    def get_personalized_context(self) -> str:
        """Gera contexto personalizado para o bot"""
        if not self.user_profile:
            return "Usuário novo, sem histórico de gastos."
        
        context_parts = [
            f"📊 PERFIL FINANCEIRO DO USUÁRIO:",
            f"• Total gasto: R$ {self.user_profile.get('total_gastos', 0):,.2f}",
            f"• Média mensal: R$ {self.user_profile.get('media_mensal', 0):,.2f}",
            f"• Categoria preferida: {self.user_profile.get('categoria_favorita', 'N/A')}",
            f"• Forma de pagamento: {self.user_profile.get('forma_pagamento_preferida', 'N/A')}",
            f"• Tendência: {self.user_profile.get('tendencia_gastos', 'N/A')}"
        ]
        
        # Adicionar alertas
        alerts = self.user_profile.get('alertas_ativos', [])
        if alerts:
            context_parts.append("\n🚨 ALERTAS:")
            context_parts.extend([f"• {alert}" for alert in alerts[:3]])
        
        # Adicionar recomendações
        recommendations = self.user_profile.get('recomendacoes', [])
        if recommendations:
            context_parts.append("\n💡 RECOMENDAÇÕES ATIVAS:")
            context_parts.extend([f"• {rec}" for rec in recommendations[:3]])
        
        return "\n".join(context_parts)
    
    def update_memory(self):
        """Atualiza a memória com dados mais recentes"""
        if self.last_update is None or datetime.now() - self.last_update > timedelta(hours=1):
            self._load_user_profile()
    
    def get_contextual_advice(self, user_message: str) -> str:
        """Gera conselhos contextuais baseados na mensagem e perfil"""
        self.update_memory()
        
        message_lower = user_message.lower()
        
        # Conselhos específicos baseados no contexto
        if 'economizar' in message_lower or 'poupar' in message_lower:
            return self._get_saving_advice()
        elif 'orçamento' in message_lower:
            return self._get_budget_advice()
        
        return ""
    
    def _get_saving_advice(self) -> str:
        """Conselhos de economia baseados no perfil"""
        categoria_dominante = self.user_profile.get('categoria_favorita', '')
        media_mensal = self.user_profile.get('media_mensal', 0)
        
        advice = "💰 DICAS DE ECONOMIA PERSONALIZADAS:\n\n"
        
        if categoria_dominante == 'Alimentação':
            advice += "🍽️ Suas maiores oportunidades de economia:\n"
            advice += "• Cozinhe mais em casa (economia de até 40%)\n"
            advice += "• Compre em atacado produtos não perecíveis\n"
            advice += "• Use aplicativos de desconto em restaurantes\n"
        elif categoria_dominante == 'Transporte':
            advice += "🚗 Suas maiores oportunidades de economia:\n"
            advice += "• Considere transporte público ou bike\n"
            advice += "• Compartilhe caronas quando possível\n"
            advice += "• Mantenha o veículo sempre revisado\n"
        
        if media_mensal > 1000:
            advice += f"\n🎯 Meta sugerida: economizar R$ {media_mensal * 0.15:.2f}/mês (15%)"
        
        return advice
    
    def _get_budget_advice(self) -> str:
        """Conselhos de orçamento personalizados"""
        advice = "📋 ORÇAMENTO PERSONALIZADO:\n\n"
        advice += "Baseado no seu perfil, sugiro:\n"
        
        for categoria, valor in self.insights_cache.get('gastos_por_categoria', {}).items():
            percentual = (valor / self.user_profile.get('total_gastos', 1)) * 100
            advice += f"• {categoria}: R$ {valor:,.2f} ({percentual:.1f}%)\n"
        
        return advice
