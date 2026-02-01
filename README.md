# AutoGrader RAG System

A production-ready, Canvas-style auto-grading platform with Retrieval-Augmented Generation (RAG) for intelligent, context-aware grading.

## 🎯 Features

- **Automated Grading**: Upload submissions and get AI-powered grades with detailed feedback
- **RAG-Enhanced**: Grounds grading decisions in reference documents and course materials
- **Asynchronous Processing**: Non-blocking grading with Celery workers
- **Strict JSON Output**: Validated, structured grading results
- **Modular Architecture**: Clean separation between UI, API, and worker layers
- **Swappable LLM**: Support for OpenAI or Ollama (local inference)

## 🏗️ Architecture

```
┌─────────────┐
│  Frontend   │  (HTML + Tailwind + Vanilla JS)
│  (Browser)  │
└──────┬──────┘
       │ HTTP
       ▼
┌─────────────┐
│   FastAPI   │  (Orchestration & State)
│   Backend   │
└──────┬──────┘
       │
       ├──────► MySQL (Assignments, Submissions, Grades)
       ├──────► MinIO (File Storage)
       ├──────► Qdrant (Vector DB for RAG)
       └──────► Redis (Task Queue)
                   │
                   ▼
            ┌──────────────┐
            │Celery Worker │  (Grading Logic)
            └──────────────┘
```

## 📋 Prerequisites

- Docker & Docker Compose
- Python 3.9+
- OpenAI API key (or Ollama for local inference)

## 🚀 Quick Start

### 1. Start Infrastructure

```bash
cd autograder-rag/infra
docker-compose up -d
```

This starts:
- MySQL (port 3306)
- Redis (port 6379)
- MinIO (ports 9000, 9001)
- Qdrant (ports 6333, 6334)

### 2. Configure Backend

```bash
cd ../backend
cp .env.example .env
```

Edit `.env` and add your OpenAI API key:
```env
OPENAI_API_KEY=sk-your-api-key-here
```

Or configure Ollama:
```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Start Backend

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

### 5. Start Celery Worker

In a new terminal:

```bash
cd backend
celery -A app.worker.celery_app worker -Q grading --loglevel=info
```

### 6. Open Frontend

Open `frontend/index.html` in your browser, or serve it with a simple HTTP server:

```bash
cd frontend
python -m http.server 8080
```

Then navigate to `http://localhost:8080`

## 📖 Usage Guide

### Creating an Assignment

1. Navigate to the **Assignments** tab
2. Fill in the assignment title
3. Define the rubric in JSON format:

```json
{
  "clarity": {
    "description": "Writing is clear and well-organized",
    "max_points": 25
  },
  "accuracy": {
    "description": "Information is accurate and well-researched",
    "max_points": 25
  },
  "citations": {
    "description": "Proper citations and references",
    "max_points": 25
  },
  "depth": {
    "description": "Analysis shows deep understanding",
    "max_points": 25
  }
}
```

4. Click **Create Assignment**
5. Click **Add Reference** to upload course materials (PDFs, DOCX, TXT)

### Submitting Work

1. Navigate to the **Submissions** tab
2. Select an assignment
3. Upload a submission file (PDF, DOCX, or TXT)
4. Click **Submit for Grading**
5. Watch the status change from "Queued" → "Grading" → "Done"

### Viewing Grades

1. Once grading is complete, click **Explain** on a submission
2. View:
   - **Score**: Total points earned
   - **Breakdown**: Points per rubric criterion
   - **Feedback**: Detailed explanation
   - **Citations**: References used in grading

## 🔧 Technology Stack

### Backend
- **FastAPI**: Modern Python web framework
- **Pydantic**: Request/response validation
- **MySQL**: Relational database (raw SQL, no ORM)
- **Celery**: Distributed task queue
- **Redis**: Message broker
- **MinIO**: S3-compatible object storage
- **Qdrant**: Vector database for RAG
- **Sentence Transformers**: Text embeddings
- **OpenAI/Ollama**: LLM inference

### Frontend
- **HTML5**: Semantic markup
- **Tailwind CSS**: Utility-first styling
- **Vanilla JavaScript**: No frameworks
- **Fetch API**: HTTP requests

## 📁 Project Structure

```
autograder-rag/
├── infra/
│   └── docker-compose.yml          # Infrastructure services
│
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI application
│   │   ├── config.py               # Pydantic settings
│   │   ├── db.py                   # MySQL raw SQL helpers
│   │   ├── routes/
│   │   │   ├── assignments.py      # Assignment endpoints
│   │   │   └── submissions.py      # Submission endpoints
│   │   ├── services/
│   │   │   ├── storage.py          # MinIO integration
│   │   │   ├── extract.py          # Text extraction
│   │   │   ├── embeddings.py       # Embedding generation
│   │   │   ├── rag.py              # Qdrant RAG service
│   │   │   └── llm.py              # LLM grading service
│   │   └── worker/
│   │       ├── celery_app.py       # Celery configuration
│   │       └── tasks.py            # Grading tasks
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── index.html                  # Main UI
│   ├── app.js                      # Application logic
│   └── styles.css                  # Custom styles
│
└── README.md
```

## 🗄️ Database Schema

### assignments
```sql
id              INT PRIMARY KEY AUTO_INCREMENT
title           VARCHAR(255)
rubric          JSON
created_at      TIMESTAMP
```

### submissions
```sql
id              INT PRIMARY KEY AUTO_INCREMENT
assignment_id   INT FOREIGN KEY
filename        VARCHAR(255)
s3_key          VARCHAR(500)
extracted_text  LONGTEXT
status          ENUM('queued', 'grading', 'done', 'error')
created_at      TIMESTAMP
```

### grades
```sql
id              INT PRIMARY KEY AUTO_INCREMENT
submission_id   INT FOREIGN KEY UNIQUE
score           INT
breakdown       JSON
feedback        TEXT
citations       JSON
created_at      TIMESTAMP
```

## 🔐 Security Considerations

### For Production

1. **Enable MinIO TLS**: Set `MINIO_SECURE=true`
2. **Secure MySQL**: Use strong passwords, restrict network access
3. **API Authentication**: Add JWT or API key authentication
4. **CORS**: Restrict allowed origins
5. **Rate Limiting**: Add request throttling
6. **Input Validation**: Sanitize file uploads
7. **Environment Variables**: Use secrets management

## 🧪 Testing

### Test the API

```bash
# Health check
curl http://localhost:8000/health

# Create assignment
curl -X POST http://localhost:8000/assignments/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Assignment",
    "rubric": {"criterion1": {"description": "Test", "max_points": 10}}
  }'

# List assignments
curl http://localhost:8000/assignments/
```

### Test File Upload

```bash
# Upload reference document
curl -X POST http://localhost:8000/assignments/1/references \
  -F "file=@reference.pdf"

# Submit assignment
curl -X POST "http://localhost:8000/submissions/?assignment_id=1" \
  -F "file=@submission.pdf"
```

## 🐛 Debugging

### Check Service Health

```bash
# MySQL
docker exec -it autograder_mysql mysql -u grader -pgraderpass autograder

# Redis
docker exec -it autograder_redis redis-cli ping

# MinIO
curl http://localhost:9000/minio/health/live

# Qdrant
curl http://localhost:6333/healthz
```

### View Logs

```bash
# Backend logs
uvicorn app.main:app --reload --log-level debug

# Worker logs
celery -A app.worker.celery_app worker -Q grading --loglevel=debug

# Docker logs
docker-compose -f infra/docker-compose.yml logs -f
```

## 📊 Performance Tuning

### Celery Workers
- Scale horizontally: `celery -A app.worker.celery_app worker -Q grading --concurrency=4`
- Use multiple queues for different priorities

### Qdrant
- Adjust `top_k` in RAG search based on context needs
- Use HNSW indexing for faster searches

### Embeddings
- Use smaller models for speed: `all-MiniLM-L6-v2` (default)
- Use larger models for accuracy: `all-mpnet-base-v2`

## 🔄 Extending the System

### Add New Document Types

Edit `app/services/extract.py`:
```python
@staticmethod
def extract_from_html(file_data: bytes) -> str:
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(file_data, 'html.parser')
    return soup.get_text()
```

### Custom Grading Logic

Edit `app/services/llm.py` to modify the grading prompt or add domain-specific rules.

### Add Authentication

Use FastAPI dependencies:
```python
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

@router.get("/protected")
async def protected_route(token: str = Depends(security)):
    # Verify token
    pass
```

## 🤝 Contributing

This is a production-ready template. Customize as needed:

1. Add user authentication
2. Implement role-based access control
3. Add analytics and reporting
4. Integrate with LMS systems (Canvas, Moodle)
5. Add plagiarism detection
6. Support more file formats

## 📝 License

MIT License - feel free to use in your projects.

## 🆘 Troubleshooting

### Issue: "Connection refused" errors
**Solution**: Ensure all Docker services are running: `docker-compose ps`

### Issue: Grading stays in "queued" status
**Solution**: Check if Celery worker is running and connected to Redis

### Issue: "LLM returned invalid JSON"
**Solution**: Check your OpenAI API key or Ollama connection. Try increasing temperature or adjusting the prompt.

### Issue: RAG returns no results
**Solution**: Ensure reference documents have been uploaded and indexed for the assignment

### Issue: MySQL connection errors
**Solution**: Wait for MySQL to fully initialize (check with `docker-compose logs mysql`)

## 📧 Support

For issues or questions:
1. Check the logs (`docker-compose logs`, worker logs, API logs)
2. Verify all services are healthy
3. Review the configuration in `.env`
4. Test each component individually

## 🎓 Learning Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Celery Documentation](https://docs.celeryproject.org/)
- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [MinIO Documentation](https://min.io/docs/minio/linux/index.html)
- [Sentence Transformers](https://www.sbert.net/)

---

Built with ❤️ for educators and students
