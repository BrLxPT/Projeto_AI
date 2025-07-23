import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import ssl
import socket

class EmailSender:
    def __init__(self):
        self.config = {
            'smtp_server': None,
            'smtp_port': None,
            'email': None,
            'password': None
        }

    def configure(self, params):
        """Configura os dados SMTP usando um dicionário"""
        try:
            self.config['smtp_server'] = params.get('smtp_server')
            self.config['smtp_port'] = params.get('smtp_port')
            self.config['email'] = params.get('email')
            self.config['password'] = params.get('password')
            
            # Validação básica
            if None in self.config.values():
                return {"status": "error", "message": "Todos os parâmetros são obrigatórios"}
                
            return {"status": "success", "message": "Configuração SMTP salva"}
        except Exception as e:
            return {"status": "error", "message": f"Erro na configuração: {str(e)}"}

    def send(self, params):
        """Envia o e-mail com tratamento avançado de erros"""
        # Verificação de configuração
        if None in self.config.values():
            return {
                "status": "error",
                "message": "Configuração SMTP incompleta. Execute configure_email() primeiro."
            }

        # Validação dos parâmetros de entrada
        required_params = ['to', 'subject', 'body']
        if not all(param in params for param in required_params):
            return {
                "status": "error",
                "message": f"Parâmetros faltando. Necessário: {', '.join(required_params)}"
            }

        try:
            # Preparação da mensagem
            msg = MIMEMultipart()
            msg['From'] = self.config['email']
            msg['To'] = params['to']
            msg['Subject'] = params['subject']
            msg.attach(MIMEText(params['body'], 'plain', 'utf-8'))

            context = ssl.create_default_context()

            # Configuração de timeout e tentativas
            with smtplib.SMTP(
                host=self.config['smtp_server'],
                port=self.config['smtp_port'],
                timeout=10
            ) as server:
                server.ehlo()
            
                # Suporte explícito para STARTTLS
                if self.config['smtp_port'] in [587, 2587]:
                    server.starttls(context=context)
                    server.ehlo()
            
                # Autenticação com tratamento específico para Gmail
                try:
                    server.login(self.config['email'], self.config['password'])
                except smtplib.SMTPAuthenticationError as auth_error:
                    error_msg = "Falha na autenticação. "
                    if "Application-specific password required" in str(auth_error):
                        error_msg += "Requer senha de app do Google. Veja: https://support.google.com/mail/?p=InvalidSecondFactor"
                    elif "BadCredentials" in str(auth_error):
                        error_msg += "Credenciais inválidas. Verifique usuário/senha."
                    else:
                        error_msg += f"Erro SMTP: {str(auth_error)}"
                    return {"status": "error", "message": error_msg}
            
                # Envio com verificação
                try:
                    server.send_message(msg)
                    return {
                        "status": "success",
                        "message": f"E-mail enviado para {params['to']}"
                    }
                except smtplib.SMTPRecipientsRefused as send_error:
                    return {
                        "status": "error",
                        "message": f"Endereço inválido: {params['to']}"
                    }

        except smtplib.SMTPConnectError:
            return {
                "status": "error",
                "message": f"Não foi possível conectar ao servidor {self.config['smtp_server']}:{self.config['smtp_port']}"
            }
        except socket.timeout:
            return {
                "status": "error",
                "message": "Timeout na conexão SMTP"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Erro inesperado: {str(e)}"
            }

def register():
    email_sender = EmailSender()
    return {
        "name": "email_sender",
        "description": "Sistema de envio de e-mails configurável",
        "actions": {
            "configure_email": {
                "description": "Configura os dados SMTP",
                "parameters": {
                    "smtp_server": "string (ex: smtp.gmail.com)",
                    "smtp_port": "number (ex: 587)",
                    "email": "string (seu e-mail)",
                    "password": "string (sua senha)"
                },
                "execute": email_sender.configure
            },
            "send_email": {
                "description": "Envia um e-mail",
                "parameters": {
                    "to": "string (e-mail destinatário)",
                    "subject": "string",
                    "body": "string"
                },
                "execute": email_sender.send
            }
        }
    }