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
            # Garante que a porta seja um inteiro
            self.config['smtp_port'] = int(params.get('smtp_port'))
            self.config['email'] = params.get('email')
            self.config['password'] = params.get('password')
            
            # Validação básica
            if None in self.config.values() or "" in self.config.values(): # Adiciona verificação de string vazia
                return {"status": "error", "message": "Todos os parâmetros são obrigatórios e não podem ser vazios."}
                
            return {"status": "success", "message": "Configuração SMTP salva"}
        except ValueError:
            return {"status": "error", "message": "A porta SMTP deve ser um número inteiro."}
        except Exception as e:
            return {"status": "error", "message": f"Erro na configuração: {str(e)}"}

    def send(self, params):
        """Envia o e-mail com tratamento avançado de erros"""
        # Verificação de configuração
        if None in self.config.values() or "" in self.config.values():
            return {
                "status": "error",
                "message": "Configuração SMTP incompleta. Execute configure_email() primeiro."
            }

        # Validação dos parâmetros de entrada
        required_params = ['to', 'subject', 'body']
        if not all(param in params and params[param] for param in required_params): # Verifica se o valor não é vazio
            return {
                "status": "error",
                "message": f"Parâmetros faltando ou vazios. Necessário: {', '.join(required_params)}"
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

# --- EXEMPLO DE USO INTERATIVO ---
if __name__ == "__main__":
    tool_info = register()
    # Acessa a instância da classe EmailSender
    email_sender_instance = tool_info["actions"]["configure_email"]["execute"].__self__

    print("--- Configuração de E-mail ---")
    print("Por favor, insira os seus dados SMTP:")

    smtp_server = input("Servidor SMTP (ex: smtp.gmail.com): ").strip()
    smtp_port_str = input("Porta SMTP (ex: 587): ").strip()
    sender_email = input("Seu endereço de e-mail: ").strip()
    sender_password = input("Sua senha de e-mail (para Gmail, use uma Senha de App): ").strip()

    config_params = {
        "smtp_server": smtp_server,
        "smtp_port": smtp_port_str, # Passa como string, será convertido dentro do método configure
        "email": sender_email,
        "password": sender_password
    }

    result_config = email_sender_instance.configure(config_params)
    print(f"\nResultado da configuração: {result_config}")

    if result_config["status"] == "success":
        print("\n--- Envio de E-mail ---")
        print("Por favor, insira os detalhes do e-mail a enviar:")

        recipient_email = input("E-mail do destinatário: ").strip()
        subject = input("Assunto do e-mail: ").strip()
        body = input("Corpo do e-mail: ").strip()

        send_params = {
            "to": recipient_email,
            "subject": subject,
            "body": body
        }

        result_send = email_sender_instance.send(send_params)
        print(f"\nResultado do envio: {result_send}")
    else:
        print("\nConfiguração falhou, não é possível enviar o e-mail.")

    print("\nFim do programa.")