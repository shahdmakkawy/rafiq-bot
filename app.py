from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Optional, Tuple
# توحيد اسم الدالة المستوردة من ملف utils
from utils import ask_wanis

app = FastAPI(title="Rafiq AI Bot API", version="1.0")

# تعريف شكل البيانات المستقبلة من الـ Frontend أو الـ Mobile
class ChatRequest(BaseModel):
    question: str
    student_id: Optional[str] = "default_student"
    student_profile: Optional[Dict[str, str]] = {}
    chat_history: Optional[List[Tuple[str, str]]] = []

@app.get("/")
def read_root():
    return {"message": "Rafiq API is running successfully!"}

@app.post("/ask")
async def chat_endpoint(request: ChatRequest):
    # تمرير السؤال، الـ ID، وبيانات الطالب للدالة الذكية المحدثة
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
