import re

def validate_command(command):
    """Valida se o comando é seguro para executar"""
    if isinstance(command, dict):
        # Se for um comando estruturado, verifica o campo 'action'
        user_input = command.get('action', '') + ' ' + str(command.get('parameters', ''))
    else:
        # Se for texto direto
        user_input = str(command)

    BLACKLIST = [
        r'rm -rf', r'format', r'delete all', r'shutdown',
        r'password', r'credential', r'senha', r'\\'
    ]

    if any(re.search(pattern, user_input, re.IGNORECASE) for pattern in BLACKLIST):
        return False
        
    # Verificar permissões do usuário (implementar conforme necessário)
    if not user_has_permissions(user_input):
        return False
        
    return True

def user_has_permissions(command):
    """Verifica se o usuário tem permissões para executar o comando"""
    # Implemente sua lógica de permissões aqui
    return True  # Temporário - sempre permite