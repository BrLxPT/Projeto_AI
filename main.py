from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from rules_engine import evaluate_rule
from typing import List, Dict
from storage import load_rules, save_rules
from scheduler import start_scheduler
from models import Rule
from ollama_client import avaliar_condiçao_ollama
from actions import send_email, call_api, log_action
import threading
import json, uuid

app = FastAPI()
rules_store = load_rules()
notificacoes = []

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

class RuleRequest(BaseModel):
    rule: str
    context: Dict

@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "rules": rules_store})

@app.post("/rules")
def add_rule(rule: RuleRequest):
    rules_store.append(rule)
    save_rules(rules_store)
    return{"message": "Regra adicionada com sucesso."}

@app.post("/rules/evaluate")
def evaluate_rules():
    results = []
    deve_executar, justificativa = avaliar_condiçao_ollama(condicao)

    for rule in rules_store:
        condicao = rule["condition"]
        acao = rule["action"]
        regra_id = rule["id"]

        if deve_executar:
            resultado_acao = executar_acao(acao)
            results.append(f'✅ "{regra_id}" ativada → {resultado_acao}\n🧠 {justificativa}')
        else:
            results.append(f'❌ "{regra_id}" ignorada\n🧠 {justificativa}')

    return {"message": "\n".join(results)}

@app.get("/")
def hello():
    return{"msg": "API de automações com AI ativa!"}

def executar_acao(acao: dict):
    tipo = acao.get("type")

    if tipo == "send_email":
        return send_email(acao["to"], acao.get("subject", "alerta AI"), acao["message"])
    
    elif tipo == "call_api":
        return call_api(acao["url"], acao.get("payload", {}))
    
    elif tipo == "log":
        return log_action(acao["message"])
    
    elif tipo == "notify":
        adicionar_notificacao["message"]
        return f"🔔 Notificação enviada para a dashboard"
    
    return f"❓ Ação desconhecida: {tipo}"

@app.get("/notificacoes")
def get_notificacoes():
    return JSONResponse(content={"notificacoes": notificacoes})

def adicionar_notificacao(msg: str):
    notificacoes.append(msg)
    if len (notificacoes) > 50:
        notificacoes.pop(0)

@app.post("/rules/add")
async def add_rule(request: Request):
    form = await request.form()
    nova_regra = {
        "id": form["id"],
        "condition": form["condition"],
        "action": {
            "type": form["type"],
            "to": form.get("to"),
            "url": form.get("url"),
            "message": form.get("message"),
            "payload": form.get("payload")
        }
    }
    rules_store.append(nova_regra)
    salvar_regras()
    return RedirectResponse("/", status_code=303)

if __name__ == "__main__":
    threading.Thread(target=start_scheduler).start()