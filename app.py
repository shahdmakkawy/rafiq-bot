from fastapi import FastAPI
from pydantic import BaseModel
import os

from langchain_openai import ChatOpenAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.messages import HumanMessage, SystemMessage

app = FastAPI()

# -----------------------------
# API KEY
os.environ["OPENROUTER_API_KEY"] = "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"

# -----------------------------

# Embeddings (CPU عشان السيرفر)

embeddings = HuggingFaceEmbeddings( 
    # model_name="BAAI/bge-m3",
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={'device': 'cpu'}
 )
# -----------------------------

# Vector DB

 db_directory = "./chroma_db_AI_Regulation"
 vector_db = Chroma(
    persist_directory=db_directory,
    embedding_function=embeddings,
 )

# -----------------------------

# LLM
 llm = ChatOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"], 
    model="google/gemini-2.0-flash-001",
    temperature=0
)
# -----------------------------

# Request schema
class Message(BaseModel):
    text: str

# -----------------------------
# شخصية ونيس
system_instruction = """أنت "ونيس"، الصديق الأكاديمي الذكي لطلاب برنامج الذكاء الاصطناعي بجامعة المنصورة.

شخصيتك:
أنت "السينير" الجدع، المثقف، واللبق. أسلوبك فيه مودة واحترام، كأنك بتنصح أخوك الصغير أو زميلك في الكلية.

قواعد:
- استخدم ألفاظ زي: يا بطل، يا هندسة
- بلاش رسمية زيادة
- اذكر رقم المادة لو موجود
- لو مش عارف الإجابة قول بصراحة

ابدأ بتحية لطيفة وانهي بتشجيع."""
# -----------------------------

# دالة ونيس
"""
def ask_wanis(question):
    results = vector_db.similarity_search(question, k=3)
    context = "\n\n---\n\n".join([doc.page_content for doc in results])

    user_prompt = f"السياق:\n{context}\n\nسؤال الطالب: {question}"

    response = llm.invoke([
        SystemMessage(content=system_instruction),
        HumanMessage(content=user_prompt)
    ])

    return response.content
 """

def ask_wanis(question):
    try:
        results = vector_db.similarity_search(question, k=3)
        context = "\n\n---\n\n".join([doc.page_content for doc in results])
    except Exception as e:
        return f"مشكلة في الداتا يا هندسة 😅: {str(e)}"

    try:
        response = llm.invoke([
            SystemMessage(content=system_instruction),
            HumanMessage(content=f"السياق:\n{context}\n\nسؤال الطالب: {question}")
        ])
        return response.content
    except Exception as e:
        return f"مشكلة في الموديل 😅: {str(e)}"

# -----------------------------

# Routes
@app.get("/")
def home():
    return {"message": "wanis is running 🚀"}

@app.post("/chat")
def chat(msg: Message):
    answer = ask_wanis(msg.text)
    return {"response": answer}

# import uvicorn
# if __name__ == "__main__":
#    port = int(os.environ.get("PORT", 10000)) 
#    uvicorn.run(app, host="0.0.0.0", port=port)


