from fastapi import FastAPI
from pydantic import BaseModel
from utils import ask_wanis

app = FastAPI()

from pydantic import BaseModel
from typing import List, Dict, Optional

class ChatRequest(BaseModel):
    question: str
    # تاريخ المحادثة: قائمة فيها رسايل قديمة، لو مبعتوش حاجة هتبقى فاضية []
    history: Optional[List[Dict[str, str]]] = [] [cite: 7, 22]
    # بيانات الطالب: قاموس فيه (سنة، تخصص، حالة)، لو مبعتوش حاجة هتبقى فاضية {}
    student_profile: Optional[Dict[str, str]] = {} [cite: 8, 9]

"""
class ChatRequest(BaseModel):
    question: str
"""
@app.get("/")
def read_root():
    return {"message": "Rafiq API is running!"}

@app.post("/ask")
async def chat_endpoint(request: ChatRequest):
    answer = ask_wanis(request.question)
    return {"answer": answer}
