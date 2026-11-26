# Rafiq – AI Academic Assistant 🎓

An AI-powered academic assistant designed to help university students understand academic regulations through intelligent, context-aware conversations.

Rafiq leverages **Retrieval-Augmented Generation (RAG)** and **Large Language Models (LLMs)** to provide academic guidance based on university regulations and individual student information.

## 🎯 Overview

University academic regulations can be complex and difficult to navigate. Rafiq addresses this challenge by providing a conversational interface that retrieves relevant regulatory information and generates contextual responses tailored to students' academic profiles.

## ✨ Key Features

- **Academic Regulation Q&A:** Answers students' questions using university academic regulations.
- **Retrieval-Augmented Generation (RAG):** Retrieves relevant regulatory information to generate context-grounded responses.
- **Personalized Academic Assistance:** Uses student information such as academic level, department, GPA, academic status, and failed courses to personalize responses.
- **Conversation History:** Maintains recent conversation history for each student to support contextual interactions.
- **Fallback Retrieval:** Uses local JSON-based retrieval when the primary vector search is unavailable or returns no relevant context, with a predefined emergency regulation text as a final fallback.
- **LLM Provider Fallback:** Uses Groq as an alternative when the primary OpenRouter request fails.
- **REST API:** Provides `/` and `/ask` endpoints using FastAPI for API health checks and academic question answering.

## 🏗️ System Architecture

The backend follows a Retrieval-Augmented Generation workflow:

1. Receives the student's question and academic profile through a FastAPI endpoint.
2. Generates a question embedding using Groq's embedding API with the Nomic Embed Text v1.5 model.
3. Retrieves relevant academic regulation passages from Pinecone.
4. Falls back to local JSON-based retrieval if Pinecone is unavailable or no relevant context is returned.
5. Uses predefined emergency regulation text if the previous retrieval methods cannot provide context.
6. Combines the retrieved context with the student's academic information and recent conversation history.
7. Sends the contextual prompt to an LLM through OpenRouter.
8. Uses Groq as an alternative LLM provider if the OpenRouter request fails.
9. Returns the generated answer as a JSON response through the `/ask` endpoint.

## 🧰 Tech Stack

| Category | Technologies |
|---|---|
| Programming Language | Python |
| Backend Framework | FastAPI |
| Vector Database | Pinecone |
| Embedding Model | Nomic Embed Text v1.5 |
| LLM Providers | OpenRouter, Groq |
| Data Format | JSON |
| HTTP Requests | Requests |
| Environment Management | Python-dotenv |
| API Server | Uvicorn |

## 📁 Project Structure

```text
rafiq-bot/
│
├── app.py
├── utils.py
├── requirements.txt
├── runtime.txt
├── final_regulation_final_clean.json
│
├── chroma_db/
├── chroma_db_AI_Regulation/
│
└── .gitignore
```

### Main Components

- **app.py:** Defines the FastAPI application, request model, and API endpoints.
- **utils.py:** Handles embedding generation, information retrieval, prompt construction, student personalization, conversation history, and LLM integration.
- **final_regulation_final_clean.json:** Contains academic regulation data used for local retrieval fallback.
- **requirements.txt:** Specifies the Python dependencies.
- **chroma_db directories:** Existing vector database directories included in the repository. The current retrieval implementation uses Pinecone with local JSON fallback.

## ⚙️ Getting Started

### Prerequisites

- Python
- API credentials for the configured external services.

### 1. Clone the Repository

```bash
git clone https://github.com/shahdmakkawy/rafiq-bot.git
cd rafiq-bot
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

Activate it:

**Windows**

```bash
venv\Scripts\activate
```

**Linux / macOS**

```bash
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root and add the required API credentials:

```env
OPENROUTER_API_KEY=your_openrouter_api_key
GROQ_API_KEY=your_groq_api_key
PINECONE_API_KEY=your_pinecone_api_key
```

**Important:** Never commit your `.env` file or expose API credentials publicly.

### 5. Run the Application

```bash
uvicorn app:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

Interactive API documentation:

```text
http://127.0.0.1:8000/docs
```

## 🔗 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Checks whether the API is running. |
| POST | `/ask` | Receives a student's question and profile, then returns the assistant's answer. |

### Example Request

```json
{
  "question": "What are the requirements for registering the graduation project?",
  "student_id": "student_123",
  "student_profile": {
    "level": "Fourth",
    "department": "AI",
    "status": "Regular",
    "gpa": "3.4",
    "failed_courses": "None"
  }
}
```

### Example Response

```json
{
  "answer": "The generated academic guidance will be returned here."
}
```

## 🏆 Project Recognition

- Awarded an **Excellent** grade.
- Recognized as **Best Project Across Departments** at the Faculty Annual Forum, Faculty of Computers and Information, Mansoura University.

## 👥 Project Contributors

Rafiq was developed as a multidisciplinary graduation project involving:

- Artificial Intelligence
- Backend Development
- Frontend Development
- Mobile Application Development
- UI/UX Design

---

*Rafiq – Making Academic Guidance Smarter and More Accessible.*
