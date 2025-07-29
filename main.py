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

def process_email_command(user_input):
    """
    Processa especificamente comandos de envio de email.
    Esta função pode ser removida se o LLM for capaz de gerar o JSON diretamente
    com base no prompt_template em process_user_input.
    Mantida para compatibilidade com o fluxo anterior.
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
        logger.error(f"Erro no processamento de email: {str(e)}")
        return {
            'status': 'error',
            'message': 'Falha ao processar comando de email'
        }

def process_user_input(user_input):
    """
    Processa comandos genéricos do usuário, usando o LLM para decidir a ação
    e formatar o JSON para as ferramentas disponíveis.
    """
    prompt_template = f"""
    Comando do usuário: "{user_input}"

    Converta o comando do usuário para um objeto JSON que possa ser executado por uma ferramenta.
    As ferramentas disponíveis incluem:
    - 'pc_control': para controlar o PC.
      - Ações:
        - 'shutdown_pc': Desliga o computador. Parâmetros: 'confirm' (boolean, obrigatório para execução real).
        - 'restart_pc': Reinicia o computador. Parâmetros: 'confirm' (boolean, obrigatório para execução real).
    - 'email_sender': para enviar e-mails.
      - Ações:
        - 'send_email': Envia um e-mail. Parâmetros: 'to' (string), 'subject' (string), 'body' (string).

    Se o comando for para desligar ou reiniciar o PC, o JSON deve ter:
    {{
        "action": "shutdown_pc" ou "restart_pc",
        "parameters": {{
            "confirm": true ou false (true se o usuário explicitamente pedir para desligar/reiniciar, caso contrário false para pedir confirmação)
        }}
    }}

    Se o comando for para enviar um email, o JSON deve ter:
    {{
        "action": "send_email",
        "parameters": {{
            "to": "email do destinatário",
            "subject": "assunto do email",
            "body": "corpo do email"
        }}
    }}

    Para outros comandos, gere uma resposta de texto simples no formato:
    {{
        "status": "text_response",
        "message": "Sua resposta de texto aqui."
    }}
    Se não conseguir mapear para uma ação, retorne uma resposta de texto simples.

    Exemplos de comandos para ferramentas:
    - "Desliga o meu computador" -> {{"action": "shutdown_pc", "parameters": {{"confirm": false}}}}
    - "Desliga o computador agora" -> {{"action": "shutdown_pc", "parameters": {{"confirm": true}}}}
    - "Reinicia o PC" -> {{"action": "restart_pc", "parameters": {{"confirm": false}}}}
    - "Reinicia o PC sem perguntar" -> {{"action": "restart_pc", "parameters": {{"confirm": true}}}}
    - "Manda um email para joao@exemplo.com com o assunto reunião e o corpo olá joão" -> {{"action": "send_email", "parameters": {{"to": "joao@exemplo.com", "subject": "reunião", "body": "olá joão"}}}}
    
    Exemplos de respostas de texto:
    - "Qual a previsão do tempo?" -> {{"status": "text_response", "message": "Não consigo verificar a previsão do tempo no momento."}}
    - "Olá" -> {{"status": "text_response", "message": "Olá! Como posso ajudar?"}}
    """
    try:
        response = ollama.generate(
            model="llama3", # Ou o modelo que estiver a usar
            prompt=prompt_template,
            format="json", # Peça sempre JSON para comandos de ferramenta
            temperature=0.0 # Use temperatura baixa para comandos precisos
        )
        
        # Tente carregar a resposta como JSON
        try:
            command = json.loads(response['response'])
            # Verifique se é um comando de ferramenta válido ou uma resposta de texto
            if "action" in command and "parameters" in command:
                return command
            elif command.get("status") == "text_response" and "message" in command:
                return command # Já é uma resposta de texto formatada
            else:
                # Se não for um comando de ferramenta nem uma resposta de texto formatada,
                # trate a resposta bruta como uma mensagem de texto simples.
                return {"status": "text_response", "message": response['response']}
        except json.JSONDecodeError:
            # Se a resposta do LLM não for JSON válido, trate como resposta de texto
            return {"status": "text_response", "message": response['response']}

    except Exception as e:
        logger.error(f"Erro no processamento do input do usuário: {str(e)}")
        return {
            "status": "error",
            "message": f"Falha ao processar: {str(e)}"
        }

def setup_email_configuration():
    """
    Coleta interativamente os dados SMTP (servidor, porta, email e senha) do utilizador.
    Retorna um dicionário com 'status' e 'config' (se sucesso).
    """
    print("\n⚙️ Configuração de Email (pressione Enter para pular)")
    
    # Agora o utilizador precisa fornecer todos os detalhes SMTP
    smtp_server = input("Servidor SMTP (ex: smtp.gmail.com, smtp.outlook.com): ").strip()
    smtp_port = input("Porta SMTP (ex: 587 para STARTTLS, 465 para SSL): ").strip()
    sender_email = input("Seu email: ").strip()
    sender_password = getpass.getpass("Sua Senha (ou Senha de Aplicativo para Gmail): ").strip()

    config = {
        'smtp_server': smtp_server,
        'smtp_port': smtp_port,
        'email': sender_email,
        'password': sender_password
    }
    
    # Se qualquer campo essencial estiver vazio, considera que a configuração foi ignorada
    if not all(config.values()):
        return {'status': 'skipped', 'message': 'Configuração de email ignorada: todos os campos são obrigatórios.'}
    
    # Validação da porta
    if not config['smtp_port'].isdigit():
        return {'status': 'error', 'message': 'Porta inválida: deve ser um número inteiro.'}
    
    # Validação do email
    if not validate_email(config['email']):
        return {'status': 'error', 'message': 'Email inválido: formato incorreto.'}
    
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

    # Configuração inicial do email_sender
    if "email_sender" in engine.plugins:
        config_result = setup_email_configuration()
        
        if config_result['status'] == 'success':
            email_configure_action = engine.plugins['email_sender']['actions']['configure_email']['execute']
            tool_config_response = email_configure_action(config_result['config'])
            
            if tool_config_response['status'] == 'success':
                print("✅ Configuração SMTP salva e aplicada à ferramenta.")
            else:
                print(f"❌ Erro ao aplicar configuração SMTP à ferramenta: {tool_config_response['message']}")
        elif config_result['status'] == 'skipped':
            print("ℹ️ Configuração de email ignorada.")
        else: # status == 'error' da setup_email_configuration
            print(f"❌ Erro na coleta da configuração de email: {config_result['message']}")


    # Loop principal
    while True:
        mode = input("\nModo (voz/texto/servidor): ").lower()
        
        if mode == "servidor":
            print("Iniciando servidor Flask na porta 5000...")
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
            
        # Processamento do comando (agora process_user_input lida com tudo)
        command = process_user_input(user_input)
        
        if command.get('status') == 'error':
            print(f"❌ {command['message']}")
            continue
        elif command.get('status') == 'text_response':
            print(f"🤖 {command['message']}")
            continue
        else: # É um comando de ferramenta
            result = engine.execute_task(command)
            print("↳ Resultado:", result)
