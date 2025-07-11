import json
from typing import List
from models import Rule

RULES_FILE = "data/rules.json"

def load_rules()->list[Rule]:
    try:
        with open(RULES_FILE, "r") as f:
            data = json.load(f)
            return [Rule(**r) for r in data]
    except FileNotFoundError:
        return[]
    except Exception as e:
        print(f"Erro ao carregar regras: {e}")
        return[]
    
def save_rules(rules: List[Rule]):
    try:
        with open(RULES_FILE, "w") as f:
            json.dump([r.dict() for r in rules], f, indent=2)
    except Exception as e:
        print(f"Erro ao guardar regras: {e}")