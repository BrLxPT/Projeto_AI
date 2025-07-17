def register():
    return {
        "name": "nome_plugin",
        "description": "Descrição das capacidades",
        "actions": {
            "nome_acao": {
                "description": "O que a ação faz",
                "parameters": {"param1": "tipo", ...},
                "execute": funcao_execucao
            }
        }
    }