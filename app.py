from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Optional, Tuple
# توحيد اسم الدالة المستوردة من ملف utils
from utils import ask_rafiq

app = FastAPI(title="Rafiq AI Bot API", version="1.0")

# تعريف شكل البيانات المستقبلة من الـ Frontend أو الـ Mobile
class ChatRequest(BaseModel):
    question: str
    student_id: str = "default_student"
    student_profile: Optional[Dict[str, str]] = {}
    # إضافة حقل الهيستوري هنا عشان يستقبل الذاكرة من الفرونت إند
    # الهيستوري بيتبعت كقائمة من الأزواج: [["سؤال الطالب السابق", "رد البوت السابق"]]
    chat_history: Optional[List[Tuple[str, str]]] = []

@app.get("/")
def read_root():
    return {"message": "Rafiq API is running successfully!"}

@app.post("/ask")
async def chat_endpoint(request: ChatRequest):
    # تمرير السؤال وقائمة الهيستوري للدالة الذكية المحدثة
    answer = ask_rafiq(
        question=request.question,
        chat_history_list=request.chat_history
    )
    
    return {"answer": answer}
    
"""
@app.post("/ask")
async def chat_endpoint(request: ChatRequest):
    answer = ask_wanis(request.question)
    return {"answer": answer}
"""
