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
    api_key = os.getenv("X_AI_API_KEY") 
    headers = {
        "X-AI-API-KEY": api_key, 
        "Content-Type": "application/json"
    }
    return None

def ask_wanis(question: str, student_id: str = "default_student", student_profile: dict = None):
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
        
        # الـ Prompt الأصلي بتاعك بالملي وبدون تعديل حرف واحد
        system_instruction = """أنت "رفيق"، الصديق الأكاديمي الذكي لطلاب برنامج الذكاء الاصطناعي بجامعة المنصورة.\n\n\n
شخصيتك:
أنت "السينير" الجدع، المثقف، واللبق. أسلوبك فيه مودة واحترام، كأنك بتنصح أخوك الصغير أو زميلك في الكلية. ابعد عن الرسمية المتخشبية وفي نفس الوقت خليك رزين.

قواعد التعامل المحدثة:
1. المسميات: استخدم مسميات مناسبة زي (يا بطل، يا هندسة، يا بشمهندس/بشمهندسة). بلاش كلمة "دكتور" إلا لو الطالب هو اللي قال إنه دكتور.
2. حذف الأكواد التقنية: ممنوع تماماً ذكر الأكواد الرقمية الغريبة اللي بتظهر بين الأقواس زي [1 0 1 1] أو [2 0 1 2]. الطالب مش بيفهمها وبتبوظ شكل الإجابة. اذكر رقم المادة فقط بشكل طبيعي.
3. الدقة الرقمية: مصدرك الوحيد هو "سياق اللائحة". لما الطالب يسأل عن أرقام (ساعات، GPA، تقديرات)، استخرجها بدقة ومتاكد منها 100%.
4. التوثيق الودي: اذكر المصدر في نهاية كلامك بلطافة، مثلاً: "وده حسب المادة 12 في اللائحة".
5. لو المعلومة مش موجودة: قول بذكاء: "بص يا بطل، دورت لك في اللائحة يمين وشمال بس النص ده مش واضح عندي، فالأضمن اسأل شؤون الطلاب أو إدارة البرنامج".
6. البداية والنهاية: ابدأ بترحيب لطيف (نورت يا هندسة، أهلاً يا بطل)، وانتهي بدعوة تشجع الطالب (بالتوفيق يا عالم المستقبل، شد حيلك يا بطل)."""

        # 3. ترتيب الرسائل للحفاظ على الذاكرة
        messages = [{"role": "system", "content": system_instruction}]
        for msg in history[-6:]:  
            messages.append(msg)
            
        user_input = (
            f"سياق ومعلومات اللائحة:\n{context}\n\n"
            f"بيانات الطالب الحالي للتخصيص:\n"
            f"- المستوى الأكاديمي: {level}\n"
            f"- التخصص الدراسي: {dept}\n"
            f"- الحالة الدراسية: {status}\n"
            f"- المعدل التراكمي الحاضر (GPA): {gpa}\n"
            f"- المواد المتعثر فيها الطالب: {failed_courses}\n\n"
            f"سؤال الطالب: {question}"
        )
        messages.append({"role": "user", "content": user_input})

        # 4. إرسال الطلب لـ Groq بالموديل المتاح والشغال والمدعوم رسمياً حالياً
        groq_key = os.getenv("GROQ_API_KEY")
        url = "https://api.groq.com/openai/v1/chat/completions"
        
        response = requests.post(
            url=url,
            headers={
                "Authorization": f"Bearer {groq_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.1-8b-instant",  # الاسم التقني الصحيح والمتاح رسمياً
                "messages": messages,
                "temperature": 0.0  # صفر حاسم لمنع التكرار والتهنيج في الصياغة العربية
            }
        )
        
        response_data = response.json()
        
        if 'choices' in response_data and len(response_data['choices']) > 0:
            bot_answer = response_data['choices'][0]['message']['content']
            
            # 💾 حفظ الذاكرة
            STUDENT_CHATS_HISTORY[student_id].append({"role": "user", "content": question})
            STUDENT_CHATS_HISTORY[student_id].append({"role": "assistant", "content": bot_answer})
            
            return bot_answer
        else:
            print("Groq Error Response:", response_data)
            return f"خطأ من سيرفر Groq: {json.dumps(response_data)}"
        
    except Exception as e:
        return f"حصل خطأ بسيط: {str(e)}"
