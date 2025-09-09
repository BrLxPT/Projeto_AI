import os
import importlib
import json
import re
import platform
from .ollama_helper import OllamaAPI
from .security import validate_command # Importa a função de validação # Importa a função de validação
import logging # Importar o módulo logging
from flask import Flask, request, jsonify

# Configure logging para core.py
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__) # Definir a variável logger

class TaskEngine:
    def __init__(self):
        self.ollama = OllamaAPI()
        logger.info("🚀 TaskEngine iniciado") # Esta mensagem será mantida
        self.plugins = self.load_plugins()
        self.capabilities = self.generate_capabilities_list()

    def load_plugins(self):
        plugins = {}
        # logger.info(f"🔍 Procurando plugins na pasta: {os.path.abspath('plugins')}") # Removido/Comentado
    
        for file in os.listdir("backend/plugins"):
            # logger.info(f" - Encontrado: {file}") # Removido/Comentado
            if file.endswith(".py") and file != "__init__.py":
                try:
                    module_name = file[:-3]
                    # logger.info(f"🔄 Tentando carregar {module_name}...") # Removido/Comentado
                    module = importlib.import_module(f".plugins.{module_name}", package="backend")
                    plugin_data = module.register()
                    # logger.info(f"✅ Plugin registrado: {plugin_data['name']}") # Removido/Comentado
                    plugins[plugin_data["name"]] = plugin_data
                except Exception as e:
                    logger.error(f"❌ Falha ao carregar {file}: {str(e)}") # Mantido para depuração de erros
    
        # logger.info(f"📋 Plugins carregados: {list(plugins.keys())}") # Removido/Comentado
        return plugins

    def generate_capabilities_list(self):
        """
        Gera uma lista detalhada das capacidades (plugins e suas ações)
        para passar ao modelo de linguagem.
        """
        capabilities = []
        for p in self.plugins.values():
            # Inclui as ações e seus parâmetros para que o LLM saiba o que pode fazer
            plugin_cap = {
                "name": p.get("name", "unknown"),
                "description": p.get("description", ""),
                "actions": {} # Adiciona um dicionário para as ações
            }
            if "actions" in p:
                for action_name, action_data in p["actions"].items():
                    plugin_cap["actions"][action_name] = {
                        "description": action_data.get("description", ""),
                        "parameters": action_data.get("parameters", {})
                    }
            capabilities.append(plugin_cap)
        return capabilities

    def execute_task(self, user_input_or_command):
        # Se o comando vier como uma string, a primeira coisa é gerar o comando JSON
        if isinstance(user_input_or_command, str):
            command = self.generate_command(user_input_or_command)
        else:
            command = user_input_or_command

        # Se a geração do comando falhou, retorna o erro
        if isinstance(command, dict) and command.get("status") == "error":
            return command
        
        # **A VALIDAÇÃO DE SEGURANÇA VEM AQUI AGORA**
        if not validate_command(command): # Agora a validação recebe um dicionário
            logger.warning(f"🚫 Comando não autorizado: {command}")
            return {"status": "error", "message": "🚫 Comando não autorizado"}
        
        # Se for uma cadeia de comandos, executa cada um
        if command.get("action") == "chain":
            results = [self.execute_single_task(task) for task in command.get("tasks", [])]
            return {"status": "success", "results": results}
        else:
            # Caso contrário, executa uma única tarefa
            return self.execute_single_task(command)

    def generate_command(self, user_input):
        """
        Gera um comando JSON para uma ferramenta usando o modelo de linguagem,
        com base no input do utilizador e nas capacidades disponíveis.
        """
        # O prompt agora usa self.capabilities para ter a lista completa de ações
        prompt = f"""
        USER REQUEST: {user_input}
        AVAILABLE TOOLS AND THEIR ACTIONS: {json.dumps(self.capabilities, ensure_ascii=False, indent=2)}

        Generate ONLY a JSON object representing the tool action to perform, or a "text_response" if no tool is applicable.

        JSON Format for Tool Action:
        {{
            "action": "tool_action_name",
            "parameters": {{
                "param1": "value1",
                "param2": "value2"
            }}
        }}

        JSON Format for Text Response:
        {{
            "status": "text_response",
            "message": "Your text response here."
        }}

        If the user explicitly asks to shutdown or restart the PC, ensure the 'confirm' parameter is set to 'true' only if they explicitly state "now", "without asking", or similar. Otherwise, set it to 'false' to require confirmation.

        Examples:
        - User: "Desliga o meu computador" -> {{"action": "shutdown_pc", "parameters": {{"confirm": false}}}}
        - User: "Desliga o computador agora" -> {{"action": "shutdown_pc", "parameters": {{"confirm": true}}}}
        - User: "Manda um email para joao@exemplo.com com o assunto reunião e o corpo olá joão" -> {{"action": "send_email", "parameters": {{"to": "joao@exemplo.com", "subject": "reunião", "body": "olá joão"}}}}
        - User: "Qual a previsão do tempo?" -> {{"status": "text_response", "message": "Não consigo verificar a previsão do tempo no momento."}}
        """

        try:
            raw_ollama_response = self.ollama.generate(
                model="llama3", # Ou o modelo que estiver a usar
                prompt=prompt,
                format="json", # Peça sempre JSON para comandos de ferramenta
                temperature=0.0 # Use temperatura baixa para comandos precisos e determinísticos
            )
            
            # **CORREÇÃO AQUI:** Verifica se a resposta do Ollama é um erro de API (como timeout)
            if isinstance(raw_ollama_response, dict) and raw_ollama_response.get("status") == "error":
                logger.error(f"Ollama API retornou um erro: {raw_ollama_response.get('message', 'Erro desconhecido')}")
                return {"status": "error", "message": f"Erro do LLM: {raw_ollama_response.get('message', 'Erro desconhecido')}"}

            # Se não for um erro de API, assume que a resposta contém a chave 'response'
            if isinstance(raw_ollama_response, dict) and "response" in raw_ollama_response:
                llm_text_response = raw_ollama_response["response"]
            else:
                # Fallback se a chave 'response' estiver faltando (pode ser um formato inesperado)
                llm_text_response = str(raw_ollama_response) 
                logger.warning(f"Resposta inesperada do Ollama (sem chave 'response'): {llm_text_response[:100]}...")

            json_data = self._extract_json(llm_text_response)
            
            # Tenta carregar o JSON extraído
            command = json.loads(json_data)
            return command
            
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao analisar JSON do Ollama: {e}. Texto extraído: {json_data[:200]}... Resposta bruta original: {raw_ollama_response}")
            return {"status": "error", "message": f"Erro de formato da resposta do LLM: {str(e)}"}
        except Exception as e:
            logger.error(f"Erro inesperado ao gerar comando: {str(e)}")
            return {"status": "error", "message": f"Erro inesperado ao gerar comando: {str(e)}"}

    def _extract_json(self, text):
        """Extrai JSON de texto marcado ou não marcado"""
        try:
            # Tenta encontrar blocos de código JSON ```json ... ```
            blocos = re.findall(r"```(?:json)?\s*([\s\S]*?)```", text)
            if blocos:
                return blocos[0].strip()
            
            # Se não encontrar blocos de código, tenta encontrar o primeiro objeto JSON
            json_match = re.search(r"\{[\s\S]*\}", text)
            if json_match:
                return json_match.group(0)
                
            # Se nada for encontrado, retorna o texto original (pode causar erro de JSON.loads)
            return text.strip()
        except Exception as e:
            logger.error(f"Erro ao extrair JSON de texto: {str(e)}. Texto: {text[:200]}...")
            return "{}" # Retorna um JSON vazio para evitar mais erros

    def execute_single_task(self, command):
        if not isinstance(command, dict) or "action" not in command:
            return {"status": "error", "message": "Comando inválido: formato incorreto ou faltando 'action'."}

        # logger.info(f"🔍 Plugins disponíveis para execução: {list(self.plugins.keys())}") # Removido/Comentado
        
        # Encontrar a ação em qualquer plugin
        action_found = None
        for plugin_name, plugin_data in self.plugins.items():
            if "actions" in plugin_data and command["action"] in plugin_data["actions"]:
                action_found = plugin_data["actions"][command["action"]]
                # logger.info(f"✅ Ação '{command['action']}' encontrada no plugin '{plugin_name}'.") # Removido/Comentado
                break
        
        if not action_found:
            return {"status": "error", "message": f"Ação '{command['action']}' não encontrada em nenhum plugin carregado."}
        
        # Verificação explícita da função execute
        if not callable(action_found.get("execute")):
            return {"status": "error", "message": f"Função 'execute' não encontrada ou inválida na ação '{command['action']}' do plugin."}
        
        # Execução com tratamento de erros
        try:
            # Passa os parâmetros para a função execute do plugin
            result = action_found["execute"](command.get("parameters", {}))
            return {"status": "success", "result": result}
        except Exception as e:
            logger.error(f"Erro ao executar a ação '{command['action']}': {str(e)}") # Mantido para depuração de erros
            return {"status": "error", "message": str(e)}
        
task_engine_instance = TaskEngine()

app = Flask(__name__)

@app.route('/api/ask', methods=['POST'])
def ask_ollie():
    data = request.get_json()
    user_query = data.get('query')
    if not user_query:
        return jsonify({"error": "Nenhuma consulta fornecida."}), 400

    result = task_engine_instance.execute_task(user_query)

    # Adapta a resposta para o formato JSON esperado pelo frontend
    if result.get("status") == "text_response":
        return jsonify({"message": result.get("message", "Sem resposta da IA.")})
    elif result.get("status") == "success":
        return jsonify({"message": f"Comando executado com sucesso: {result.get('result', '')}"})
    else:
        return jsonify({"message": f"Erro: {result.get('message', 'Erro desconhecido')}"})

if __name__ == '__main__':
    # A porta padrão é 5000, pode ser alterada se necessário
    app.run(debug=True, port=int(os.environ.get("PORT", 5000)))

