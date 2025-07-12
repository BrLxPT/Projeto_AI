from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from rules_engine import evaluate_rule
from typing import List, Dict
from storage import load_rules, save_rules
from scheduler import start_scheduler
from models import Rule
import threading
import json, uuid

app = FastAPI()
rules_store = load_rules()

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

@app.post("/evaluate")
def evaluate_rules():
    triggered_rules = []
    for rule in rules_store:
        result = evaluate_rule(rule.rule, rule.context)
        if result["triggered"]:
            triggered_rules.append({
                "rule": rule.rule,
                "reason": result["reason"],
                "action": rule.context.get("action", {})
            })
    return{"triggered_rules": triggered_rules}

@app.get("/")
def hello():
    return{"msg": "API de automações com AI ativa!"}

if __name__ == "__main__":
    threading.Thread(target=start_scheduler).start()