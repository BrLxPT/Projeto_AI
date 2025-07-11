from pydantic import BaseModel

class Rule(BaseModel):
    id: str
    condition: str
    action: dict