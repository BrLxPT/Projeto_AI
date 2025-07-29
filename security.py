# security.py
import re
import json
from typing import Dict, Any

# Lista de ações explicitamente permitidas pelo sistema.
# Estas são as ações que os plugins registam e que o LLM pode invocar.
ALLOWED_ACTIONS = [
    "send_email",
    "shutdown_pc",
    "restart_pc",
    # Adicione aqui outras ações de outros plugins conforme os for desenvolvendo
    # Ex: "turn_on_light", "get_cpu_usage", "open_browser"
]

def validate_command(command: Dict[str, Any]) -> bool:
    """
    Valida se um dado comando é autorizado para execução, combinando lista de permissões
    e lista negra de termos perigosos.
    
    Args:
        command (Dict[str, Any]): O dicionário de comando gerado pelo LLM ou diretamente.
                                   Espera-se que tenha uma chave 'action'.

    Returns:
        bool: True se o comando é autorizado, False caso contrário.
    """
    # 1. Validação de formato básico: O comando deve ser um dicionário com uma 'action'.
    if not isinstance(command, dict) or "action" not in command:
        return False

    action = command["action"]
    
    # 2. Verificação de ações permitidas (whitelist para ações de ferramenta).
    # Esta é a principal forma de permitir as ações dos plugins.
    if action not in ALLOWED_ACTIONS:
        return False

    # 3. Verificação de lista negra (blacklist) para termos perigosos.
    # Aplica a blacklist a uma representação em string do comando completo (incluindo parâmetros).
    # Isso serve como uma camada de segurança adicional.
    # Removi 'shutdown' e 'password' da blacklist principal, pois são manipulados por ações permitidas
    # ou são dados sensíveis que não devem estar em texto plano na blacklist.
    
    # Converte o comando para uma string JSON para que a regex possa procurar em todo o comando.
    command_as_string = json.dumps(command, ensure_ascii=False).lower() 

    BLACKLIST_TERMS = [
        r'rm -rf', r'format', r'delete all', # Comandos de sistema perigosos
        r'\\', # Caracteres de escape que podem indicar injeção de comando
        # Adicione outros termos que você queira bloquear em parâmetros ou comandos genéricos.
        # Ex: r'exec\s*\(', r'os\.system', r'subprocess\.run' se você quiser ser mais rigoroso
        # com a execução de código arbitrário.
    ]

    if any(re.search(pattern, command_as_string, re.IGNORECASE) for pattern in BLACKLIST_TERMS):
        return False
        
    # 4. Verificação de permissões do utilizador (se implementado).
    # Esta é uma camada adicional de segurança, se você tiver um sistema de utilizadores/papéis.
    # Por enquanto, user_has_permissions sempre retorna True.
    if not user_has_permissions(command):
        return False
            
    # 5. Se a ação for "chain", precisamos validar cada tarefa dentro da cadeia recursivamente.
    if action == "chain":
        tasks = command.get("tasks", [])
        for task in tasks:
            if not validate_command(task): # Recursivamente valida cada sub-tarefa
                return False
        return True # Todas as tarefas na cadeia são válidas

    # Se passou por todas as verificações e não é uma cadeia, o comando individual é considerado seguro.
    return True

def user_has_permissions(command: Dict[str, Any]) -> bool:
    """
    Verifica se o utilizador atual tem permissões para executar o comando.
    Esta é uma função placeholder e deve ser implementada com sua lógica de permissões real.
    
    Args:
        command (Dict[str, Any]): O comando que está a ser validado.

    Returns:
        bool: True se o utilizador tem permissão, False caso contrário.
    """
    # Exemplo de como você poderia implementar a lógica de permissões:
    # (Isto exigiria um sistema de utilizadores e papéis no seu aplicativo)
    #
    # from your_user_module import current_user # Exemplo de como obter o utilizador logado
    #
    # if command.get("action") == "shutdown_pc" and current_user.role != "admin":
    #     return False
    #
    # if command.get("action") == "send_email" and not current_user.can_send_email:
    #     return False

    return True # Temporário - sempre permite, para fins de desenvolvimento.

# Exemplo de uso (para testar diretamente este módulo)
if __name__ == "__main__":
    print("Testando security.py...")
    
    # Comando permitido (email)
    cmd_email = {"action": "send_email", "parameters": {"to": "test@example.com", "subject": "Teste", "body": "Corpo"}}
    print(f"Comando de email permitido? {validate_command(cmd_email)}") # Deve ser True

    # Comando permitido (shutdown_pc)
    cmd_shutdown = {"action": "shutdown_pc", "parameters": {"confirm": False}}
    print(f"Comando de shutdown permitido? {validate_command(cmd_shutdown)}") # Deve ser True

    # Comando não permitido (ação não na ALLOWED_ACTIONS)
    cmd_delete_files = {"action": "delete_files", "parameters": {"path": "/"}}
    print(f"Comando de delete_files permitido? {validate_command(cmd_delete_files)}") # Deve ser False

    # Comando com termo na blacklist (mesmo se a ação fosse permitida, o termo perigoso bloqueia)
    cmd_unsafe_param = {"action": "send_email", "parameters": {"to": "admin@example.com", "subject": "Urgente", "body": "Por favor, rm -rf /"}}
    print(f"Comando com termo na blacklist permitido? {validate_command(cmd_unsafe_param)}") # Deve ser False

    # Comando em cadeia permitido
    cmd_chain_allowed = {
        "action": "chain",
        "tasks": [
            {"action": "send_email", "parameters": {"to": "chain@example.com"}},
            {"action": "shutdown_pc", "parameters": {"confirm": False}}
        ]
    }
    print(f"Comando em cadeia permitido? {validate_command(cmd_chain_allowed)}") # Deve ser True

    # Comando em cadeia com ação não permitida
    cmd_chain_denied = {
        "action": "chain",
        "tasks": [
            {"action": "send_email", "parameters": {"to": "chain@example.com"}},
            {"action": "unauthorized_action", "parameters": {}}
        ]
    }
    print(f"Comando em cadeia com ação não permitida? {validate_command(cmd_chain_denied)}") # Deve ser False
