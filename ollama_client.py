from ollama import Client

ollama = Client(host='http://localhost:11434')

def avaliar_condiçao_ollama(condicao: str)-> tuple[bool, str]:
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
        explicacao = "/n".join(linhas[1:]).strip()
        return valid, explicacao
    return False, "sem respostaválida do AI"