import os
import importlib
import json
import re
import platform
from ollama_helper import OllamaAPI
from security import validate_command

class TaskEngine:
    def __init__(self):
        self.ollama = OllamaAPI()
        print("🚀 TaskEngine iniciado")
        self.plugins = self.load_plugins()
        self.capabilities = self.generate_capabilities_list()

    def load_plugins(self):
        plugins = {}
        print("🔍 Procurando plugins na pasta:", os.path.abspath("plugins"))
    
        for file in os.listdir("plugins"):
            print(" - Encontrado:", file)
            if file.endswith(".py") and file != "__init__.py":
                try:
                    module_name = file[:-3]
                    print(f"🔄 Tentando carregar {module_name}...")
                    module = importlib.import_module(f"plugins.{module_name}")
                    plugin_data = module.register()
                    print(f"✅ Plugin registrado: {plugin_data['name']}")
                    plugins[plugin_data["name"]] = plugin_data
                except Exception as e:
                    print(f"❌ Falha ao carregar {file}: {str(e)}")
    
        print("📋 Plugins carregados:", list(plugins.keys()))
        return plugins

    def generate_capabilities_list(self):
        capabilities = []
        for p in self.plugins.values():
            cap = {
                "name": p.get("name", "unknown"),
                "description": p.get("description", ""),
                "parameters": p.get("parameters", {})
            }
            capabilities.append(cap)
        return capabilities

    def execute_task(self, user_input_or_command):
        if not validate_command(user_input_or_command):
            return {"status": "error", "message": "🚫 Comando não autorizado"}

        if isinstance(user_input_or_command, str):
            command = self.generate_command(user_input_or_command)
        else:
            command = user_input_or_command

        if isinstance(command, dict) and command.get("status") == "error":
            return command
            
        if command.get("action") == "chain":
            results = [self.execute_single_task(task) for task in command.get("tasks", [])]
            return {"status": "success", "results": results}
        else:
            return self.execute_single_task(command)

    def generate_command(self, user_input):
        prompt = f"""
        USER REQUEST: {user_input}
        AVAILABLE CAPABILITIES: {json.dumps(self.capabilities, ensure_ascii=False)}

        Gere SOMENTE um JSON com:
        - 'action': nome da ação ou 'chain'
        - 'parameters': {{...}}
        - 'tasks': [] (se 'chain')
        - 'confirm': true/false

        Formato:
        {{
            "action": "nome_plugin",
            "parameters": {{...}},
            "confirm": false
        }}
        """

        try:
            response = self.ollama.generate(
                model="llama3",
                prompt=prompt,
                format="json",
                temperature=0.7
            )
            
            if isinstance(response, dict) and "response" in response:
                json_data = self._extract_json(response["response"])
            else:
                json_data = self._extract_json(str(response))
                
            return json.loads(json_data)
        except Exception as e:
            print("❌ Erro ao gerar comando:", e)
            return {"status": "error", "message": str(e)}

    def _extract_json(self, text):
        """Extrai JSON de texto marcado ou não marcado"""
        try:
            blocos = re.findall(r"```(?:json)?\s*([\s\S]*?)```", text)
            if blocos:
                return blocos[0].strip()
            
            json_match = re.search(r"\{[\s\S]*\}", text)
            if json_match:
                return json_match.group(0)
                
            return text.strip()
        except Exception as e:
            print("❌ Erro ao extrair JSON:", e)
            return "{}"

    def execute_single_task(self, command):
        if not isinstance(command, dict) or "action" not in command:
            return {"status": "error", "message": "Comando inválido"}

        plugin = self.plugins.get(command["action"])
        if not plugin:
            return {"status": "error", "message": f"Ação {command['action']} não encontrada"}
        
        if command.get("confirm"):
            confirm = input(f"⚠️ Confirmar ação perigosa? ({command['action']}) [y/N]: ")
            if confirm.lower() != "y":
                return {"status": "cancelled", "message": "Ação cancelada pelo usuário"}
        
        try:
            result = plugin["execute"](command.get("parameters", {}))
            return {"status": "success", "result": result}
        except Exception as e:
            return {"status": "error", "message": str(e)}