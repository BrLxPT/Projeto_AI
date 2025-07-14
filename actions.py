import requests
import smtplib
from email.mime.text import MIMEText
from pathlib import Path

log_file = Path("log.txt")

def send_email(to, subject, message):
    smtp_server = "smtp.gmai.com"
    smtp_port = 587
    username = "teu@gmail.com"
    password = "tua_senha"

    msg = MIMEText(message)
    msg["Subject"] = subject
    msg["From"] = username
    msg["To"] = to

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(username, password)
            server.send_message(msg)
        return "✅ Email enviado com sucesso"
    except Exception as e:
        return f"❌ Erro ao enviar email: {e}"
    
def call_api(url, payload=None):
    try:
        res = requests.post(url, json=payload or {})
        return f"✅ API chamada: {res.status_code}"
    except Exception as e:
        return f"❌ Erro na chamada da API: {e}"
    
def log_action(text):
    log_file.write_text(log_file.read_text() + f"{text}\n")
    return f"📝 Log escrito: {text}"