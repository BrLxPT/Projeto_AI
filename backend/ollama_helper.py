import requests
from urllib3.exceptions import ReadTimeoutError

class OllamaAPI:
    def __init__(self, base_url="http://localhost:11434", timeout=300):
        self.base_url = base_url
        self.timeout = timeout  # Aumente o timeout padrão

    def generate(self, model, prompt, temperature=0.7, format=None, max_retries=3):
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature}
        }
        if format:
            payload["format"] = format

        for attempt in range(max_retries):
            try:
                response = requests.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    timeout=self.timeout
                )
                response.raise_for_status()
                return response.json()
            
            except ReadTimeoutError:
                if attempt == max_retries - 1:
                    return {"status": "error", "message": "Timeout após várias tentativas"}
                print(f"⚠️ Timeout (tentativa {attempt + 1}/{max_retries}), tentando novamente...")
                continue
                
            except Exception as e:
                return {"status": "error", "message": str(e)}