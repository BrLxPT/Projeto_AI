def execute_function(params):
    # lógica do plugin
    return "Executado com " + str(params)

def register():
    return {
        "name": "exemplo_plugin",
        "description": "Plugin exemplo para demo",
        "parameters": {
            "param1": "string"
        },
        "execute": execute_function
    }
