import os
import importlib
import json
from ollama_helper import ask_ollama
from security import validate_command
import platform

class TaskEngine:
    def __init__(self):
        self.plugins = self.load_plugins()
        self.capabilities = self.generate_capabilities_list()

    def load_plugins(self):
        plugins = {}
        for file in os.listdir("plugins"):
            if file.endswith(".py") and file != "__init__.py":
                if file == "hardware_control.py" and platform.system() != "Linux":
                    print("⚠️ Ignorando plugin de hardware: não estamos em Linux/Raspberry Pi")
                    continue
                module_name = file[:-3]
                module = importlib.import_module(f"plugins.{module_name}")
                plugins[module_name] = module.register()
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


    def execute_task(self, user_input):
        # Validar permissões
        if not validate_command(user_input):
            return "🚫 Comando não autorizado"

        # Gerar comando estruturado
        command = self.generate_command(user_input)
        
        # Executar ação
        if command["action"] == "chain":
            results = [self.execute_single_task(task) for task in command["tasks"]]
            return {"status": "success", "results": results}
        else:
            return self.execute_single_task(command)

    def generate_command(self, user_input):
        prompt = f"""
        USER REQUEST: {user_input}
        AVAILABLE CAPABILITIES: {json.dumps(self.capabilities)}
        
        Generate JSON response with:
        - 'action': Action name or 'chain' for multiple
        - 'tasks': [array of actions] (if chained)
        - 'parameters': {{key: value}}
        - 'confirm': true/false (if dangerous)
        
        Examples:
        {{"action": "email_send", "parameters": {{"to": "user@ex.com", "subject": "Hello", "body": "..."}}}}
        {{"action": "chain", "tasks": [
            {{"action": "pc_wake", "parameters": {{"mac": "01:23:45:67:89:AB"}}}},
            {{"action": "script_run", "parameters": {{"path": "/scripts/backup.py"}}}}
        ]}}
        """
        response = ask_ollama(prompt)

        print("🧪 Resposta bruta do Ollama:")
        print(response)

        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            print("❌ Erro ao converter JSON:", e)
            return {"action": "none", "error": "Resposta inválida do Ollama"}

        return json.loads(response)

    def execute_single_task(self, command):
        plugin = self.plugins.get(command["action"])
        if not plugin:
            return {"status": "error", "message": f"Action {command['action']} not found"}
        
        # Requer confirmação para ações perigosas
        if command.get("confirm"):
            confirm = input(f"⚠️ Confirmar ação perigosa? ({command['action']}) [y/N]: ")
            if confirm.lower() != "y":
                return {"status": "cancelled"}
        
        # Executar ação
        try:
            result = plugin["execute"](command["parameters"])
            return {"status": "success", "result": result}
        except Exception as e:
            return {"status": "error", "message": str(e)}

def load_plugins(self):
    plugins = {}
    for file in os.listdir("plugins"):
        if file.endswith(".py") and file != "__init__.py":
            if file == "hardware_control.py" and platform.system() != "Linux":
                print("⚠️ Ignorando plugin de hardware: não estamos em Linux/Raspberry Pi")
                continue
            module_name = file[:-3]
            module = importlib.import_module(f"plugins.{module_name}")
            plugins[module_name] = module.register()
    return plugins
