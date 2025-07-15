from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List, Dict
from rules_engine import evaluate_rule
from storage import load_rules, save_rules
from scheduler import start_scheduler
from models import Rule
from ollama_client import avaliar_condiçao_ollama, gerar_regra
from actions import send_email, call_api, log_action
import threading
import json

app = FastAPI()
rules_store = load_rules()
notifications = []  

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

class RuleRequest(BaseModel):
    rule: str
    context: Dict

@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "rules": rules_store})

@app.post("/rules", response_model=dict)
def add_rule(rule: RuleRequest):
    rules_store.append(rule.dict())
    save_rules(rules_store)
    return {"message": "Regra adicionada com sucesso."}

@app.post("/rules/evaluate")
def evaluate_rules():
    results = []

    for rule in rules_store:
        condicao = rule["condition"]
        acao = rule["action"]
        regra_id = rule["id"]

        deve_executar, justificativa = avaliar_condiçao_ollama(condicao)

        if deve_executar:
            resultado_acao = executar_acao(acao)
            results.append(f'✅ "{regra_id}" ativada → {resultado_acao}\n🧠 {justificativa}')
        else:
            results.append(f'❌ "{regra_id}" ignorada\n🧠 {justificativa}')

    return {"message": "\n".join(results)}

def executar_acao(acao: dict):
    tipo = acao.get("type")

    if tipo == "send_email":
        return send_email(acao["to"], acao.get("subject", "alerta AI"), acao["message"])
    
    elif tipo == "call_api":
        return call_api(acao["url"], acao.get("payload", {}))
    
    elif tipo == "log":
        return log_action(acao["message"])
    
    elif tipo == "notify":
        adicionar_notificacao(acao["message"])
        return "🔔 Notificação enviada para a dashboard"
    
    return f"❓ Ação desconhecida: {tipo}"

@app.get("/notifications")
async def get_notifications():
    return {"notifications": notifications}

def adicionar_notificacao(msg: str):
    notifications.append(msg)
    if len(notifications) > 50:
        notifications.pop(0)

@app.post("/rules/add")
async def add_rule_form(
    request: Request,
    id: str = Form(...),
    condition: str = Form(...),
    type: str = Form(...),
    to: str = Form(None),
    url: str = Form(None),
    message: str = Form(None),
    payload: str = Form(None),
):
    nova_regra = {
        "id": id,
        "condition": condition,
        "action": {
            "type": type,
            "to": to,
            "url": url,
            "message": message,
            "payload": payload,
        }
    }
    rules_store.append(nova_regra)
    save_rules(rules_store)
    return RedirectResponse("/", status_code=303)

@app.post("/rules/generate/json")
async def gerar_regra_ai_json(request: Request):
    form = await request.form()
    instrucao = form["instrucao"]

    from ollama_client import gerar_regra
    nova_regra = gerar_regra(instrucao)

    if nova_regra:
        rules_store.append(nova_regra)
        save_rules()
        return JSONResponse(content={
            "message": "✅ Regra gerada com sucesso!",
            "rule": nova_regra
        })
    else:
        return JSONResponse(status_code=400, content={
            "message": "❌ Erro ao gerar regra com IA."
        })

@app.post("/rules/generate/json")
async def gerar_regra_ai_json(request: Request):
    form = await request.form()
    instrucao = form["instrucao"]

    from ollama_client import gerar_regra
    nova_regra = gerar_regra(instrucao)

    if nova_regra:
        rules_store.append(nova_regra)
        save_rules()
        return JSONResponse({"message": "Regra gerada com sucesso!", "rule": nova_regra})
    else:
        return JSONResponse({"message": "Erro ao gerar regra com IA"}, status_code=400)
    
@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/chat")
async def chat(message: str = Form(...)):
    resposta = gerar_resposta_ai(message)
    return JSONResponse({"resposta": resposta})

if __name__ == "__main__":
    threading.Thread(target=start_scheduler).start()
