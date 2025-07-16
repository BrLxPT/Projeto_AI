"""
Cliente Ollama melhorado para integração com o projeto
"""

import requests
import logging
from typing import Optional

class OllamaClient:
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3"):
        """
        Inicializa o cliente Ollama
        
        Args:
            base_url: URL da API Ollama
            model: Modelo padrão para uso
        """
        self.base_url = base_url
        self.model = model
        self.logger = logging.getLogger(__name__)
        
    def generate_response(self, prompt: str, model: Optional[str] = None, **kwargs) -> str:
        """
        Gera resposta usando o Ollama
        
        Args:
            prompt: Texto de entrada
            model: Modelo alternativo (opcional)
            **kwargs: Parâmetros adicionais (temperature, top_p, etc.)
            
        Returns:
            Resposta gerada pelo modelo
        """
        model = model or self.model
        endpoint = f"{self.base_url}/api/generate"
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            **kwargs
        }
        
        try:
            response = requests.post(endpoint, json=payload)
            response.raise_for_status()
            return response.json()["response"]
        except Exception as e:
            self.logger.error(f"Erro ao gerar resposta: {str(e)}")
            return f"Erro ao consultar o Ollama: {str(e)}"

    def list_models(self) -> list:
        """Lista modelos disponíveis localmente"""
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            return [model['name'] for model in response.json()['models']]
        except Exception as e:
            self.logger.error(f"Erro ao listar modelos: {str(e)}")
            return []

# Instância global para importação
ollama_client = OllamaClient()