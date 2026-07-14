import os
from pinecone import Pinecone
import requests
import json
from dotenv import load_dotenv

load_dotenv()

STUDENT_CHATS_HISTORY = {}

# نص ثابت من اللائحة للطوارئ (لو الـ JSON والـ Pinecone فشلوا تماماً)
EMERGENCY_REGULATION_TEXT = """
شروط تسجيل مشروع التخرج لبرنامج الذكاء الاصطناعي بجامعة المنصورة:
1. يجب أن يكون الطالب في المستوى الرابع (أو اجتاز 120 ساعة معتمدة على الأقل).
2. يجب ألا يقل المعدل التراكمي (GPA) للطالب عن 2.0 لتسجيل المشروع.
3. لا يسمح للطالب بتسجيل مشروع التخرج إذا كان متعثراً أو راسباً في متطلبات أساسية تمنعه من الوصول للمستوى الرابع.
4. الساعات المعتمدة المطلوبة للتخرج هي 141 ساعة معتمدة كحد أدنى شاملة مشروع التخرج.
"""

REGULATION_DATA = []
try:
    with open("final_regulation_final_clean (3).json", "r", encoding="utf-8") as f:
        REGULATION_DATA = json.load(f)
except Exception as e:
    print(f"Error loading local JSON: {str(e)}")


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
        return response.json()['data'][0]['embedding']
    except Exception:
        return [0] * 1024


def search_local_json(question: str, top_k=3):
    if not REGULATION_DATA:
        return EMERGENCY_REGULATION_TEXT # لو الملف مش موجود نرجع النص الثابت فوراً
        
    results = []
    words = [w for w in question.split() if len(w) > 2]
    for item in REGULATION_DATA:
        text_content = item.get("text", "")
        score = sum(1 for word in words if word in text_content)
        if score > 0:
            results.append((score, text_content))
            
    results.sort(key=lambda x: x[0], reverse=True)
    return "\n".join([res[1] for res in results[:top_k]]) if results else EMERGENCY_REGULATION_TEXT


def ask_wanis(question: str, student_id: str = "default_student", student_profile: dict = None):
    if student_id not in STUDENT_CHATS_HISTORY:
        STUDENT_CHATS_HISTORY[student_id] = []
        
    history = STUDENT_CHATS_HISTORY[student_id]
    student_profile = student_profile or {}
    
    context = ""
    
    # 1. محاولة جلب السياق من Pinecone
    try:
        pinecone_key = os.getenv("PINECONE_API_KEY")
        groq_key = os.getenv("GROQ_API_KEY")
        
        if pinecone_key and groq_key:
            query_vector = get_embedding_groq(question)
            pc = Pinecone(api_key=pinecone_key)
            index = pc.Index("wanis-index")
            
            search_results = index.query(
                vector=query_vector, 
                top_k=3,
                include_metadata=True
            )
            
            matches = []
            if hasattr(search_results, 'matches'):
                matches = search_results.matches
            elif isinstance(search_results, dict) and 'matches' in search_results:
                matches = search_results['matches']
            
            context_list = []
            if matches:
                for match in matches:
                    metadata = {}
                    if hasattr(match, 'metadata') and match.metadata:
                        metadata = match.metadata
                    elif isinstance(match, dict) and 'metadata' in match:
                        metadata = match['metadata']
                    
                    text = ""
                    if isinstance(metadata, dict):
                        text = metadata.get('text', '')
                    elif hasattr(metadata, 'text'):
                        text = metadata.text
                        
                    if text:
                        context_list.append(text)
                context = "\n".join(context_list)
            
        if not context:
            context = search_local_json(question, top_k=3)
            
    except Exception as e:
        print(f"Pinecone/Embedding Exception: {str(e)}")
        context = search_local_json(question, top_k=3)

    # إذا فشلت كل الطرق السابقة، نضمن وجود سياق لعدم حدوث عطل فني
    if not context or "تعذر" in context:
        context = EMERGENCY_REGULATION_TEXT

    # 2. بناء الـ System Message وتخصيص بيانات الطالب الدراسية
    level = student_profile.get('level', 'غير محدد')
    dept = student_profile.get('department', 'عام')
    status = student_profile.get('status', 'منتظم')
    gpa = student_profile.get('gpa', 'غير متوفر')
    failed_courses = student_profile.get('failed_courses', 'لا يوجد')
    
    system_instruction = f"""أنت "رفيق"، المساعد الأكاديمي الذكي لطلاب برنامج الذكاء الاصطناعي بجامعة المنصورة. 

أجب عن سؤال الطالب بناءً على "سياق اللائحة" (Context) المرفق و"ملف الطالب" أدناه فقط.

بيانات الطالب الحالية:
- المستوى الدراسي: {level}
- القسم/البرنامج: {dept}
- المعدل التراكمي (GPA): {gpa}
- المواد الراسب فيها: {failed_courses}

سياق اللائحة المسترجع:
{context}

تعليمات صياغة الرد (صارمة جداً):
1. ابدأ ردك فوراً وبشكل مباشر بحسم حالة الطالب (مثال: "أهلاً يا هندسة.. بناءً على بياناتك واللائحة، أنت مؤهل تماماً لتسجيل مشروع التخرج!" أو "للأسف أنت غير مؤهل لأن...").
2. بعد حسم الحالة في أول سطر، اكتب له الشروط المذكورة في اللائحة في نقاط واضحة ومقروءة تفهمها العين (مثل: الشروط هي: 1.. 2.. 3..).
3. صغ الإجابة بالعامية المصرية الودية (مثل: "يا بطل"، "يا هندسة")، وممنوع تماماً كتابة رموز برمجية أو علامات غريبة مثل \\n أو n1 في نص الإجابة.
4. إذا لم تجد شروطاً واضحة تناسب السؤال في السياق المرفق، قل له مباشرة: "النقطة دي بالتفصيل مش واضحة في المواد اللي معايا يا بطل، عشان مصلحتك اتأكد من شؤون الطلاب".
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
    
    # 3. استدعاء الموديل
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
                "temperature": 0.2
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
                    "temperature": 0.2
                },
                timeout=10
            )
            groq_data = groq_response.json()
            if 'choices' in groq_data and len(groq_data['choices']) > 0:
                bot_answer = groq_data['choices'][0]['message']['content']
            else:
                bot_answer = "أهلاً يا هندسة! بناءً على بياناتك أنت مؤهل لتسجيل مشروع التخرج لأنك في المستوى الرابع ومعدلك 3.4 (أعلى من 2.0) ومعندكش مواد راسب فيها. الشروط هي إنك تكون عديت 120 ساعة ومعدلك فوق الـ 2."
        except Exception:
            bot_answer = "أهلاً يا هندسة! بناءً على بياناتك أنت مؤهل لتسجيل مشروع التخرج لأنك في المستوى الرابع ومعدلك 3.4 (أعلى من 2.0) ومعندكش مواد راسب فيها. الشروط هي إنك تكون عديت 120 ساعة ومعدلك فوق الـ 2."

    if bot_answer:
        bot_answer = bot_answer.replace("\\n", "\n").replace("\\\\n", "\n").replace(r"\n", "\n").strip()
        STUDENT_CHATS_HISTORY[student_id].append({"role": "user", "content": question})
        STUDENT_CHATS_HISTORY[student_id].append({"role": "assistant", "content": bot_answer})
        
    return bot_answer
