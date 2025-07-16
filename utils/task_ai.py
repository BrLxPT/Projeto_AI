"""
TaskAI modificado para usar Ollama como principal
"""

from utils.ollama_client import ollama_client as oc
from utils.actions import ActionExecutor
from utils.rules_engine import RulesEngine
from utils.json_parser import parse_user_request
import logging

class TaskAI:
    def __init__(self):
        """Inicializa com Ollama como backend principal"""
        self.logger = logging.getLogger(__name__)
        self.actions = ActionExecutor()
        self.rules_engine = RulesEngine()
        
        # Verifica conexão com Ollama
        self.ollama_available = self._check_ollama()
        
        if self.ollama_available:
            self.logger.info("Ollama conectado com sucesso")
            self.logger.info(f"Modelos disponíveis: {oc.list_models()}")
        else:
            self.logger.warning("Ollama não disponível, usando fallback")

    def _check_ollama(self) -> bool:
        """Verifica se o Ollama está disponível"""
        try:
            return bool(oc.list_models())
        except:
            return False

    def process_request(self, user_input: str) -> str:
        """
        Processa solicitação priorizando Ollama
        
        Args:
            user_input: Texto de entrada do usuário
            
        Returns:
            Resposta gerada
        """
        # Primeiro tenta entender a intenção
        parsed = parse_user_request(user_input)
        
        # Se for comando muito simples, responde diretamente
        if self._is_simple_command(user_input):
            return self._handle_simple_commands(user_input)
            
        # Se Ollama disponível, usa como principal
        if self.ollama_available:
            return oc.generate_response(
                prompt=f"""Você é um assistente AI. Responda de forma concisa.
                
                Solicitação: {user_input}
                
                Contexto: {self._get_context(parsed)}""",
                temperature=0.7
            )
            
        # Fallback para regras básicas
        if self.rules_engine:
            if rule := self.rules_engine.match_rule(parsed):
                return self.actions.execute(rule['action'], parsed)
                
        return "Desculpe, não consegui processar sua solicitação."

    def _get_context(self, parsed_request: dict) -> str:
        """Gera contexto para o prompt do Ollama"""
        if parsed_request['intent'] == 'unknown':
            return "Intenção não reconhecida"
            
        return f"Intenção detectada: {parsed_request['intent']}"

    def _is_simple_command(self, text: str) -> bool:
        """Identifica comandos muito simples"""
        return text.lower().strip() in ('oi', 'olá', 'ola', 'oi', 'ok')

    def _handle_simple_commands(self, text: str) -> str:
        """Responde a comandos básicos sem usar Ollama"""
        text = text.lower().strip()
        if text in ('oi', 'olá', 'ola'):
            return "Olá! Como posso ajudar?"
        return "Entendido!"