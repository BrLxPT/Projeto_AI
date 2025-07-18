import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

def execute(params):
    to = params.get("to")
    subject = params.get("subject")
    body = params.get("body")

    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    sender_email = os.getenv("EMAIL_USER")
    sender_password = os.getenv("EMAIL_PASS")

    if not (to and subject and body):
        return "Parâmetros insuficientes para enviar email."

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = to
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        return f"Email enviado para {to} com sucesso!"
    except Exception as e:
        return f"Erro ao enviar email: {e}"

def register():
    return {
        "name": "email_send",
        "description": "Envia um email via SMTP",
        "parameters": {
            "to": "string",
            "subject": "string",
            "body": "string"
        },
        "execute": execute
    }
