from core import TaskEngine
import speech_recognition as sr
from ollama_helper import OllamaAPI
from flask import Flask, request, jsonify
import re
import json
import requests
import logging
import getpass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
engine = TaskEngine()
ollama = OllamaAPI(timeout=120)  # Increased timeout to 120 seconds

def setup_email_configuration():
    """Configura os dados de e-mail interativamente"""
    print("\n⚙️ Configuração inicial do serviço de e-mail:")
    print("Por favor, insira suas credenciais SMTP:")
    
    smtp_server = input("Servidor SMTP (ex: smtp.gmail.com): ").strip()
    smtp_port = int(input("Porta SMTP (ex: 587): ").strip())
    email = input("Seu endereço de e-mail: ").strip()
    password = getpass.getpass("Sua senha/app password: ").strip()

    # Obtém a função de configuração do plugin
    configure_func = engine.plugins["email_sender"]["actions"]["configure_email"]["execute"]
    
    # Chama a função com os parâmetros corretos
    config_result = configure_func({
        "smtp_server": smtp_server,
        "smtp_port": smtp_port,
        "email": email,
        "password": password
    })
    
    return config_result

def check_ollama_connection():
    """Check if Ollama server is running"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Ollama connection check failed: {str(e)}")
        return False

def extract_email(text):
    """Extract first email found in text"""
    pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    match = re.search(pattern, text)
    return match.group(0) if match else None

def process_user_input(user_input):
    """Process user input for email commands"""
    try:
        recipient = extract_email(user_input)
        if not recipient:
            return {"status": "error", "message": "Nenhum e-mail válido encontrado no comando"}
        
        prompt = f"""
        Extraia assunto e corpo de e-mail do texto abaixo para enviar para {recipient}.
        Retorne APENAS um JSON válido no formato:
        {{
            "action": "send_email",
            "parameters": {{
                "to": "{recipient}",
                "subject": "assunto extraído aqui",
                "body": "corpo da mensagem aqui"
            }}
        }}
        
        Texto: {user_input}
        """
        
        logger.info(f"Enviando prompt para Ollama: {prompt[:200]}...")
        ollama_response = ollama.generate(
            model="llama3",
            prompt=prompt,
            temperature=0.7,
            format="json",
            max_retries=3
        )
        
        if isinstance(ollama_response, dict) and ollama_response.get("status") == "error":
            return ollama_response
            
        response_text = ollama_response.get("response", str(ollama_response))
        
        # Tenta extrair JSON da resposta
        try:
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            return {"status": "error", "message": "Nenhum JSON válido encontrado na resposta"}
        except json.JSONDecodeError as e:
            return {"status": "error", "message": f"Erro ao decodificar JSON: {str(e)}"}
            
    except Exception as e:
        logger.error(f"Erro ao processar input: {str(e)}")
        return {"status": "error", "message": f"Erro de processamento: {str(e)}"}

def voice_input():
    """Captura entrada por voz usando microfone"""
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Ouvindo...")
        try:
            audio = r.listen(source, timeout=5)
            return r.recognize_google(audio, language="pt-BR")
        except sr.WaitTimeoutError:
            print("Nenhum comando de voz detectado")
            return ""
        except Exception as e:
            print(f"Erro no reconhecimento de voz: {str(e)}")
            return ""

@app.route("/chat", methods=["POST"])
def chat_endpoint():
    """Endpoint API para interações de chat"""
    try:
        data = request.get_json()
        if not data or "mensagem" not in data:
            return jsonify({"error": "Formato de requisição inválido"}), 400
            
        response = ollama.generate(
            model="llama3",
            prompt=data["mensagem"],
            temperature=0.7
        )
        return jsonify({"response": response.get("response", response)})
    except Exception as e:
        logger.error(f"Erro na API: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    if not check_ollama_connection():
        print("Erro: Servidor Ollama não está rodando. Por favor inicie com:")
        print("$ ollama serve")
        exit(1)

    # Configuração inicial do e-mail
    if "email_sender" in engine.plugins:
        print("🔧 Configuração inicial necessária")
        config_result = setup_email_configuration()
        if config_result.get("status") != "success":
            print(f"❌ Erro na configuração: {config_result['message']}")
            exit(1)
        print("✅ Configuração de e-mail concluída com sucesso\n")
    else:
        print("⚠️ Plugin de e-mail não encontrado - funcionalidade de e-mail desabilitada")

    while True:
        mode = input("Modo (voz/texto/servidor): ").lower()
        
        if mode == "servidor":
            print("Iniciando servidor Flask...")
            app.run(host='0.0.0.0', port=5000, debug=False)
            break
            
        elif mode == "voz":
            user_input = voice_input()
            if not user_input:
                print("Não foi possível entender o comando de voz")
                continue
            print(f"Comando: {user_input}")
        else:
            user_input = input("Comando: ")
        
        if user_input.lower() in ["sair", "exit", "quit"]:
            break
            
        command = process_user_input(user_input)
        if command.get("status") == "error":
            print(f"Erro: {command['message']}")
            continue
            
        result = engine.execute_task(command)
        print("Resultado:", result)