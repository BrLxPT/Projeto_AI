"""
Módulo actions.py - Responsável por executar ações no sistema AI

Este módulo contém a classe ActionExecutor que:
1. Gerencia todas as ações disponíveis no sistema
2. Integra com APIs externas
3. Executa scripts e operações locais
4. Retorna resultados padronizados para o sistema principal
"""

import importlib  # Para carregamento dinâmico de módulos
from apis import weather_api, crypto_api, calendar_api  # APIs integradas
import subprocess  # Para execução de comandos do sistema
import json  # Para manipulação de dados JSON
import logging  # Para registro de logs

# Configuração básica de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ActionExecutor:
    """
    Classe principal que executa todas as ações disponíveis no sistema
    
    Atributos:
        api_modules (dict): Dicionário com módulos de API carregados
        available_actions (list): Lista de ações disponíveis
    """
    
    def __init__(self):
        """
        Inicializa o executor de ações configurando:
        - Módulos de API padrão
        - Ações disponíveis
        - Configurações iniciais
        """
        self.api_modules = {
            'weather': weather_api,  # API de previsão do tempo
            'crypto': crypto_api,    # API de criptomoedas
            'calendar': calendar_api # API de calendário
        }
        
        # Lista de ações suportadas pelo sistema
        self.available_actions = [
            "get_weather",
            "get_crypto_price",
            "add_calendar_event",
            "run_script",
            "save_data",
            "load_data"
        ]
        
        logger.info("ActionExecutor inicializado com %d APIs e %d ações disponíveis", 
                  len(self.api_modules), len(self.available_actions))

    def execute(self, action_name, parameters):
        """
        Método principal para execução de ações
        
        Parâmetros:
            action_name (str): Nome da ação a ser executada
            parameters (dict): Parâmetros necessários para a ação
            
        Retorno:
            dict: Resultado da execução no formato:
                {
                    "status": "success"|"error",
                    "data": resultado|None,
                    "message": str
                }
        """
        logger.info("Executando ação '%s' com parâmetros: %s", action_name, str(parameters))
        
        # Verifica se a ação existe
        if action_name not in self.available_actions:
            error_msg = f"Ação '{action_name}' não reconhecida."
            logger.error(error_msg)
            return {
                "status": "error",
                "data": None,
                "message": error_msg
            }
        
        try:
            # Executa a ação correspondente
            if action_name == "get_weather":
                result = self._execute_weather_action(parameters)
            elif action_name == "get_crypto_price":
                result = self._execute_crypto_action(parameters)
            elif action_name == "add_calendar_event":
                result = self._execute_calendar_action(parameters)
            elif action_name == "run_script":
                result = self._execute_script_action(parameters)
            else:
                result = {
                    "status": "error",
                    "data": None,
                    "message": f"Ação '{action_name}' implementada mas não tratada"
                }
            
            logger.info("Ação '%s' executada com status: %s", action_name, result["status"])
            return result
            
        except Exception as e:
            error_msg = f"Erro ao executar ação '{action_name}': {str(e)}"
            logger.exception(error_msg)
            return {
                "status": "error",
                "data": None,
                "message": error_msg
            }

    def _execute_weather_action(self, params):
        """
        Executa ações relacionadas a previsão do tempo
        
        Parâmetros:
            params (dict): Deve conter:
                - location (str): Localização para consulta
                
        Retorno:
            dict: Resultado da consulta meteorológica
        """
        required = ['location']
        if not all(k in params for k in required):
            return {
                "status": "error",
                "data": None,
                "message": f"Parâmetros obrigatórios faltando: {required}"
            }
        
        # Chama a API de tempo
        data = self.api_modules['weather'].get_weather(params['location'])
        
        return {
            "status": "success",
            "data": data,
            "message": "Dados meteorológicos obtidos com sucesso"
        }

    def _execute_crypto_action(self, params):
        """
        Executa ações relacionadas a criptomoedas
        
        Parâmetros:
            params (dict): Deve conter:
                - coin (str): Nome/ID da criptomoeda
                
        Retorno:
            dict: Resultado da consulta de preço
        """
        required = ['coin']
        if not all(k in params for k in required):
            return {
                "status": "error",
                "data": None,
                "message": f"Parâmetros obrigatórios faltando: {required}"
            }
        
        # Chama a API de criptomoedas
        data = self.api_modules['crypto'].get_price(params['coin'])
        
        return {
            "status": "success",
            "data": data,
            "message": "Dados de criptomoeda obtidos com sucesso"
        }

    def _execute_calendar_action(self, params):
        """
        Executa ações relacionadas a calendário
        
        Parâmetros:
            params (dict): Deve conter:
                - title (str): Título do evento
                - date (str): Data do evento (YYYY-MM-DD)
                - time (str): Hora do evento (HH:MM)
                
        Retorno:
            dict: Resultado da operação
        """
        required = ['title', 'date', 'time']
        if not all(k in params for k in required):
            return {
                "status": "error",
                "data": None,
                "message": f"Parâmetros obrigatórios faltando: {required}"
            }
        
        # Chama a API de calendário
        result = self.api_modules['calendar'].add_event(
            params['title'],
            params['date'],
            params['time']
        )
        
        return {
            "status": "success" if result else "error",
            "data": result,
            "message": "Evento adicionado ao calendário" if result else "Falha ao adicionar evento"
        }

    def _execute_script_action(self, params):
        """
        Executa scripts externos
        
        Parâmetros:
            params (dict): Deve conter:
                - script_name (str): Nome do script (sem extensão)
                - args (list, opcional): Argumentos para o script
                
        Retorno:
            dict: Resultado da execução
        """
        required = ['script_name']
        if not all(k in params for k in required):
            return {
                "status": "error",
                "data": None,
                "message": f"Parâmetros obrigatórios faltando: {required}"
            }
        
        # Monta comando para executar o script
        cmd = ['python', f'scripts/{params["script_name"]}.py']
        
        # Adiciona argumentos se existirem
        if 'args' in params and isinstance(params['args'], list):
            cmd.extend(params['args'])
        
        try:
            # Executa o script
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            return {
                "status": "success",
                "data": {
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "returncode": result.returncode
                },
                "message": "Script executado com sucesso"
            }
        except subprocess.CalledProcessError as e:
            return {
                "status": "error",
                "data": {
                    "stdout": e.stdout,
                    "stderr": e.stderr,
                    "returncode": e.returncode
                },
                "message": f"Erro ao executar script (código {e.returncode})"
            }

    def list_actions(self):
        """
        Retorna lista de ações disponíveis
        
        Retorno:
            list: Nomes de todas as ações suportadas
        """
        return self.available_actions

    def add_custom_action(self, action_name, action_function):
        """
        Adiciona uma nova ação personalizada ao sistema
        
        Parâmetros:
            action_name (str): Nome da nova ação
            action_function (callable): Função que implementa a ação
            
        Retorno:
            bool: True se ação foi adicionada, False se já existia
        """
        if action_name in self.available_actions:
            logger.warning("Tentativa de adicionar ação já existente: %s", action_name)
            return False
        
        self.available_actions.append(action_name)
        setattr(self, f'_execute_{action_name}_action', action_function)
        logger.info("Nova ação adicionada: %s", action_name)
        return True