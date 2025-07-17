import re

def validate_command(user_input):
    # Lista negra de comandos perigosos
    BLACKLIST = [
        "rm -rf", "format", "delete all", "shutdown", 
        "senha", "password", "credential"
    ]
    
    # Verificar padrões perigosos
    if any(re.search(pattern, user_input, re.IGNORECASE) for pattern in BLACKLIST):
        return False
    
    # Verificar permissões do usuário (implementar LDAP/JWT)
    if not user_has_permissions(user_input):
        return False
        
    return True

def user_has_permissions(command):
    # Implementar lógica de RBAC (Role-Based Access Control)
    return True  # Temporário