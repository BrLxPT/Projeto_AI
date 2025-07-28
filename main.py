from core import TaskEngine
import speech_recognition as sr
from ollama_helper import OllamaAPI
from flask import Flask, request, jsonify
import re
import json
import requests
import logging
import getpass
import smtplib
import socket
from email.utils import parseaddr

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
engine = TaskEngine()
ollama = OllamaAPI(timeout=120)

def check_ollama_connection():
    """Verifica se o servidor Ollama está rodando"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Falha na conexão com Ollama: {str(e)}")
        return False

def extract_email(text):
    """Extrai o primeiro email válido do texto"""
    pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    match = re.search(pattern, text)
    return match.group(0) if match else None

def validate_email(email):
    """Valida o formato de um endereço de email"""
    return '@' in parseaddr(email)[1]

def voice_input():
    """Captura entrada por voz usando microfone"""
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Ouvindo... (fale agora)")
        try:
            audio = r.listen(source, timeout=5)
            return r.recognize_google(audio, language="pt")
        except sr.WaitTimeoutError:
            print("Tempo esgotado - nenhum comando detectado")
            return ""
        except Exception as e:
            print(f"Erro no reconhecimento: {str(e)}")
            return ""

def process_email_command(user_input):
    """Processa especificamente comandos de envio de email"""
    try:
        recipient = extract_email(user_input)
        if not recipient or not validate_email(recipient):
            return {
                'status': 'error',
                'message': 'Endereço de email inválido ou não encontrado'
            }
        
        prompt = f"""
        Comando: "{user_input}"
        
        Converta para JSON com:
        - 'action': "send_email" (fixo)
        - 'parameters': {{
            'to': "{recipient}" (fixo),
            'subject': "string com 2-6 palavras",
            'body': "string com 10+ palavras"
        }}
        
        Exemplo válido:
        {{
            "action": "send_email",
            "parameters": {{
                "to": "{recipient}",
                "subject": "Assunto do Email",
                "body": "Conteúdo detalhado com pelo menos dez palavras..."
            }}
        }}
        """
        
        response = ollama.generate(
            model="llama3",
            prompt=prompt,
            format="json",
            temperature=0.5
        )
        
        if isinstance(response, dict) and 'response' in response:
            command = json.loads(response['response'])
            if all(k in command.get('parameters', {}) for k in ['to', 'subject', 'body']):
                return command
        
        return {
            'status': 'error',
            'message': 'Não foi possível gerar um comando de email válido'
        }
            
    except Exception as e:
        logger.error(f"Erro no processamento de email: {str(e)}")
        return {
            'status': 'error',
            'message': 'Falha ao processar comando de email'
        }

def process_user_input(user_input):
    """Processa comandos genéricos do usuário"""
    try:
        response = ollama.generate(
            model="llama3",
            prompt=f"Converta para JSON o comando: {user_input}",
            format="json"
        )
        return json.loads(response['response'])
    except Exception as e:
        return {
            "status": "error",
            "message": f"Falha ao processar: {str(e)}"
        }

def setup_email_configuration():
    """Configura interativamente os dados SMTP"""
    print("\n⚙️ Configuração de Email (pressione Enter para pular)")
    
    config = {
        'smtp_server': input("Servidor SMTP (ex: smtp.gmail.com): ").strip(),
        'smtp_port': input("Porta SMTP (ex: 587): ").strip(),
        'email': input("Seu email: ").strip(),
        'password': getpass.getpass("Senha/App Password: ").strip()
    }
    
    if not all(config.values()):
        return {'status': 'skipped', 'message': 'Configuração ignorada'}
    
    # Validação
    if not config['smtp_port'].isdigit():
        return {'status': 'error', 'message': 'Porta inválida'}
    if not validate_email(config['email']):
        return {'status': 'error', 'message': 'Email inválido'}
    
    return {
        'status': 'success',
        'config': config
    }

@app.route("/chat", methods=["POST"])
def chat_endpoint():
    """Endpoint para API de chat"""
    try:
        data = request.get_json()
        if not data or "mensagem" not in data:
            return jsonify({"error": "Formato inválido"}), 400
            
        response = ollama.generate(
            model="llama3",
            prompt=data["mensagem"],
            temperature=0.7
        )
        return jsonify(response)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    if not check_ollama_connection():
        print("❌ Ollama não está rodando. Execute primeiro:")
        print("$ ollama serve")
        exit(1)

    # Configuração inicial
    if "email_sender" in engine.plugins:
        config_result = setup_email_configuration()
        if config_result['status'] == 'error':
            print(f"❌ {config_result['message']}")
        elif config_result['status'] == 'success':
            print("✅ Configuração SMTP salva")

    # Loop principal
    while True:
        mode = input("\nModo (voz/texto/servidor): ").lower()
        
        if mode == "servidor":
            app.run(host='0.0.0.0', port=5000)
            break
            
        if mode == "voz":
            user_input = voice_input()
            if not user_input:
                continue
            print(f"Comando detectado: {user_input}")
        else:
            user_input = input("Comando: ")
        
        if user_input.lower() in ['sair', 'exit']:
            break
            
        # Processamento do comando
        if '@' in user_input or 'enviar email' in user_input.lower():
            command = process_email_command(user_input)
        else:
            command = process_user_input(user_input)
        
        if command.get('status') == 'error':
            print(f"❌ {command['message']}")
            continue
            
        result = engine.execute_task(command)
        print("↳ Resultado:", result)