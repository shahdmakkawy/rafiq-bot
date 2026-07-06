import os
from pinecone import Pinecone
import requests
import json
from dotenv import load_dotenv

load_dotenv()

# connecting with Pinecone
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("wanis-index")

# 🧠 ذاكرة مؤقتة لحفظ تاريخ المحادثات لكل طالب بناءً على الـ ID بتاعه
STUDENT_CHATS_HISTORY = {}

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

def ask_wanis(question: str, student_id: str = "default_student", student_profile: dict = None):
    # 1. سحب الهيستوري القديم للطالب ده لو موجود، لو مش موجود بنعمله قائمة فاضية
    if student_id not in STUDENT_CHATS_HISTORY:
        STUDENT_CHATS_HISTORY[student_id] = []
        
    history = STUDENT_CHATS_HISTORY[student_id]
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

        # 3. ترتيب الرسائل (System + التاريخ القديم)
        messages = [{"role": "system", "content": system_prompt}]
        for msg in history[-10:]:  # بناخد آخر 10 رسائل بس عشان الـ Tokens
            messages.append(msg)
            
        user_input = f"بناءً على معلومات اللائحة التالية:\n{context}\n\nالسؤال: {question}"
        messages.append({"role": "user", "content": user_input})

        # 4. إرسال الطلب لـ Groq API الصاروخي والمجاني (تحديث الموديل لـ Llama 3.1 المدعوم حالياً)
        groq_key = os.getenv("GROQ_API_KEY")
        url = "https://api.groq.com/openai/v1/chat/completions"
        
        response = requests.post(
            url=url,
            headers={
                "Authorization": f"Bearer {groq_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.1-8b-instant",  # الاسم الجديد للموديل الأحدث المدعوم مجاناً من Groq
                "messages": messages,
                "temperature": 0.3
            }
        )
        
        response_data = response.json()
        
        # التأكد من أن الرد رجع سليماً وقراءة الإجابة
        if 'choices' in response_data and len(response_data['choices']) > 0:
            bot_answer = response_data['choices'][0]['message']['content']
            
            # 💾 حفظ السؤال والرد في ذاكرة الطالب عشان المرة الجاية يفتكرهم
            STUDENT_CHATS_HISTORY[student_id].append({"role": "user", "content": question})
            STUDENT_CHATS_HISTORY[student_id].append({"role": "assistant", "content": bot_answer})
            
            return bot_answer
        else:
            # طباعة الخطأ في سيرفر ريندر لو حصلت مشكلة عشان تظهر في الـ Logs
            print("Groq Error Response:", response_data)
            return f"خطأ من سيرفر Groq: {json.dumps(response_data)}"
        
    except Exception as e:
        return f"حصل خطأ بسيط: {str(e)}"
