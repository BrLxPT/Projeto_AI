from ollama import Client
import json

ollama = Client(host='http://localhost:11434')

def avaliar_condiçao_ollama(condicao: str) -> tuple[bool, str]:
    prompt = f"""
Analisa a seguinte condição: "{condicao}".
Responde com:
- Uma linha: "true" ou "false"
- Depois: uma explicação da decisão em 1-2 frases.
"""
    
    response = ollama.chat(model='llama3', message=[{"role": "user", "content": prompt}])
    content = response['message']['content'].strip().lower()
    linhas = content.splitlines()

    if linhas:
        valid = "true" in linhas[0]
        explicacao = "\n".join(linhas[1:]).strip()
        return valid, explicacao
    return False, "sem respostaválida do AI"

def gerar_regra(texto_instrucao: str) -> dict:
    prompt = f"""
Transforma esta instrução em uma regra JSON:

"{texto_instrucao}"

O formato da regra deve ser:
{{
  "id": "regra_alguma_coisa",
  "condition": "condição lógica em texto",
  "action": {{
    "type": "send_email" ou "call_api" ou "log" ou "notify",
    "to": "email@example.com" (opcional),
    "url": "https://api.com/..." (opcional),
    "message": "texto da mensagem" (opcional),
    "payload": "corpo json" (opcional)
  }}
}}

Só responde com o JSON. Sem explicações.
"""
    
    response = ollama.chat(model='llama3', message=[{"role": "user", "content": prompt}])
    content = response['message']['content'].strip()

    try:
        regra = json.loads(content)
        return regra
    except Exception as e:
        print("Erro a gerar regra:", e)
        return None
