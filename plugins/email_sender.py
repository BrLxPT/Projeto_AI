import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import ssl

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
        """Envia o e-mail com os parâmetros configurados"""
        if None in self.config.values():
            return {"status": "error", "message": "Configuração SMTP não definida"}

        try:
            msg = MIMEMultipart()
            msg['From'] = self.config['email']
            msg['To'] = params['to']
            msg['Subject'] = params['subject']
            msg.attach(MIMEText(params['body'], 'plain'))

            context = ssl.create_default_context()

            with smtplib.SMTP(self.config['smtp_server'], self.config['smtp_port']) as server:
                server.ehlo()
                server.starttls(context=context)
                server.ehlo()
                server.login(self.config['email'], self.config['password'])
                server.send_message(msg)

            return {"status": "success", "message": f"E-mail enviado para {params['to']}"}
        except Exception as e:
            return {"status": "error", "message": f"Erro ao enviar: {str(e)}"}

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