import os
from pinecone import Pinecone
import requests
import json
from dotenv import load_dotenv

load_dotenv()

# 🧠 ذاكرة مؤقتة لحفظ تاريخ المحادثات لكل طالب
STUDENT_CHATS_HISTORY = {}

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

def ask_wanis(question: str, student_id: str = "default_student", student_profile: dict = None):
    if student_id not in STUDENT_CHATS_HISTORY:
        STUDENT_CHATS_HISTORY[student_id] = []
        
    history = STUDENT_CHATS_HISTORY[student_id]
    student_profile = student_profile or {}
    
    context = ""
    try:
        try:
            pinecone_key = os.getenv("PINECONE_API_KEY")
            groq_key = os.getenv("GROQ_API_KEY")
            
            if pinecone_key and groq_key:
                # 1. تحويل سؤال الطالب لـ Vector حقيقي بدلاً من الأصفار العشوائية
                embed_url = "https://api.groq.com/openai/v1/embeddings"
                embed_response = requests.post(
                    url=embed_url,
                    headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
                    json={"model": "nomic-embed-text-v1.5", "input": question},
                    timeout=5
                )
                query_vector = embed_response.json()['data'][0]['embedding']
                
                # 2. البحث في Pinecone بالـ Vector الحقيقي بتاع السؤال
                pc = Pinecone(api_key=pinecone_key)
                index = pc.Index("wanis-index")
                
                search_results = index.query(
                    vector=query_vector, # <--- هنا السحر، بنبحث بالسؤال نفسه!
                    top_k=3,
                    include_metadata=True
                )
                context = "\n".join([match['metadata']['text'] for match in search_results['matches'] if 'metadata' in match and 'text' in match['metadata']])
            else:
                context = "بيئة العمل تفتقد لمفاتيح الاتصال."
        except Exception as e:
            context = "تعذر استخراج سياق اللائحة حالياً بسبب عطل في قاعدة البيانات."

        # بقية كود الـ System Instruction والـ OpenRouter زي ما هو بالظبط تحت...

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
        
        # 4. الـ Fallback Logic الصامت تماماً
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
                    "temperature": 0.4
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
                        "temperature": 0.55
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
        
    except Exception as e:
        return f"حصل خطأ بسيط: {str(e)}"
