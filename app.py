from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Optional
from utils import ask_wanis

app = FastAPI()

# تعريف شكل البيانات المستقبلة من الـ Backend
class ChatRequest(BaseModel):
    question: str
    # تاريخ المحادثة (آخر 6-10 رسائل) لتمكين البوت من تذكر السياق
    history: Optional[List[Dict[str, str]]] = []
    # بيانات الطالب (سنة، تخصص، حالة) لتخصيص الردود
    student_profile: Optional[Dict[str, str]] = {}

@app.get("/")
def read_root():
    return {"message": "Rafiq API is running!"}

@app.post("/ask")
async def chat_endpoint(request: ChatRequest):
    # تمرير البيانات لـ ask_wanis لجعل الردود مخصصة بناءً على بروفايل الطالب وتاريخ المحادثة
    answer = ask_wanis(
        question=request.question, 
        history=request.history, 
        student_profile=request.student_profile
    )
    return {"answer": answer}
    
"""
@app.post("/ask")
async def chat_endpoint(request: ChatRequest):
    answer = ask_wanis(request.question)
    return {"answer": answer}
"""
