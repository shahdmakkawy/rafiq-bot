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
        
        system_instruction = """أنت "رفيق"، الصديق الأكاديمي الذكي لطلاب برنامج الذكاء الاصطناعي بجامعة المنصورة.


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
        for msg in history[-4:]:  
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

        bot_answer = ""
        
        # 4. الـ Fallback Logic الصامت تماماً باستخدام الـ APIs مباشرة
        try:
            # الخيار الأول: محاولة استخدام OpenRouter للحصول على أفضل جودة
            openrouter_key = os.getenv("OPENROUTER_API_KEY")
            or_url = "https://openrouter.ai/api/v1/chat/completions"
            
            or_response = requests.post(
                url=or_url,
                headers={
                    "Authorization": f"Bearer {openrouter_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "google/gemma-2-9b-it:free",
                    "messages": messages,
                    "temperature": 0.4
                },
                timeout=10
            )
            or_data = or_response.json()
            if 'choices' in or_data and len(or_data['choices']) > 0:
                bot_answer = or_data['choices'][0]['message']['content']
            else:
                raise Exception("OpenRouter failed or empty choice")
                
        except Exception:
            # الخيار الثاني البديل الصامت: لو OpenRouter وقع، بنروح لـ Groq فوراً
            try:
                groq_key = os.getenv("GROQ_API_KEY")
                groq_url = "https://api.groq.com/openai/v1/chat/completions"
                
                groq_response = requests.post(
                    url=groq_url,
                    headers={
                        "Authorization": f"Bearer {groq_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "llama-3.1-8b-instant",
                        "messages": messages,
                        "temperature": 0.55 # درجة حرارة متوسطة للعامية المصرية المظبوطة في Groq
                    },
                    timeout=10
                )
                groq_data = groq_response.json()
                if 'choices' in groq_data and len(groq_data['choices']) > 0:
                    bot_answer = groq_data['choices'][0]['message']['content']
                else:
                    bot_answer = "بص يا بطل، حصلت مشكلة فنية بسيطة في السيرفر عندي دلوقتي، جرب تسألني تاني كمان ثواني كده."
            except Exception:
                bot_answer = "بص يا بطل، حصلت مشكلة فنية بسيطة في السيرفر عندي دلوقتي، جرب تسألني تاني كمان ثواني كده."

        # 5. تنظيف الـ \n نصية من الـ Output النهائي قبل الرجوع
       # if bot_answer:
       #     bot_answer = bot_answer.replace("\\n", "\n").replace("\\\\n", "\n").strip()
        if bot_answer:
            # التعديل الشامل لتنظيف الرموز النصية وتحويلها لأسطر حقيقية
            bot_answer = bot_answer.replace("\\n", "\n").replace("\\\\n", "\n").replace(r"\n", "\n").strip()    
            
            # 💾 حفظ الذاكرة فقط لو أرجع رد حقيقي
            STUDENT_CHATS_HISTORY[student_id].append({"role": "user", "content": question})
            STUDENT_CHATS_HISTORY[student_id].append({"role": "assistant", "content": bot_answer})
            
        return bot_answer
        
    except Exception as e:
        return f"حصل خطأ بسيط: {str(e)}"
