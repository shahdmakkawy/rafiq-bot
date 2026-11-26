# Rafiq – AI Academic Assistant 🎓

An AI-powered academic assistant designed to help university students understand academic regulations through intelligent, context-aware conversations.

Rafiq leverages **Retrieval-Augmented Generation (RAG)** and **Large Language Models (LLMs)** to provide relevant academic guidance grounded in university regulations and student information.

## 🎯 Overview

University academic regulations can be complex and difficult to navigate. Rafiq addresses this challenge by providing an intelligent conversational interface that retrieves relevant regulatory information and generates contextual responses tailored to students' academic profiles.

## ✨ Key Features

- **Academic Regulation Q&A:** Answers student questions using university academic regulations.
- **Retrieval-Augmented Generation (RAG):** Retrieves relevant regulatory content to provide context-grounded responses.
- **Personalized Academic Assistance:** Incorporates student information such as academic level, department, GPA, academic status, and failed courses.
- **Conversation Context:** Maintains recent conversation history to support contextual interactions.
- **Fallback Retrieval:** Uses local JSON-based retrieval when the primary vector search is unavailable.
- **LLM Provider Fallback:** Supports an alternative LLM provider when the primary provider is unavailable.
- **REST API:** Provides backend endpoints for integration with frontend and mobile applications.

## 🏗️ System Architecture

The backend follows a Retrieval-Augmented Generation workflow:

1. Receives the student's question and academic profile through a FastAPI endpoint.
2. Generates a question embedding using Groq's embedding API.
3. Retrieves relevant academic regulation passages from Pinecone.
4. Falls back to local JSON-based retrieval when vector search is unavailable or returns no relevant context.
5. Combines the retrieved context with the student's academic information and recent conversation history.
6. Sends the contextual prompt to an LLM through OpenRouter.
7. Uses Groq as an alternative LLM provider when needed.
8. Returns the generated response through the REST API.

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

**Main Components**

- `app.py`: Defines the FastAPI application and API endpoints.
- `utils.py`: Handles embedding generation, information retrieval, prompt construction, conversation context, and LLM integration.
- `final_regulation_final_clean.json`: Contains academic regulation data used for local retrieval fallback.
- `requirements.txt`: Specifies the Python dependencies.

*Note: ChromaDB directories are present in the repository, while the current retrieval implementation uses Pinecone with a local JSON fallback.*

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

`http://127.0.0.1:8000`

Interactive API documentation:

`http://127.0.0.1:8000/docs`

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

<p align="center">
  <b>Rafiq – Making Academic Guidance Smarter and More Accessible.</b>
</p>
