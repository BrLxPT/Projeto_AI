from .core import TaskEngine
import speech_recognition as sr
from .ollama_helper import OllamaAPI
from flask import Flask, request, jsonify
from flask_cors import CORS # Importar Flask-CORS
import re
import json
import requests
import logging
import getpass # getpass não será usado no backend da web, mas mantido para referência
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
CORS(app) # Habilitar CORS para todas as rotas
engine = TaskEngine() # A instância do TaskEngine já carrega os plugins e capacidades
ollama = OllamaAPI(timeout=300) # OllamaAPI é usado diretamente pelo TaskEngine para gerar comandos

# Variável global para armazenar o estado de configuração do e-mail
# Em uma aplicação real, isso seria armazenado de forma persistente (ex: banco de dados)
email_configured = False 

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

# Esta função de voice_input é para o terminal e não será usada diretamente na web
def voice_input():
    """Captura entrada por voz usando microfone default do pc"""
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

# Função para processar comandos de email, agora adaptada para ser chamada internamente
def process_email_command_internal(user_input):
    """
    Processa especificamente comandos de envio de email.
    Adaptada para ser chamada internamente pelo endpoint /command se o LLM decidir.
    """
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
        logger.error(f"Erro no processamento de email interno: {str(e)}")
        return {
            'status': 'error',
            'message': 'Falha ao processar comando de email'
        }

# A função process_user_input agora é um wrapper para engine.generate_command
def process_user_input(user_input):
    """
    Processa comandos genéricos do usuário, usando o TaskEngine para gerar o comando
    e lidar com respostas de texto.
    """
    command = engine.generate_command(user_input) 
    return command

# Função para configurar o email via API
@app.route("/configure_email", methods=["POST"])
def configure_email_endpoint():
    global email_configured
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "Dados de configuração ausentes."}), 400

    smtp_server = data.get('smtp_server')
    smtp_port = data.get('smtp_port')
    sender_email = data.get('email')
    sender_password = data.get('password')

    config_params = {
        "smtp_server": smtp_server,
        "smtp_port": smtp_port,
        "email": sender_email,
        "password": sender_password
    }

    if "email_sender" not in engine.plugins:
        return jsonify({"status": "error", "message": "Plugin 'email_sender' não carregado."}), 500

    config_result = {}
    try:
        # Validação da porta
        if not isinstance(smtp_port, (int, str)) or (isinstance(smtp_port, str) and not smtp_port.isdigit()):
            return jsonify({'status': 'error', 'message': 'Porta inválida: deve ser um número inteiro.'}), 400
        config_params['smtp_port'] = int(smtp_port) # Converte para int após validação
        
        # Validação do email
        if not validate_email(sender_email):
            return jsonify({'status': 'error', 'message': 'Email inválido: formato incorreto.'}), 400

        # Chama o método configure do plugin EmailSender
        email_configure_action = engine.plugins['email_sender']['actions']['configure_email']['execute']
        tool_config_response = email_configure_action(config_params)
        
        if tool_config_response['status'] == 'success':
            email_configured = True
            return jsonify({"status": "success", "message": "Configuração SMTP salva e aplicada."})
        else:
            return jsonify(tool_config_response), 500 # Retorna o erro do plugin
    except Exception as e:
        logger.error(f"Erro no endpoint /configure_email: {str(e)}")
        return jsonify({"status": "error", "message": f"Erro interno ao configurar e-mail: {str(e)}"}), 500

# Endpoint para verificar o status da configuração do e-mail
@app.route("/email_status", methods=["GET"])
def email_status_endpoint():
    return jsonify({"email_configured": email_configured})


@app.route("/command", methods=["POST"])
def command_endpoint():
    data = request.get_json()
    if not data or "user_input" not in data:
        return jsonify({"error": "Formato inválido: 'user_input' ausente."}), 400
    
    user_input = data["user_input"]
    
    # Decide se usa process_email_command_internal ou process_user_input
    # Dependendo da complexidade desejada, o LLM em process_user_input poderia lidar com tudo.
    # Mantido aqui para seguir a lógica anterior de priorizar email.
    if '@' in user_input or 'enviar email' in user_input.lower():
        command = process_email_command_internal(user_input)
    else:
        command = process_user_input(user_input) # Esta função usa engine.generate_command

    if command.get('status') == 'error':
        return jsonify(command), 500
    elif command.get('status') == 'text_response':
        return jsonify(command)
    else: # É um comando de ferramenta
        # A validação de segurança já ocorre dentro de engine.execute_task
        result = engine.execute_task(command)
        return jsonify(result)

# Endpoint de chat simples (direto para Ollama, sem ferramentas)
@app.route("/chat", methods=["POST"])
def chat_endpoint():
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
        logger.error("❌ Ollama não está rodando. Por favor, execute 'ollama serve' antes de iniciar o servidor.")
        exit(1)

    logger.info("✨ Iniciando servidor Flask na porta 5000...")
    # Removido o loop principal interativo do terminal
    app.run(host='0.0.0.0', port=5000, debug=True) # debug=True para desenvolvimento
