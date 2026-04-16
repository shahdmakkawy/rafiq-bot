from fastapi import FastAPI
from pydantic import BaseModel
from utils import ask_wanis

app = FastAPI()

class ChatRequest(BaseModel):
    question: str

@app.get("/")
def read_root():
    return {"message": "Rafiq API is running!"}

@app.post("/ask")
async def chat_endpoint(request: ChatRequest):
    answer = ask_wanis(request.question)
    return {"answer": answer}
