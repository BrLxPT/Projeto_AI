"""
Módulo json_parser.py - Responsável por analisar e interpretar entradas do usuário
"""

import re
import json
from typing import Dict, Any

class JSONParser:
    """Classe principal para análise de entradas do usuário"""
    
    def __init__(self):
        """Inicializa o parser com padrões de regex"""
        self.patterns = {
            'weather': r'(clima|tempo|previsão).*(em|para|na|no)\s*(.+)',
            'crypto': r'(preço|valor|cotação).*(do|da)\s*(.+)'
        }
    
    def parse_user_request(self, input_text: str) -> Dict[str, Any]:
        """
        Analisa o texto de entrada do usuário e extrai intenção e parâmetros
        
        Args:
            input_text: Texto inserido pelo usuário
            
        Returns:
            Dicionário com:
            - 'intent': Intenção detectada
            - 'parameters': Parâmetros extraídos
        """
        input_text = input_text.lower().strip()
        
        # Verifica padrão de clima
        weather_match = re.search(self.patterns['weather'], input_text)
        if weather_match:
            return {
                "intent": "check_weather",
                "parameters": {"location": weather_match.group(3).strip()}
            }
        
        # Verifica padrão de criptomoeda
        crypto_match = re.search(self.patterns['crypto'], input_text)
        if crypto_match:
            return {
                "intent": "get_crypto_price",
                "parameters": {"coin": crypto_match.group(3).strip()}
            }
        
        # Padrão não reconhecido
        return {
            "intent": "unknown",
            "parameters": {"raw_input": input_text}
        }

# Cria uma instância global para importação
json_parser = JSONParser()

# Função de conveniência para importação
def parse_user_request(input_text: str) -> Dict[str, Any]:
    """Função pública para análise de requisições"""
    return json_parser.parse_user_request(input_text)