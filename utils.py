import os
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
import requests
import json

load_dotenv()

# 1. إعداد الـ Embeddings (موديل البحث) - هنستخدم موديل أصغر شوية عشان Render
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# 2. تحميل قاعدة البيانات (تأكدي إن فولدر chroma_db_AI_Regulation مرفوع على GitHub)
db_directory = os.path.join(os.path.dirname(__file__), "chroma_db_AI_Regulation")
vector_db = Chroma(persist_directory=db_directory, embedding_function=embeddings)

API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL_NAME = "google/gemini-2.0-flash-001"

def ask_wanis(question: str):
    try:
        # البحث في اللائحة كلها (دي أهم حتة إنتي عايزياها)
        results = vector_db.similarity_search(question, k=3)
        context = "\n\n".join([doc.page_content for doc in results])
        
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
            },
            data=json.dumps({
                "model": MODEL_NAME,
                "messages": [
                    {"role": "system", "content": "أنت 'ونيس'، صديق أكاديمي لطلاب جامعة المنصورة. استخدم السياق التالي فقط للرد بدقة من اللائحة."},
                    {"role": "user", "content": f"السياق: {context}\n\nالسؤال: {question}"}
                ]
            })
        )
        result = response.json()
        return result['choices'][0]['message']['content']
    except Exception as e:
        return f"حصل خطأ: {str(e)}"








"""
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

# 1. إعدادات المفتاح
API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL_NAME = "google/gemini-2.0-flash-001"

# 2. دالة قراءة اللائحة من ملف الـ JSON
def get_context_from_json(question: str):
    try:
        # تأكدي إن الملف ده مرفوع فعلاً بنفس الاسم على GitHub
        json_path = os.path.join(os.path.dirname(__file__), "final_regulation_final_clean.json")
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            # هنبعت أول جزء من البيانات كـ "سياق" مؤقتاً
            context = str(data)[:3000] 
            return context
    except Exception as e:
        print(f"Error reading JSON: {e}")
        return ""

def ask_wanis(question: str):
    try:
        context = get_context_from_json(question)
        
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
            },
            data=json.dumps({
                "model": MODEL_NAME,
                "messages": [
                    {"role": "system", "content": "أنت 'ونيس'، صديق أكاديمي لطلاب جامعة المنصورة. لخص المعلومات من اللائحة بأسلوب ودي وشرح بسيط."},
                    {"role": "user", "content": f"السياق: {context}\n\nالسؤال: {question}"}
                ]
            })
        )
        
        result = response.json()
        return result['choices'][0]['message']['content']

    except Exception as e:
        return f"حصل خطأ بسيط يا بطل: {str(e)}"


-------------------------------------
import requests
import json
import os
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# تحميل الإعدادات من ملف .env
load_dotenv()

# 1. إعداد الـ Embeddings (موديل البحث)
embeddings = HuggingFaceEmbeddings(
    model_name="BAAI/bge-m3",
    model_kwargs={'device': 'cpu'}
)

# 2. تحميل قاعدة البيانات
db_directory = "./chroma_db_AI_Regulation"
vector_db = Chroma(persist_directory=db_directory, embedding_function=embeddings)

# 3. إعدادات OpenRouter (بيسحب المفتاح من البيئة المحيطة)
API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL_NAME = "google/gemini-2.0-flash-001"

def ask_wanis(question: str):
    try:
        # البحث في اللائحة
        results = vector_db.similarity_search(question, k=2)
        context = "\n\n".join([doc.page_content for doc in results])
        
        if not context:
            return "يا بطل، دورت في اللائحة ومش لاقي إجابة واضحة بخصوص سؤالك."

        # الربط بـ OpenRouter
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
            },
            data=json.dumps({
                "model": MODEL_NAME,
                "messages": [
                    {"role": "system", "content": "أنت 'ونيس'، صديق أكاديمي لطلاب جامعة المنصورة. لخص المعلومات من اللائحة بأسلوب ودي وشرح بسيط كأنك شات بوت."},
                    {"role": "user", "content": f"السياق: {context}\n\nالسؤال: {question}"}
                ]
            })
        )
        
        result = response.json()
        
        if "error" in result:
            return f"مشكلة في المفتاح: {result['error']['message']}"
            
        return result['choices'][0]['message']['content']

    except Exception as e:
        return f"حصل خطأ يا بطل: {str(e)}"
---------------------------------------------------------
import requests
import json
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# 1. رجعنا الموديل اللي إنتي عايزاه (التقيل بس القوي)
embeddings = HuggingFaceEmbeddings(
    model_name="BAAI/bge-m3",
    model_kwargs={'device': 'cpu'}
)

# 2. تحميل قاعدة البيانات
db_directory = "./chroma_db_AI_Regulation"
vector_db = Chroma(persist_directory=db_directory, embedding_function=embeddings)

# 3. إعدادات OpenRouter
API_KEY = "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"
MODEL_NAME = "google/gemini-2.0-flash-001"

def ask_wanis(question: str):
    try:
        results = vector_db.similarity_search(question, k=2)
        context = "\n\n".join([doc.page_content for doc in results])
        
        if not context:
            return "يا بطل، مش لاقي إجابة في اللائحة."

        # الربط المباشر بـ requests عشان نضمن إن الـ Key يتقبل
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
            },
            data=json.dumps({
                "model": MODEL_NAME,
                "messages": [
                    {"role": "system", "content": "أنت 'ونيس'، صديق أكاديمي لطلاب جامعة المنصورة. لخص المعلومات من اللائحة بأسلوب ودي وشرح بسيط كأنك شات بوت."},
                    {"role": "user", "content": f"السياق: {context}\n\nالسؤال: {question}"}
                ]
            })
        )
        
        result = response.json()
        
        if "error" in result:
            return f"مشكلة في المفتاح: {result['error']['message']}"
            
        return result['choices'][0]['message']['content']

    except Exception as e:
        return f"حصل خطأ يا بطل: {str(e)}"
"""


















""""
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
import os

# 1. إعداد الـ Embeddings (اللي بيخلي البرنامج يفهم الكلام)
embeddings = HuggingFaceEmbeddings(
    model_name="BAAI/bge-m3",
    model_kwargs={'device': 'cpu'}
)

# 2. تحميل قاعدة بيانات اللائحة
db_directory = "./chroma_db_AI_Regulation"
vector_db = Chroma(persist_directory=db_directory, embedding_function=embeddings)

def ask_wanis(question: str):
    try:
        # البحث عن أكثر المعلومات صلة بسؤال الطالب
        results = vector_db.similarity_search(question, k=2)
        
        # تجميع النصوص اللي لقاها في اللائحة
        context = "\n\n".join([doc.page_content for doc in results])
        
        if not context:
            return "يا بطل، دورت في اللائحة ومش لاقي معلومة محددة بخصوص سؤالك، حاول تسأل بطريقة تانية."

        # الرد النهائي بأسلوب ونيس ومنظم جداً
        friendly_response = (
            f"أهلاً بك يا بطل! دورت لك في اللائحة وده اللي لقيته بخصوص سؤالك:\n\n"
            f"{context}\n\n"
            f"أتمنى تكون الإجابة وضحت لك، ولو محتاج أي حاجة تانية أنا موجود! 😊"
        )
        return friendly_response

    except Exception as e:
        return f"يا بطل حصلت مشكلة فنية بسيطة: {str(e)}"
    
    """
