# Carenova AI Health Assistant

A production-ready medical guidance system with RAG (Retrieval Augmented Generation) using Ollama and LangChain. Includes both REST API and real-time WebSocket support for frontend integration.

## 🎯 Features

✅ **RAG-Based Medical Knowledge** — Uses vector embeddings + semantic search  
✅ **OpenRouter LLM** — No local downloads, cloud-based inference  
✅ **Adaptive Q&A** — LLM generates contextualized follow-up questions  
✅ **Streaming Chat** — WebSocket support for real-time responses  
✅ **REST APIs** — `/followup-questions`, `/analyze`, `/health` endpoints  
✅ **Production Ready** — Error handling, logging, session management, rate limiting  
✅ **Frontend Included** — HTML/CSS/JS interface out of the box  
✅ **Configurable** — Environment variables for all settings  
✅ **Docker Ready** — Single server VPS deployment

---

## 🚀 Quick Start

### 1. **Get API Keys**

**OpenRouter** (Free tier available):
1. Go to [openrouter.ai](https://openrouter.ai)
2. Sign up → Copy your API key

**OpenAI Embeddings** (Optional, for better embeddings):
1. Go to [platform.openai.com](https://platform.openai.com)
2. Create account → Copy API key
   - OR skip this and use local Ollama for embeddings only

### 2. **Install Dependencies**

```bash
pip install -r requirements.txt
```

### 3. **Configure Environment**

Copy and edit `.env`:
```bash
copy .env.example .env
```

Edit `.env` with your API keys:
```env
OPENROUTER_API_KEY=your_key_from_step_1
OPENAI_API_KEY=your_openai_key_or_leave_blank
EMBEDDINGS_PROVIDER=openai  # or "ollama" if using local
```

### 4. **Ingest Medical Knowledge** (One-time)

Builds vector database from markdown files in `medical_knowledge/`:

```bash
python ingest.py
```

### 5. **Start Backend Server**

```bash
python server.py
```

Expected output:
```
🚀 Starting Carenova API on 0.0.0.0:8000
✅ LLM initialized with OpenRouter: meta-llama/llama-2-7b-chat
✅ Using OpenAI embeddings: text-embedding-3-small
✅ Vector DB initialized: chroma_db
📖 Docs available at http://localhost:8000/docs
```

### 6. **Access Frontend**

Open browser → **http://localhost:8000**

---

## 📡 API Endpoints

### `GET /health`
Health check for load balancers.

```bash
curl http://localhost:8000/health

# Response:
{
  "status": "healthy",
  "message": "All systems operational",
  "models_loaded": true,
  "vector_db_ready": true
}
```

### `POST /followup-questions`
Generate adaptive follow-up questions.

```bash
curl -X POST http://localhost:8000/followup-questions \
  -H "Content-Type: application/json" \
  -d '{
    "symptoms": "I have a persistent cough and chest pain"
  }'

# Response:
{
  "questions": [
    "How long have you had these symptoms?",
    "Is the chest pain constant or intermittent?",
    "Do you have difficulty breathing?"
  ]
}
```

### `POST /analyze`
Full symptom analysis with RAG.

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "initial_symptoms": "I have a persistent cough and chest pain",
    "followup_answers": ["For 2 weeks", "It comes and goes", "Yes"]
  }'

# Response:
{
  "severity": "Moderate",
  "confidence": "78%",
  "possible_conditions": ["Bronchitis", "Pneumonia", "GERD"],
  "explanation": ["Persistent cough + chest pain typical of..."],
  "home_care_tips": ["Rest", "Stay hydrated", "Use humidifier"],
  "when_to_see_doctor": ["If cough persists > 3 weeks", "If fever > 101°F"],
  "disclaimer": "This is not a medical diagnosis..."
}
```

### `WebSocket /ws/chat`
Real-time streaming chat (used by frontend).

**JavaScript client example:**

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/chat');

ws.onopen = () => {
    ws.send(JSON.stringify({
        session_id: 'user123',
        initial_symptoms: 'I have a cough',
        followup_answers: ['For 2 weeks', 'Getting worse']
    }));
};

ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    if (msg.type === 'thinking') {
        console.log(msg.content); // "🧠 Analyzing..."
    } else if (msg.type === 'analysis') {
        console.log(msg.data); // Full analysis result
    }
};
```

### `GET /docs`
Interactive API documentation (Swagger UI).

Open → **http://localhost:8000/docs**

---

## 🔧 Configuration

Create a `.env` file (or copy from `.env.example`):

```env
# Server
HOST=0.0.0.0
PORT=8000
DEBUG=False
LOG_LEVEL=INFO

# LLM (OpenRouter)
OPENROUTER_API_KEY=your_key_from_openrouter.ai
LLM_MODEL=meta-llama/llama-2-7b-chat
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=512

# Embeddings (choose one)
EMBEDDINGS_PROVIDER=openai              # "openai" or "ollama"
OPENAI_API_KEY=your_openai_api_key      # Required if EMBEDDINGS_PROVIDER=openai
EMBEDDINGS_MODEL=text-embedding-3-small
OLLAMA_BASE_URL=http://localhost:11434  # Required if EMBEDDINGS_PROVIDER=ollama

# Database
CHROMA_DIR=chroma_db
MEDICAL_KNOWLEDGE_PATH=medical_knowledge

# RAG
RAG_SCORE_THRESHOLD=0.55
RAG_K_RESULTS=5
RAG_CACHE_ENABLED=True

# Session & Rate Limiting
SESSION_TIMEOUT_MINUTES=30
MAX_FOLLOWUP_QUESTIONS=3
RATE_LIMIT_PER_MINUTE=10

# CORS (for frontend)
ENABLE_CORS=True
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000
```

### **Embedding Options**

**Option 1: OpenAI Embeddings** (Recommended)
- High quality, cloud-based
- Requires: `OPENAI_API_KEY`
- Fast, no local setup needed

**Option 2: Local Ollama Embeddings**
- Free, keeps data local
- Requires: Ollama service running (`ollama serve`)
- Download: `ollama pull nomic-embed-text`

### **LLM Model Options**

Available models on [openrouter.ai](https://openrouter.ai):
- `meta-llama/llama-2-7b-chat` (Free, fast)
- `meta-llama/llama-2-13b-chat` (Slower, better quality)
- `openai/gpt-3.5-turbo` (Premium, high quality)
- `openai/gpt-4` (Premium, best quality)
- [See all models](https://openrouter.ai/docs/models)

---

## 📁 Project Structure

```
carenova-health-chatbot/
├── server.py                    # FastAPI app (REST + WebSocket)
├── chatbot.py                   # Symptom analysis logic
├── rag.py                       # Vector DB retrieval + caching
├── llm.py                       # LLM initialization
├── adaptive_questions.py         # Follow-up Q&A generation
├── ingest.py                    # Data ingestion pipeline
├── models.py                    # Pydantic request/response schemas
├── config.py                    # Configuration management
├── logger.py                    # Structured logging
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment template
├── static/                      # Frontend (HTML/CSS/JS)
│   ├── index.html
│   ├── style.css
│   └── script.js
├── medical_knowledge/           # Medical markdown files
│   ├── cardiovascular/
│   ├── respiratory/
│   ├── neurological/
│   └── ...
└── chroma_db/                   # Vector database (auto-created)
```

---

## 🔌 Frontend Integration

### **Option 1: Use Included Frontend**
Static HTML/CSS/JS is served at `http://localhost:8000` and communicates via WebSocket.

### **Option 2: Connect External Frontend (React, Vue, etc.)**

**React Example:**
```javascript
const BASE_URL = 'http://localhost:8000';

// Get followup questions
const response = await fetch(`${BASE_URL}/followup-questions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ symptoms: 'I have a cough' })
});
const { questions } = await response.json();

// Stream analysis via WebSocket
const ws = new WebSocket('ws://localhost:8000/ws/chat');
ws.send(JSON.stringify({
    session_id: userId,
    initial_symptoms: '...',
    followup_answers: ['...', '...']
}));
```

### **Option 3: REST-Only (No WebSocket)**
Call `/analyze` endpoint directly for synchronous response:

```javascript
const result = await fetch(`${BASE_URL}/analyze`, {
    method: 'POST',
    body: JSON.stringify({
        initial_symptoms: '...',
        followup_answers: ['...']
    })
}).then(r => r.json());
```

---

## 🧪 Testing

**Run Streamlit CLI (local testing only):**
```bash
streamlit run app.py
```

**Run as script:**
```bash
python chatbot.py
```

---

## 📊 Logging & Monitoring

Logs are saved to `logs/carenova.log` in JSON format:

```bash
tail -f logs/carenova.log | jq '.'
```

Check health:
```bash
watch curl http://localhost:8000/health
```

---

## 🚀 Deployment

### **Local/VPS (Single Server)**
```bash
# Install dependencies
pip install -r requirements.txt

# Ingest medical knowledge (one-time)
python ingest.py

# Start API server
python server.py
```

Server runs at `http://localhost:8000`

### **Docker**
Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "server.py"]
```

Build & run:
```bash
docker build -t carenova .
docker run -p 8000:8000 -e OPENROUTER_API_KEY=$YOUR_KEY carenova
```

### **Docker Compose**
Create `docker-compose.yml`:
```yaml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      OPENROUTER_API_KEY: ${OPENROUTER_API_KEY}
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      EMBEDDINGS_PROVIDER: openai
    volumes:
      - ./chroma_db:/app/chroma_db
```

Run:
```bash
docker-compose up
```

### **Systemd Service** (Linux)
Create `/etc/systemd/system/carenova.service`:
```ini
[Unit]
Description=Carenova Health API
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/carenova
EnvironmentFile=/var/www/carenova/.env
ExecStart=/usr/bin/python3 server.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Enable & start:
```bash
sudo systemctl enable carenova
sudo systemctl start carenova
```

---

## ⚙️ Performance & Optimization

| Setting | Impact | Tuning |
|---------|--------|--------|
| `LLM_NUM_CTX=2048` | Reasoning depth | Increase for complex cases (slower) |
| `RAG_SCORE_THRESHOLD=0.55` | Relevance filter | Lower (0.4) = more results, higher (0.7) = stricter |
| `RAG_K_RESULTS=5` | Retrieved docs | Increase for diversity, decrease for speed |
| `RAG_CACHE_ENABLED=True` | Response caching | Disable for real-time updates |
| `RATE_LIMIT_PER_MINUTE=10` | API throttling | Adjust per expected load |

---

## 🆘 Troubleshooting

**Issue: "OPENROUTER_API_KEY not set"**
```bash
# Edit .env and add your key from openrouter.ai
OPENROUTER_API_KEY=sk_...
```

**Issue: "OPENAI_API_KEY required"**
- Either add your OpenAI key to `.env`
- OR switch to Ollama embeddings: `EMBEDDINGS_PROVIDER=ollama`

**Issue: "Vector DB not found"**
```bash
python ingest.py
```

**Issue: "LLM response truncated"**
- Increase `LLM_MAX_TOKENS` in `.env` (default 512)

**Issue: "Rate limit exceeded"**
- Increase `RATE_LIMIT_PER_MINUTE` in `.env`

**Issue: OpenAI embeddings slow**
- Use smaller model: `EMBEDDINGS_MODEL=text-embedding-3-small`
- Or switch to Ollama

**Issue: WebSocket won't connect**
- Check CORS is enabled: `ENABLE_CORS=True`
- Verify frontend URL is in `ALLOWED_ORIGINS`

---

## 📝 License

MIT License — Free to use and modify

---

## 🤝 Contributing

PRs welcome! Areas for improvement:
- Multi-language support
- Advanced session persistence (Redis)
- Feedback loop to improve RAG quality
- Mobile app (React Native)
- Advanced analytics dashboard

---

**Built with ❤️ for safer, smarter healthcare**
