# 🚀 QuickStart Guide

Get the AutoGrader RAG system running in 5 minutes!

## Prerequisites

- Docker & Docker Compose installed
- Python 3.9+ installed
- OpenAI API key (or Ollama for local LLM)

## Step-by-Step Setup

### 1️⃣ Clone and Navigate

```bash
cd autograder-rag
```

### 2️⃣ Run Setup Script

```bash
./setup.sh
```

This will:
- Start all infrastructure services (MySQL, Redis, MinIO, Qdrant)
- Wait for services to be ready
- Create a `.env` file from the template

### 3️⃣ Configure API Key

Edit `backend/.env` and add your OpenAI API key:

```bash
cd backend
nano .env  # or use your preferred editor
```

Change:
```env
OPENAI_API_KEY=your-openai-api-key-here
```

To your actual key:
```env
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx
```

### 4️⃣ Install Python Dependencies

```bash
pip install -r requirements.txt
```

Or with a virtual environment (recommended):

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 5️⃣ Start the Backend

```bash
uvicorn app.main:app --reload
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### 6️⃣ Start the Worker

Open a new terminal window:

```bash
cd backend
source venv/bin/activate  # If using venv
celery -A app.worker.celery_app worker -Q grading --loglevel=info
```

You should see:
```
[tasks]
  . app.worker.tasks.grade_submission
```

### 7️⃣ Open the Frontend

Option A: Direct file access
```bash
cd ../frontend
open index.html  # On Mac
# Or just double-click index.html
```

Option B: HTTP server (recommended)
```bash
cd ../frontend
python -m http.server 8080
# Then open: http://localhost:8080
```

## ✅ Verify Everything Works

Run the test script:

```bash
cd ..
python test_system.py
```

This will:
1. Create a test assignment
2. Upload a reference document
3. Submit a test assignment
4. Wait for grading
5. Display the grade

## 🎯 Your First Real Assignment

### Create an Assignment

1. Go to the **Assignments** tab
2. Enter title: "Introduction to Python"
3. Paste this rubric:

```json
{
  "code_quality": {
    "description": "Code is clean, well-structured, and follows best practices",
    "max_points": 30
  },
  "correctness": {
    "description": "Code runs correctly and produces expected output",
    "max_points": 40
  },
  "documentation": {
    "description": "Code includes comments and docstrings",
    "max_points": 30
  }
}
```

4. Click **Create Assignment**
5. Click **Add Reference** and upload a Python tutorial PDF or textbook

### Submit Work

1. Go to **Submissions** tab
2. Select your assignment
3. Upload a `.txt` or `.pdf` file with Python code
4. Click **Submit for Grading**
5. Watch it get graded automatically!

## 🐛 Troubleshooting

### Services not starting?

```bash
cd infra
docker-compose down
docker-compose up -d
docker-compose ps  # Check all services are running
```

### Worker not processing?

Check Redis connection:
```bash
docker exec -it autograder_redis redis-cli ping
# Should return: PONG
```

### "Module not found" errors?

Make sure you're in the backend directory and have installed dependencies:
```bash
cd backend
pip install -r requirements.txt
```

### Grading stuck in "queued"?

1. Make sure Celery worker is running
2. Check worker logs for errors
3. Verify Redis is accessible

### OpenAI API errors?

1. Verify your API key is correct in `.env`
2. Check you have credits in your OpenAI account
3. Try switching to Ollama for local inference:

```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2
```

## 📚 Next Steps

- Read the full [README.md](README.md) for architecture details
- Customize the grading prompt in `backend/app/services/llm.py`
- Add authentication to the API
- Deploy to production

## 🎉 You're Done!

You now have a fully functional AI-powered auto-grading system running locally!

---

**Need help?** Check the logs:
- Backend: Terminal running uvicorn
- Worker: Terminal running celery
- Infrastructure: `docker-compose -f infra/docker-compose.yml logs -f`
