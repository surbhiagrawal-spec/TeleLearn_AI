# TeleLearn AI 📡 — AI-Powered Telecom Training Assistant

> An intelligent, RAG-based learning platform for wireless communication, networking, protocols, signal processing and modern telecom technologies — powered by **Groq LLM**, built with **Flask + SQLite**.

---

## 🚀 Overview

TeleLearn AI is a full-stack web application that transforms how students and engineers learn telecommunications. It combines a conversational AI tutor, retrieval-augmented generation (RAG) from uploaded study materials, AI-generated quizzes, an interactive topic explorer, and a learning dashboard — all in a single polished application.

**Landing Page Tagline:**
> "Learn telecom technologies, resolve doubts instantly, and test your knowledge with AI-powered interactive learning."

---

## ✨ Core Features

| Feature | Description |
|---|---|
| 🤖 **AI Chatbot** | Ask any telecom question; get structured answers with explanations, examples, and follow-up suggestions |
| 📚 **RAG Learning** | Upload PDF/TXT/DOCX files; the AI answers questions grounded in your documents via TF-IDF retrieval |
| 🗺️ **Topic Explorer** | Browse 20+ telecom categories, each with AI-generated overviews and deep-dive explanations |
| 💡 **Explain This** | Choose how to explain any concept: Simply, With Examples, Step-by-Step, Technically, or as a Comparison |
| ❓ **AI Quiz Generator** | Generate MCQ quizzes by topic and difficulty; get detailed explanations and performance feedback |
| 📊 **Learning Dashboard** | Visualize questions asked, quiz scores, topics covered, and recent activity with Chart.js |
| 🔐 **Authentication** | Secure register/login/logout with Werkzeug password hashing and Flask sessions |
| 💬 **Chat History** | All conversations are saved; continue, search, or delete past chats |
| 📁 **Material Management** | Upload, list, search, and delete study documents with chunk indexing |

---

## 🏗️ Architecture

```
telelearn_ai/
├── app.py                     # Flask application factory & entry point
├── config.py                  # All configuration, topic data
├── requirements.txt
├── .env                       # Environment variables (not committed)
├── database/
│   ├── database.db            # SQLite database (auto-created)
│   └── db_init.py             # Schema creation & DB connection
├── services/
│   ├── groq_service.py        # All Groq API calls (chat, explain, quiz, topic)
│   ├── rag_service.py         # Pure-Python TF-IDF retrieval engine
│   ├── document_service.py    # PDF/TXT/DOCX extraction, file management
│   └── quiz_service.py        # Quiz generation, scoring, history
├── routes/
│   ├── auth.py                # /register, /login, /logout
│   ├── dashboard.py           # /dashboard
│   ├── chatbot.py             # /chatbot, /chatbot/send, conversation CRUD
│   ├── topics.py              # /topics, /topics/<name>, explain API
│   ├── materials.py           # /materials, upload, delete
│   ├── quiz.py                # /quiz, generate, submit, results
│   └── profile.py             # /profile, /progress, /history
├── templates/
│   ├── base.html              # Sidebar layout (all authenticated pages)
│   ├── index.html             # Landing page
│   ├── login.html / register.html
│   ├── dashboard.html         # Chart.js dashboard
│   ├── chatbot.html           # Real-time chat interface
│   ├── topics.html            # Topic grid + Explain This
│   ├── topic_detail.html      # Per-topic AI overview + deep dive
│   ├── materials.html         # Upload zone + document list
│   ├── quiz.html              # Quiz generator + history
│   ├── quiz_take.html         # Active quiz page
│   ├── results.html           # Score ring + question review
│   ├── progress.html          # Progress charts
│   ├── history.html           # Chat history list
│   └── profile.html           # Profile editor
└── static/
    ├── css/style.css          # Full custom CSS (dark telecom theme)
    └── js/main.js             # Sidebar toggle, alerts, utilities
```

---

## 🔬 RAG Workflow

```
User Question
    │
    ▼
TF-IDF Vectorize Query
    │
    ▼
Cosine Similarity vs. All Document Chunks
    │
    ▼
Retrieve Top-K Chunks (score > 0.05)
    │
    ├──► Chunks found? → Send context + question to Groq
    │                        Groq returns: "📚 Based on learning materials: …"
    │
    └──► No relevant chunks? → General AI answer
                                 Groq returns standard educational response
```

**Why pure TF-IDF?**  
No external embedding API required. All retrieval happens locally in Python using only the standard library math/collections and custom tokenization — making the system self-contained and free to run.

---

## 🛠️ Technologies

| Layer | Technology |
|---|---|
| Backend | Python 3.10+, Flask 2.3+ |
| AI | Groq API (llama3-8b-8192) |
| Database | SQLite + Werkzeug |
| Retrieval | Pure-Python TF-IDF (no sklearn/embedding APIs required) |
| Document Parsing | PyPDF2, python-docx |
| Frontend | HTML5, CSS3, Bootstrap 5.3, Chart.js 4, marked.js |
| Auth | Werkzeug password hashing, Flask sessions |

---

## ⚙️ Setup & Installation

### Prerequisites
- Python 3.10+
- A [Groq API key](https://console.groq.com) (free tier available)

### 1. Clone / navigate to the project

```bash
cd telelearn_ai
```

### 2. Create a virtual environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment

Copy `env.example` to `.env` and add your Groq API key:

```bash
cp env.example .env
```

Edit `.env`:

```
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
SECRET_KEY=your-random-secret-key
DEBUG=True
GROQ_MODEL=llama3-8b-8192
```

> Get your free API key at https://console.groq.com

### 5. Initialize the database

The database is automatically created on first run. To initialize manually:

```bash
python database/db_init.py
```

### 6. Run the application

```bash
python app.py
```

Open your browser at: **http://127.0.0.1:5000**

---

## 📋 Database Schema

```sql
users              -- Registered users with hashed passwords
documents          -- Uploaded study materials metadata
document_chunks    -- Extracted + chunked text for RAG retrieval
conversations      -- Chat conversation sessions
messages           -- Individual messages (role: user/assistant)
quiz_attempts      -- Quiz sessions with scores
quiz_questions     -- MCQ questions with answers + explanations
learning_progress  -- Activity tracking for dashboard/charts
```

All tables use parameterized queries and proper foreign keys with `ON DELETE CASCADE`.

---

## 🎨 UI Design

- **Theme**: Dark telecom-inspired with blue/cyan/purple accents
- **Cards**: Glassmorphism-style with subtle borders and shadows  
- **Animations**: Floating hero nodes, pulsing status dot, thinking bounce
- **Charts**: Chart.js line (quiz scores), doughnut (topics), bar (progress)
- **Responsive**: Mobile-friendly sidebar with slide-in overlay
- **Typography**: Inter (UI) + JetBrains Mono (code)

---

## 🔒 Security

- Passwords hashed with **Werkzeug** (PBKDF2-SHA256)
- API key loaded from **environment variable only** — never hardcoded
- All SQL queries use **parameterized statements** (no injection risk)
- Session-based auth with `login_required` decorator on all protected routes
- File upload restricted to `.pdf`, `.txt`, `.docx` extensions with 16 MB limit

---

## 🗺️ Telecom Topics Covered

5G NR · 4G LTE · GSM · CDMA · OFDM · MIMO · Modulation · Antennas · Signal Processing ·  
Wireless Communication · Computer Networks · TCP/IP · Routing · Switching · Network Architecture ·  
Protocols · IoT Communication · Fiber Optics · Satellite Communication · 6G Basics

---

## 🚧 Future Enhancements

- [ ] Voice input / text-to-speech responses
- [ ] Semantic chunking with sentence-transformers (local)
- [ ] Collaborative study rooms
- [ ] Formula renderer (MathJax integration)
- [ ] PDF annotation and highlighting
- [ ] Flashcard generator from documents
- [ ] Email-based account recovery
- [ ] Admin panel for global material management
- [ ] Export quiz results as PDF
- [ ] Mobile PWA support


*Built as an AI-powered B.Tech project demonstrating Flask, RAG, LLM integration, and full-stack web development.*
