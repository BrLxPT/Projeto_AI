import requests

class OllamaAPI:
    def __init__(self, base_url="http://localhost:11434"):
        self.base_url = base_url
    
    def generate(self, model: str, prompt: str, **kwargs):
        endpoint = f"{self.base_url}/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            **kwargs
        }
        response = requests.post(endpoint, json=payload)
        response.raise_for_status()
        return response.json()
    
def ask_ollama(prompt, model="llama3"):
    response = requests.post(
    "http://localhost:11434/api/generate",
    json={
            "model": model,
            "prompt": prompt,
            "stream": False
        }
    )
    return response.json()["response"]

# Exemplo de uso
if __name__ == "__main__":
    ollama = OllamaAPI()
    resposta = ollama.generate(
        model="llama3",
        prompt="Explique como a API do Ollama funciona",
        stream=False
    )
    print(resposta["response"])