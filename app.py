from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Optional
from utils import ask_wanis

app = FastAPI()

# Backend تعريف شكل البيانات المستقبلة من الـ
class ChatRequest(BaseModel):
    student_id: str = "default_student"  # معرف الطالب لربط الذاكرة والهيستوري
    question: str
    student_profile: Optional[Dict[str, str]] = {}

@app.get("/")
def read_root():
    return {"message": "Rafiq API is running!"}

@app.post("/ask")
async def chat_endpoint(request: ChatRequest):
    # لعمل الردود مخصصة بناءً على بروفايل الطالب وتاريخ المحادثة نمرر البيانات لـ ask_wanis
    answer = ask_wanis(
        question=request.question,
        student_id=request.student_id,
        student_profile=request.student_profile
    )
    return {"answer": answer}
    
"""
@app.post("/ask")
async def chat_endpoint(request: ChatRequest):
    answer = ask_wanis(request.question)
    return {"answer": answer}
"""
