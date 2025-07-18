def register():
    def execute(params):
        print(f"Simulando execução de hardware com params: {params}")
        return "Simulação OK"
    return {"name": "hardware_control", "description": "Simulação de controle de hardware", "parameters": {}, "execute": execute}
