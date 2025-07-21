import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import logging

logger = logging.getLogger(__name__)

def send_email(params):
    try:
        # Configurações SMTP (substitua com suas credenciais)
        smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", 587))
        sender_email = os.getenv("EMAIL_USER")
        sender_password = os.getenv("EMAIL_PASS")

        if not all([sender_email, sender_password]):
            raise ValueError("Credenciais de e-mail não configuradas")

        # Criar mensagem
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = params['to']
        msg['Subject'] = params['subject']
        msg.attach(MIMEText(params['body'], 'plain'))

        # Enviar e-mail
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        
        return {"status": "success", "message": f"E-mail enviado para {params['to']}"}
    
    except Exception as e:
        logger.error(f"Erro ao enviar e-mail: {str(e)}")
        return {"status": "error", "message": f"Falha no envio: {str(e)}"}

def register():
    return {
        "name": "email_sender",  # Nome deve ser exatamente este
        "description": "Plugin para envio de e-mails",
        "actions": {
            "send_email": {  # Ação deve ser exatamente esta
                "description": "Envia um e-mail",
                "parameters": {
                    "to": "string (e-mail válido)",
                    "subject": "string",
                    "body": "string"
                },
                "execute": send_email
            }
        }
    }