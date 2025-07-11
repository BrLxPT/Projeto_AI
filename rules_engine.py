import requests
import json

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3"

def build_prompt(rule:str, context: dict)->str:
    return f"""Analiza a seguinte regra: "{rule}"
    
    contexto: {context}

    Decide se esta regra deve ser ativada. Só respode em JSON assim:
    {{
        "triggered": true | false,
        "reason": "explicação curta
    }}
    """

def evaluate_rule(rule, context):
   prompt = build_prompt(rule, context)

   response = requests.post(OLLAMA_URL, json={
       "model": OLLAMA_MODEL,
       "prompt": prompt,
       "stream": False
   })

   if response.status_code != 200:
       return{
           "triggered": False,
           "reason": "Erro ao contactar o modelo AI"
       }
   try:
       raw_output = response.json().get("response", "").strip()
       result = eval(raw_output) if raw_output.startswith("{") else {"triggered": False, "reason": "resposta inesperada"}
       return result
   
   except Exception as e:
       return{
           "triggered": False,
           "reason": f"Erro ao interpretar a resposta do modelo: {str(e)}"
       }

