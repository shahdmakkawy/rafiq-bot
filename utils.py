import os
from pinecone import Pinecone
import requests
import json
from dotenv import load_dotenv

load_dotenv()

# connecting with Pinecone
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("wanis-index")

# connecting with the back-end
def get_real_student_data(student_id):
    """
    #this function will use the API that we used in Render, to make use the real data instead the fake one
    """
    api_key = os.getenv("X_AI_API_KEY") 
    
    headers = {
        "X-AI-API-KEY": api_key, 
        "Content-Type": "application/json"
    }
    return None

def ask_wanis(question: str, history: list = None, student_profile: dict = None):
    history = history or []
    student_profile = student_profile or {}
    
    try:
        # 1. search in Pinecone
        search_results = index.query(
            vector=[0]*1024, 
            top_k=3,
            include_metadata=True
        )
        
        context = "\n".join([match['metadata']['text'] for match in search_results['matches']])

        # 2. بناء الـ System Message ببيانات الطالب
        level = student_profile.get('level', 'غير محدد')
        dept = student_profile.get('department', 'عام')
        status = student_profile.get('status', 'منتظم')
        gpa = student_profile.get('gpa', 'غير متوفر')
        failed_courses = student_profile.get('failed_courses', 'لا يوجد')
        
        system_prompt = (
            f"أنت 'رفيق' مساعد أكاديمي ذكي لطلاب حاسبات المنصورة. "
            f"أنت تتحدث الآن مع طالب في {level}، تخصص {dept}، وحالته {status}. "
            f"بياناته الحالية: GPA هو {gpa}، والمواد المتعثر فيها هي: {failed_courses}. "
            "مهمتك ليست فقط الإجابة، بل تقديم نصيحة أكاديمية ذكية: "
            "1. إذا كان الـ GPA منخفضاً، انصحه بتقليل عدد الساعات والتركيز على رفع التقدير. "
            "2. إذا كان متعثراً في مادة هي 'متطلب' لمواد أخرى, نبهه لخطورة ذلك وأولوية تسجيلها. "
            "3. إذا كان متفوقاً، شجعه على تسجيل ساعات إضافية (Overload) إذا سمحت اللائحة. "
            "اجعل نصيحتك ودودة، تشجيعية، ومبنية دائماً على نصوص اللائحة المرفقة."
        )

        # 3. messages ordering 
        messages = [{"role": "system", "content": system_prompt}]
        for msg in history[-10:]:
            messages.append(msg)
            
        user_input = f"بناءً على معلومات اللائحة التالية:\n{context}\n\nالسؤال: {question}"
        messages.append({"role": "user", "content": user_input})

        # 4. sending a request to the used model using OpenRouter
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
                "Content-Type": "application/json"
            },
            data=json.dumps({
                "model": "meta-llama/llama-3-8b-instruct:free",  # الموديل المجاني الشغال والمستقر حالياً
                "messages": messages,
                "temperature": 0.3
            })
        )
        
        response_data = response.json()
        if 'choices' in response_data:
            return response_data['choices'][0]['message']['content']
        else:
            # لو في مشكلة في المفتاح أو السيرفر، هيطبعهالك بالملي في الـ Swagger عشان نقراها
            return f"خطأ من سيرفر OpenRouter: {json.dumps(response_data)}"
        
    except Exception as e:
        return f"حصل خطأ بسيط: {str(e)}"



"""
import os
from pinecone import Pinecone
import requests
import json
from dotenv import load_dotenv

load_dotenv()

# connecting with Pinecone
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("wanis-index")

#  connecting with the back-end
def get_real_student_data(student_id):

    #this function will use the API that we used in Render, to make use the real data instead the fake one
    api_key = os.getenv("X_AI_API_KEY") # سحب المفتاح من ريندر 
    
    headers = {
        "X-AI-API-KEY": api_key, 
        "Content-Type": "application/json"
    }
    
    # the URL of the bach-end
    # url = f"https://api.backend.com/student/{student_id}"
    # response = requests.get(url, headers=headers)
    # return response.json()
    return None

def ask_wanis(question: str, history: list = None, student_profile: dict = None):
    history = history or []
    student_profile = student_profile or {}
    
    try:
        # 1. search in Pinecone
        search_results = index.query(
            vector=[0]*1024, 
            top_k=3,
            include_metadata=True
        )
        
        context = "\n".join([match['metadata']['text'] for match in search_results['matches']])

        # 2. بناء الـ System Message ببيانات الطالب
        level = student_profile.get('level', 'غير محدد')
        dept = student_profile.get('department', 'عام')
        status = student_profile.get('status', 'منتظم')
        gpa = student_profile.get('gpa', 'غير متوفر')
        failed_courses = student_profile.get('failed_courses', 'لا يوجد')
        
        system_prompt = (
            f"أنت 'رفيق' مساعد أكاديمي ذكي لطلاب حاسبات المنصورة. "
            f"أنت تتحدث الآن مع طالب في {level}، تخصص {dept}، وحالته {status}. "
            f"بياناته الحالية: GPA هو {gpa}، والمواد المتعثر فيها هي: {failed_courses}. "
            "مهمتك ليست فقط الإجابة، بل تقديم نصيحة أكاديمية ذكية: "
            "1. إذا كان الـ GPA منخفضاً، انصحه بتقليل عدد الساعات والتركيز على رفع التقدير. "
            "2. إذا كان متعثراً في مادة هي 'متطلب' لمواد أخرى، نبهه لخطورة ذلك وأولوية تسجيلها. "
            "3. إذا كان متفوقاً، شجعه على تسجيل ساعات إضافية (Overload) إذا سمحت اللائحة. "
            "اجعل نصيحتك ودودة، تشجيعية، ومبنية دائماً على نصوص اللائحة المرفقة."
        )

        # 3. messages ordering 
        messages = [{"role": "system", "content": system_prompt}]
        for msg in history[-10:]:
            messages.append(msg)
            
        user_input = f"بناءً على معلومات اللائحة التالية:\n{context}\n\nالسؤال: {question}"
        messages.append({"role": "user", "content": user_input})

        # 4. sending a requed to the used model using OpenRouter
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
                "Content-Type": "application/json"
            },
            data=json.dumps({
                "model": "google/gemma-2-9b-it:free",
                "messages": messages,
                "temperature": 0.3
            })
        )
        return response.json()['choices'][0]['message']['content']
        
    except Exception as e:
        return f"حصل خطأ بسيط: {str(e)}"
"""
