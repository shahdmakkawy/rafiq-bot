import os
from pinecone import Pinecone
import requests
import json
from dotenv import load_dotenv

load_dotenv()

# 🧠 ذاكرة مؤقتة لحفظ تاريخ المحادثات لكل طالب
STUDENT_CHATS_HISTORY = {}

# تحميل ملف اللائحة الـ JSON كـ خط دفاع بديل (Fallback) محلي
REGULATION_DATA = []
try:
    # تأكدي أن ملف الـ JSON مرفوع بنفس الاسم في فولدر المشروع على السيرفر
    with open("final_regulation_final_clean (3).json", "r", encoding="utf-8") as f:
        REGULATION_DATA = json.load(f)
except Exception as e:
    print(f"Error loading local JSON regulation file: {str(e)}")


def get_embedding_groq(text: str):
    try:
        groq_key = os.getenv("GROQ_API_KEY")
        url = "https://api.groq.com/openai/v1/embeddings"
        
        response = requests.post(
            url=url,
            headers={
                "Authorization": f"Bearer {groq_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "nomic-embed-text-v1.5",
                "input": text
            },
            timeout=5
        )
        res_data = response.json()
        return res_data['data'][0]['embedding']
    except Exception as e:
        print(f"Embedding Error: {str(e)}")
        return [0] * 1024


def search_local_json(question: str, top_k=3):
    """
    مسترجع محلي بسيط يبحث بالكلمات المفتاحية في ملف الـ JSON 
    في حال عطل Pinecone السحابي تماماً لمنع توقف البوت.
    """
    results = []
    # تنظيف كلمات البحث
    words = [w for w in question.split() if len(w) > 2]
    
    for item in REGULATION_DATA:
        text_content = item.get("text", "")
        # حساب عدد الكلمات المتطابقة ببساطة كـ fallback سريع
        score = sum(1 for word in words if word in text_content)
        if score > 0:
            results.append((score, text_content))
            
    # ترتيب النتائج وأخذ الـ top_k
    results.sort(key=lambda x: x[0], reverse=True)
    return "\n".join([res[1] for res in results[:top_k]])


def ask_wanis(question: str, student_id: str = "default_student", student_profile: dict = None):
    if student_id not in STUDENT_CHATS_HISTORY:
        STUDENT_CHATS_HISTORY[student_id] = []
        
    history = STUDENT_CHATS_HISTORY[student_id]
    student_profile = student_profile or {}
    
    context = ""
    
    # 1. محاولة جلب سياق اللائحة عبر الـ Embedding والبحث في Pinecone
    try:
        pinecone_key = os.getenv("PINECONE_API_KEY")
        groq_key = os.getenv("GROQ_API_KEY")
        
        if pinecone_key and groq_key:
            # تحويل سؤال الطالب لـ Vector حقيقي
            query_vector = get_embedding_groq(question)
            
            # البحث في Pinecone بالـ Vector الحقيقي
            pc = Pinecone(api_key=pinecone_key)
            index = pc.Index("wanis-index")
            
            search_results = index.query(
                vector=query_vector, 
                top_k=3,
                include_metadata=True
            )
            
            matches = search_results.get('matches', [])
            if matches:
                context = "\n".join([match['metadata']['text'] for match in matches if 'metadata' in match and 'text' in match['metadata']])
            
        # إذا لم نجد أي سياق مسترجع من Pinecone، نلجأ فوراً للـ Fallback المحلي من الـ JSON
        if not context and REGULATION_DATA:
            print("Pinecone returned empty results. Falling back to local JSON search...")
            context = search_local_json(question, top_k=3)
            
    except Exception as e:
        print(f"Pinecone/Embedding Error: {str(e)}")
        # في حالة حدوث أي Exception في Pinecone، نستخدم الـ Fallback المحلي ونمنع العطل
        if REGULATION_DATA:
            print("Exception caught. Falling back to local JSON search...")
            context = search_local_json(question, top_k=3)
        else:
            context = "تعذر استخراج سياق اللائحة حالياً بسبب عطل في قاعدة البيانات."

    # 2. بناء الـ System Message وتخصيص بيانات الطالب الدراسية
    level = student_profile.get('level', 'غير محدد')
    dept = student_profile.get('department', 'عام')
    status = student_profile.get('status', 'منتظم')
    gpa = student_profile.get('gpa', 'غير متوفر')
    failed_courses = student_profile.get('failed_courses', 'لا يوجد')
    
    system_instruction = f"""أنت "رفيق"، المساعد الأكاديمي الذكي لطلاب برنامج الذكاء الاصطناعي بجامعة المنصورة. 

أجب عن سؤال الطالب بناءً على "سياق اللائحة" (Context) المرفق و"ملف الطالب" (Student Profile) أدناه فقط.

بيانات الطالب الحالية:
- المستوى الدراسي: {level}
- القسم/البرنامج: {dept}
- المعدل التراكمي (GPA): {gpa}
- المواد الراسب فيها: {failed_courses}

سياق اللائحة المسترجع:
{context}

تعليمات صياغة الرد (هامة جداً):
1. صغ إجابتك بالعامية المصرية الودية والواضحة مباشرة (مثال: "أهلاً يا هندسة، بناءً على اللائحة وبياناتك...").
2. ممنوع تماماً كتابة رموز برمجية أو علامات غريبة مثل \\n أو n1 أو n2 في نص الإجابة. اكتب الشروط في نقاط واضحة ومقروءة تفهمها العين.
3. قارن بيانات الطالب مباشرة بشروط اللائحة المرفقة، وقل له بثقة هل هو مؤهل لتسجيل مشروع التخرج أم لا (مثال: طالما مسجل 120 ساعة ومعدلك فوق 2، إذن أنت مؤهل تماماً!).
4. إذا لم تجد شروطاً واضحة تناسب السؤال في السياق المرفق، قل له مباشرة وبدون تردد: "النقطة دي بالتفصيل مش واضحة في المواد اللي معايا يا بطل، عشان مصلحتك اتأكد من شؤون الطلاب". وممنوع تأليف أي أرقام من دماغك.
"""

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
    
    # 3. استدعاء الموديل من الـ APIs مع نظام الـ Fallback
    try:
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
                "temperature": 0.2  # جعلناه 0.2 لضمان عدم الهلوسة والالتزام بالنص
            },
            timeout=10
        )
        or_data = or_response.json()
        if 'choices' in or_data and len(or_data['choices']) > 0:
            bot_answer = or_data['choices'][0]['message']['content']
        else:
            raise Exception("OpenRouter failed")
            
    except Exception:
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
                    "temperature": 0.2  # جعلناه 0.2 للالتزام التام بالتعليمات
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

    if bot_answer:
        bot_answer = bot_answer.replace("\\n", "\n").replace("\\\\n", "\n").replace(r"\n", "\n").strip()
        STUDENT_CHATS_HISTORY[student_id].append({"role": "user", "content": question})
        STUDENT_CHATS_HISTORY[student_id].append({"role": "assistant", "content": bot_answer})
        
    return bot_answer
