# AutoGrader RAG System

A production-ready, Canvas-style auto-grading platform with Retrieval-Augmented Generation (RAG) for intelligent, context-aware grading — now enhanced with a fine-tuned DistilBERT model for semantic answer similarity scoring.

## 🎯 Features

- **Automated Grading:** Upload submissions and get AI-powered grades with detailed feedback
- **RAG-Enhanced:** Grounds grading decisions in reference documents and course materials
- **Semantic Grading:** Fine-tuned DistilBERT model scores student answers against correct answers with a similarity score (0–1)
- **Asynchronous Processing:** Non-blocking grading with Celery workers
- **Strict JSON Output:** Validated, structured grading results
- **Modular Architecture:** Clean separation between UI, API, and worker layers
- **Swappable LLM:** Support for OpenAI or Ollama (local inference)

-----

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
       ├──────► Redis (Task Queue)
       └──────► DistilBERT (Semantic Grading — /grade endpoint)
                   │
                   ▼
            ┌──────────────┐
            │Celery Worker │  (Grading Logic)
            └──────────────┘
```

-----

## 🧠 ML Grading Layer (PyTorch + DistilBERT)

AutoGrader includes a fine-tuned transformer model that scores student answers semantically — going beyond keyword matching to understand meaning.

### How it works

1. A student answer and correct answer are passed as a pair to DistilBERT
1. The `[CLS]` token embedding (768-dim) is extracted — it represents the full meaning of both texts
1. A custom grading head (Linear → ReLU → Dropout → Linear → Sigmoid) maps this to a score between 0 and 1
1. The score is returned via the `/grade` endpoint

### Architecture

```
[student_answer + correct_answer]
        │
        ▼
  DistilBERT (frozen, 66M params)
        │
        ▼
  [CLS] embedding (768-dim)
        │
        ▼
  Grading Head (trainable, ~200K params)
  Linear(768→256) → ReLU → Dropout(0.3) → Linear(256→1) → Sigmoid
        │
        ▼
  Grade score (0.0 – 1.0)
```

### Fine-tuning approach

- **Base model:** `distilbert-base-uncased` (HuggingFace)
- **Strategy:** Frozen BERT + trainable head (only 0.3% of parameters trained)
- **Optimizer:** AdamW (lr=2e-4, weight_decay=0.01)
- **Loss:** MSELoss
- **Training data:** Answer pairs with human-labelled similarity scores

### API endpoint

```bash
POST /grade
Content-Type: application/json

{
  "student_answer": "Mitochondria produces ATP energy for the cell.",
  "correct_answer": "The mitochondria is the powerhouse of the cell."
}

# Response
{
  "score": 0.87,
  "student_answer": "Mitochondria produces ATP energy for the cell.",
  "correct_answer": "The mitochondria is the powerhouse of the cell."
}
```

### PyTorch learning notebooks

All foundational ML work is documented in `notebooks/`:

|Notebook                      |Topic                                                  |
|------------------------------|-------------------------------------------------------|
|`01_tensors_foundations.ipynb`|Tensors — creation, reshape, indexing, matrix ops      |
|`02_autograd.ipynb`           |Autograd — automatic differentiation, backward()       |
|`03_neural_network.ipynb`     |nn.Module — layers, loss functions, training loop      |
|`04_dataloader.ipynb`         |DataLoader — batching, custom datasets, train/val split|
|`05_finetune.ipynb`           |Fine-tuning DistilBERT for answer similarity scoring   |

-----

## 📋 Prerequisites

- Docker & Docker Compose
- Python 3.9+
- OpenAI API key (or Ollama for local inference)

-----

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

Configure Ollama:

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

The API will be available at http://localhost:8000

### 5. Start Celery Worker

In a new terminal:

```bash
cd backend
celery -A app.worker.celery_app worker -Q grading --loglevel=info
```

### 6. Open Frontend

```bash
cd frontend
python -m http.server 8080
```

Then navigate to http://localhost:8080

-----

## 📖 Usage Guide

### Creating an Assignment

1. Navigate to the **Assignments** tab
1. Fill in the assignment title
1. Define the rubric in JSON format:

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

1. Click **Create Assignment**
1. Click **Add Reference** to upload course materials (PDFs, DOCX, TXT)

### Submitting Work

1. Navigate to the **Submissions** tab
1. Select an assignment
1. Upload a submission file (PDF, DOCX, or TXT)
1. Click **Submit for Grading**
1. Watch the status change from “Queued” → “Grading” → “Done”

### Viewing Grades

Once grading is complete, click **Explain** on a submission to view:

- **Score:** Total points earned
- **Breakdown:** Points per rubric criterion
- **Feedback:** Detailed explanation
- **Citations:** References used in grading

-----

## 🔧 Technology Stack

### Backend

|Technology                  |Purpose                              |
|----------------------------|-------------------------------------|
|FastAPI                     |Modern Python web framework          |
|Pydantic                    |Request/response validation          |
|MySQL                       |Relational database (raw SQL, no ORM)|
|Celery                      |Distributed task queue               |
|Redis                       |Message broker                       |
|MinIO                       |S3-compatible object storage         |
|Qdrant                      |Vector database for RAG              |
|Sentence Transformers       |Text embeddings                      |
|OpenAI / Ollama             |LLM inference                        |
|**PyTorch**                 |**Deep learning framework**          |
|**HuggingFace Transformers**|**DistilBERT fine-tuning**           |

### Frontend

- HTML5, Tailwind CSS, Vanilla JavaScript, Fetch API

-----

## 📁 Project Structure

```
autograder-rag/
├── infra/
│   └── docker-compose.yml
│
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI application + lifespan
│   │   ├── config.py
│   │   ├── db.py
│   │   ├── routes/
│   │   │   ├── assignments.py
│   │   │   └── submissions.py      # Includes /grade endpoint
│   │   ├── services/
│   │   │   ├── storage.py
│   │   │   ├── extract.py
│   │   │   ├── embeddings.py
│   │   │   ├── rag.py
│   │   │   ├── llm.py
│   │   │   └── grading.py          # DistilBERT grading service
│   │   └── worker/
│   │       ├── celery_app.py
│   │       └── tasks.py
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── index.html
│   ├── app.js
│   └── styles.css
│
├── notebooks/                      # PyTorch learning + ML experiments
│   ├── 01_tensors_foundations.ipynb
│   ├── 02_autograd.ipynb
│   ├── 03_neural_network.ipynb
│   ├── 04_dataloader.ipynb
│   └── 05_finetune.ipynb           # DistilBERT fine-tuning
│
└── README.md
```

-----

## 🗄️ Database Schema

**assignments**

|Column    |Type                          |
|----------|------------------------------|
|id        |INT PRIMARY KEY AUTO_INCREMENT|
|title     |VARCHAR(255)                  |
|rubric    |JSON                          |
|created_at|TIMESTAMP                     |

**submissions**

|Column        |Type                                      |
|--------------|------------------------------------------|
|id            |INT PRIMARY KEY AUTO_INCREMENT            |
|assignment_id |INT FOREIGN KEY                           |
|filename      |VARCHAR(255)                              |
|s3_key        |VARCHAR(500)                              |
|extracted_text|LONGTEXT                                  |
|status        |ENUM(‘queued’, ‘grading’, ‘done’, ‘error’)|
|created_at    |TIMESTAMP                                 |

**grades**

|Column       |Type                          |
|-------------|------------------------------|
|id           |INT PRIMARY KEY AUTO_INCREMENT|
|submission_id|INT FOREIGN KEY UNIQUE        |
|score        |INT                           |
|breakdown    |JSON                          |
|feedback     |TEXT                          |
|citations    |JSON                          |
|created_at   |TIMESTAMP                     |

-----

## 🔐 Security Considerations

For production:

- Enable MinIO TLS: `MINIO_SECURE=true`
- Secure MySQL with strong passwords and restricted network access
- Add JWT or API key authentication
- Restrict CORS allowed origins
- Add request rate limiting
- Sanitize file uploads
- Use secrets management for environment variables

-----

## 🧪 Testing

```bash
# Health check
curl http://localhost:8000/health

# Create assignment
curl -X POST http://localhost:8000/assignments/ \
  -H "Content-Type: application/json" \
  -d '{"title": "Test Assignment", "rubric": {"criterion1": {"description": "Test", "max_points": 10}}}'

# Grade a student answer
curl -X POST http://localhost:8000/grade \
  -H "Content-Type: application/json" \
  -d '{
    "student_answer": "Mitochondria produces ATP energy for the cell.",
    "correct_answer": "The mitochondria is the powerhouse of the cell."
  }'
```

-----

## 🐛 Debugging

```bash
# MySQL
docker exec -it autograder_mysql mysql -u grader -pgraderpass autograder

# Redis
docker exec -it autograder_redis redis-cli ping

# MinIO
curl http://localhost:9000/minio/health/live

# Qdrant
curl http://localhost:6333/healthz

# Backend (debug mode)
uvicorn app.main:app --reload --log-level debug

# Worker (debug mode)
celery -A app.worker.celery_app worker -Q grading --loglevel=debug

# Docker logs
docker-compose -f infra/docker-compose.yml logs -f
```

-----

## 📊 Performance Tuning

**Celery Workers**

- Scale horizontally: `celery -A app.worker.celery_app worker -Q grading --concurrency=4`

**Qdrant**

- Adjust `top_k` in RAG search based on context needs
- Use HNSW indexing for faster searches

**DistilBERT Grading**

- Model loads once at startup via FastAPI lifespan — no per-request loading overhead
- Unfreeze BERT layers and retrain with more data to improve accuracy ceiling

-----

## 🔄 Extending the System

**Improve grading accuracy**

- Unfreeze DistilBERT and fine-tune end-to-end with more labelled answer pairs
- Switch to `sentence-transformers/all-mpnet-base-v2` for better embeddings

**Add new document types**

```python
# app/services/extract.py
@staticmethod
def extract_from_html(file_data: bytes) -> str:
    from bs4 import BeautifulSoup
    return BeautifulSoup(file_data, 'html.parser').get_text()
```

**Add authentication**

```python
from fastapi.security import HTTPBearer
security = HTTPBearer()

@router.get("/protected")
async def protected_route(token: str = Depends(security)):
    # Verify token
    pass
```

-----

## 🤝 Contributing

Customisation ideas:

- Add user authentication and role-based access control
- Add analytics and reporting dashboard
- Integrate with LMS systems (Canvas, Moodle)
- Add plagiarism detection
- Support more file formats

-----

## 📝 License

MIT License — feel free to use in your projects.

-----

## 🆘 Troubleshooting

|Issue                      |Solution                                                           |
|---------------------------|-------------------------------------------------------------------|
|“Connection refused” errors|Ensure all Docker services are running: `docker-compose ps`        |
|Grading stays in “queued”  |Check if Celery worker is running and connected to Redis           |
|“LLM returned invalid JSON”|Check OpenAI API key or Ollama connection                          |
|RAG returns no results     |Ensure reference documents are uploaded and indexed                |
|MySQL connection errors    |Wait for MySQL to fully initialise: `docker-compose logs mysql`    |
|Grading model not loaded   |Ensure `load_model()` is called in FastAPI lifespan (see `main.py`)|

-----

## 🎓 Learning Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [Celery Documentation](https://docs.celeryq.dev)
- [Qdrant Documentation](https://qdrant.tech/documentation)
- [MinIO Documentation](https://min.io/docs)
- [Sentence Transformers](https://www.sbert.net)
- [PyTorch Documentation](https://pytorch.org/docs)
- [HuggingFace Transformers](https://huggingface.co/docs/transformers)
