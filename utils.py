import os
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

# شحن ملف الـ .env محلياً (في الـ Production هتقرأ من الـ Environment Variables مباشرة)
load_dotenv()

# 1. إعداد موديل الـ Embeddings وقاعدة البيانات (Chroma DB)
# تأكدي أن مجلد الـ chroma_db_AI_Regulation مرفوع مع المشروع أو المسار بتاعه مظبوط
db_directory = "./chroma_db_AI_Regulation"
model_name = "BAAI/bge-m3"
encode_kwargs = {'normalize_embeddings': True}

# تحديد الكرت الشغال أو المعالج
import torch
device = "cuda" if torch.cuda.is_available() else "cpu"

embeddings = HuggingFaceEmbeddings(
    model_name=model_name,
    model_kwargs={'device': device},
    encode_kwargs=encode_kwargs
)

# استدعاء قاعدة البيانات المتجهية الحالية
vector_db = Chroma(persist_directory=db_directory, embedding_function=embeddings)

# 2. تعريف الموديلين (الأساسي والبديل) بالاعتماد على os.getenv
llm_openrouter = ChatOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    model="google/gemma-2-9b-it:free",  # الموديل المجاني الذكي
    temperature=0.4
)

llm_groq = ChatGroq(
    groq_api_key=os.getenv("GROQ_API_KEY"),
    model_name="llama-3.1-8b-instant",
    temperature=0.55
)

# 3. دالة ask_rafiq الذكية والمحدثة بـ Silent Fallback
def ask_rafiq(question: str, chat_history_list: list = None) -> str:
    try:
        # مرحلة الـ Retrieval
        results = vector_db.similarity_search(question, k=3)
        context = "\n\n---\n\n".join([doc.page_content for doc in results])
        
        # الـ Prompt الأصلي المميز لشخصية رفيق
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

        messages = [SystemMessage(content=system_instruction)]
        
        # تحويل الهيستوري القادم من الـ API لرسائل يفهمها لانجشين
        if chat_history_list:
            for turn in chat_history_list[-2:]:  # حفظاً للمساحة والـ Rate Limits
                user_msg = turn[0]
                bot_msg = turn[1]
                if user_msg:
                    messages.append(HumanMessage(content=user_msg))
                if bot_msg:
                    messages.append(AIMessage(content=bot_msg))
                    
        # دمج الـ Context الحالي
        user_prompt = f"السياق المستخرج من اللائحة:\n{context}\n\nسؤال الطالب: {question}"
        messages.append(HumanMessage(content=user_prompt))
        
        bot_answer = ""
        # تنفيذ الـ Silent Fallback
        try:
            response = llm_openrouter.invoke(messages)
            bot_answer = response.content
        except Exception:
            # التحويل الصامت فوراً لـ Groq عند حدوث عطل في OpenRouter
            try:
                response = llm_groq.invoke(messages)
                bot_answer = response.content
            except Exception:
                bot_answer = "بص يا بطل، حصلت مشكلة فنية بسيطة في السيرفر عندي دلوقتي، جرب تسألني تاني كمان ثواني كده."
                
        # معالجة النصوص وتنظيف الـ Escape Characters للـ Swagger والـ UI
        if bot_answer:
            bot_answer = bot_answer.replace("\\n", "\n").replace("\\\\n", "\n").strip()
            
        return bot_answer
        
    except Exception as e:
        return f"حصل خطأ داخلي في معالجة الطلب: {str(e)}"
