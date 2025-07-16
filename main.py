from http.server import SimpleHTTPRequestHandler, HTTPServer
from utils.task_ai import TaskAI
from typing import Dict, Any
import json
import os
import requests
import logging


ai = TaskAI()

class CustomHandler(SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/api/chat':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)
            
            response = ai.process_request(data.get('message', ''))
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'response': response}).encode())
        else:
            super().do_GET()

    def do_GET(self):
        if self.path == '/':
            self.path = '/templates/index.html'
        elif self.path.startswith('/static/'):
            self.path = self.path[1:]  # Remove a barra inicial
        super().do_GET()

class ActionExecutor:
    """Executor de ações com integração a APIs"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.api_endpoints = {
            'weather':{
                'url': 'https://api.openweathermap.org/data/2.5/weather',
                'params': {'units': 'metric', 'appid': 'SUA_CHAVE_API'}
            },
            'crypto':{
                'url': 'https://api.coingecko.com/api/v3/simple/price',
                'params': {'vs_currencies': 'usd'}
            },
            'calendar': {
                'url': 'http://localhost:8000/api/calendar',  # Exemplo local
                'headers': {'Content-Type': 'application/json'}
            }
        }
    
    def execute_api_call(self, api_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Executa chamada genérica a API"""
        if api_name not in self.api_endpoints:
            return {"error": f"API {api_name} não configurada"}
        
        config = self.api_endpoints[api_name]
        try:
            if api_name == 'weather':
                params = {**config['params'], 'q': params['location']}
                response = requests.get(config['url'], params=params)
            elif api_name == 'crypto':
                params = {**config['params'], 'ids': params['coin']}
                response = requests.get(config['url'], params=params)
            elif api_name == 'calendar':
                response = requests.post(
                    config['url'],
                    json=params,
                    headers=config.get('headers', {})
                )
            
            response.raise_for_status()
            return response.json()
        
        except Exception as e:
            self.logger.error(f"Erro na API {api_name}: {str(e)}")
            return {"error": str(e)}

    def execute(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executa uma ação com tratamento padronizado
        
        Args:
            action: {
                "type": "api_call"|"script"|"composite",
                "api": nome da API (se aplicável),
                "params": parâmetros para a ação
            }
        """
        action_type = action.get('type')
        
        if action_type == 'api_call':
            return self._execute_api_action(action)
        elif action_type == 'script':
            return self._execute_script_action(action)
        else:
            return {"error": f"Tipo de ação não suportado: {action_type}"}
    
    def _execute_api_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Executa ação de chamada a API"""
        required = ['api', 'params']
        if not all(k in action for k in required):
            return {"error": f"Parâmetros obrigatórios faltando: {required}"}
        
        result = self.execute_api_call(action['api'], action['params'])
        
        if 'error' in result:
            return {
                "status": "error",
                "message": f"Falha na API {action['api']}: {result['error']}"
            }
        
        return {
            "status": "success",
            "data": result,
            "message": f"Ação {action['api']} realizada"
        }

    def _execute_script_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Executa scripts locais"""
        # Implementação similar à anterior para scripts
        pass

def run_server():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    print("Servidor rodando em http://localhost:8000")
    server = HTTPServer(('0.0.0.0', 8000), CustomHandler)
    server.serve_forever()

if __name__ == "__main__":
    run_server()