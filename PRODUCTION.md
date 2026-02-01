# 🚀 Production Deployment Guide

This guide helps you deploy the AutoGrader RAG system to production.

## Architecture Overview

```
Internet
    ↓
[Load Balancer / Reverse Proxy]
    ↓
[FastAPI Backend] ← → [Celery Workers]
    ↓                        ↓
[MySQL] [Redis] [MinIO] [Qdrant]
```

## Pre-Deployment Checklist

### Security

- [ ] Change all default passwords
- [ ] Enable TLS/SSL for all services
- [ ] Set up firewall rules
- [ ] Configure CORS properly
- [ ] Add API authentication (JWT)
- [ ] Enable rate limiting
- [ ] Use secrets management (AWS Secrets Manager, HashiCorp Vault)
- [ ] Regular security audits
- [ ] Keep dependencies updated

### Infrastructure

- [ ] Set up monitoring (Prometheus, Grafana)
- [ ] Configure logging (ELK stack, CloudWatch)
- [ ] Set up alerts
- [ ] Database backups
- [ ] Disaster recovery plan
- [ ] CDN for static files
- [ ] Auto-scaling configuration

### Performance

- [ ] Database indexing optimized
- [ ] Connection pooling configured
- [ ] Caching layer (Redis)
- [ ] Worker scaling strategy
- [ ] Load testing completed
- [ ] Resource limits set

## Deployment Options

### Option 1: AWS ECS/Fargate

#### Infrastructure Components

```yaml
# docker-compose.production.yml
version: '3.8'

services:
  backend:
    image: your-registry/autograder-backend:latest
    environment:
      - MYSQL_HOST=${RDS_ENDPOINT}
      - REDIS_URL=redis://${ELASTICACHE_ENDPOINT}:6379
      - MINIO_ENDPOINT=${S3_ENDPOINT}
      - QDRANT_HOST=${QDRANT_ENDPOINT}
      - OPENAI_API_KEY=${OPENAI_API_KEY_SECRET}
    ports:
      - "8000:8000"
    
  worker:
    image: your-registry/autograder-backend:latest
    command: celery -A app.worker.celery_app worker -Q grading --concurrency=4
    environment:
      - MYSQL_HOST=${RDS_ENDPOINT}
      - REDIS_URL=redis://${ELASTICACHE_ENDPOINT}:6379
```

#### Services to Use

- **RDS MySQL**: Managed database
- **ElastiCache Redis**: Managed cache and queue
- **S3**: Replace MinIO with S3
- **ECS/Fargate**: Container orchestration
- **Application Load Balancer**: Traffic distribution
- **CloudWatch**: Logging and monitoring
- **Secrets Manager**: Credentials management

#### Deployment Steps

```bash
# 1. Build and push Docker image
docker build -t your-registry/autograder-backend:latest backend/
docker push your-registry/autograder-backend:latest

# 2. Update ECS task definition
aws ecs register-task-definition --cli-input-json file://task-definition.json

# 3. Update service
aws ecs update-service --cluster autograder --service backend --force-new-deployment
```

### Option 2: Kubernetes (GKE/EKS/AKS)

#### Kubernetes Manifests

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: autograder-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: autograder-backend
  template:
    metadata:
      labels:
        app: autograder-backend
    spec:
      containers:
      - name: backend
        image: your-registry/autograder-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: MYSQL_HOST
          valueFrom:
            secretKeyRef:
              name: autograder-secrets
              key: mysql-host
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: autograder-worker
spec:
  replicas: 5
  selector:
    matchLabels:
      app: autograder-worker
  template:
    metadata:
      labels:
        app: autograder-worker
    spec:
      containers:
      - name: worker
        image: your-registry/autograder-backend:latest
        command: ["celery", "-A", "app.worker.celery_app", "worker", "-Q", "grading"]
        env:
        - name: MYSQL_HOST
          valueFrom:
            secretKeyRef:
              name: autograder-secrets
              key: mysql-host
```

#### Deploy

```bash
kubectl apply -f k8s/
kubectl rollout status deployment/autograder-backend
```

### Option 3: DigitalOcean App Platform

Simpler managed platform for smaller deployments.

```yaml
# .do/app.yaml
name: autograder-rag
services:
  - name: backend
    github:
      repo: your-username/autograder-rag
      branch: main
      deploy_on_push: true
    source_dir: backend
    run_command: uvicorn app.main:app --host 0.0.0.0 --port 8080
    http_port: 8080
    instance_count: 2
    instance_size_slug: professional-xs
    
  - name: worker
    github:
      repo: your-username/autograder-rag
      branch: main
    source_dir: backend
    run_command: celery -A app.worker.celery_app worker -Q grading
    instance_count: 3
    
databases:
  - engine: MYSQL
    name: autograder-db
    
  - engine: REDIS
    name: autograder-redis
```

## Database Migration Strategy

### Initial Setup

```sql
-- Create database
CREATE DATABASE autograder;
USE autograder;

-- Run schema
SOURCE schema.sql;

-- Create indexes
CREATE INDEX idx_submissions_status ON submissions(status);
CREATE INDEX idx_submissions_created ON submissions(created_at);
CREATE INDEX idx_grades_score ON grades(score);
```

### Backup Strategy

```bash
# Daily automated backup
0 2 * * * mysqldump -u user -p autograder | gzip > /backups/autograder-$(date +\%Y\%m\%d).sql.gz

# Backup retention: 30 days
find /backups -name "autograder-*.sql.gz" -mtime +30 -delete
```

## Monitoring & Observability

### Prometheus Metrics

Add to `backend/app/main.py`:

```python
from prometheus_client import Counter, Histogram, make_asgi_app
from prometheus_fastapi_instrumentator import Instrumentator

# Metrics
grading_requests = Counter('grading_requests_total', 'Total grading requests')
grading_duration = Histogram('grading_duration_seconds', 'Grading duration')

# Add metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Instrument
Instrumentator().instrument(app).expose(app)
```

### Health Checks

```python
@app.get("/health/live")
async def liveness():
    return {"status": "alive"}

@app.get("/health/ready")
async def readiness():
    # Check dependencies
    checks = {
        "database": check_mysql(),
        "redis": check_redis(),
        "storage": check_minio(),
        "qdrant": check_qdrant()
    }
    
    if all(checks.values()):
        return {"status": "ready", "checks": checks}
    else:
        raise HTTPException(status_code=503, detail=checks)
```

### Logging

```python
import logging
from pythonjsonlogger import jsonlogger

# Configure JSON logging
logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)
```

## Performance Tuning

### Database Connection Pooling

```python
# app/db.py
from mysql.connector import pooling

db_config = {
    "pool_name": "autograder_pool",
    "pool_size": 10,
    "host": settings.mysql_host,
    "user": settings.mysql_user,
    "password": settings.mysql_password,
    "database": settings.mysql_database
}

connection_pool = pooling.MySQLConnectionPool(**db_config)

def get_connection():
    return connection_pool.get_connection()
```

### Celery Configuration

```python
# app/worker/celery_app.py
celery_app.conf.update(
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    result_expires=3600,
)
```

### Nginx Configuration

```nginx
upstream backend {
    least_conn;
    server backend1:8000 weight=1;
    server backend2:8000 weight=1;
    server backend3:8000 weight=1;
}

server {
    listen 80;
    server_name autograder.example.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name autograder.example.com;
    
    ssl_certificate /etc/ssl/certs/autograder.crt;
    ssl_certificate_key /etc/ssl/private/autograder.key;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN";
    add_header X-Content-Type-Options "nosniff";
    add_header X-XSS-Protection "1; mode=block";
    
    # Frontend
    location / {
        root /var/www/autograder/frontend;
        try_files $uri $uri/ /index.html;
    }
    
    # API
    location /api/ {
        proxy_pass http://backend/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeout for long grading operations
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req zone=api burst=20 nodelay;
}
```

## Security Hardening

### Environment Variables

Never commit sensitive data. Use:

```bash
# AWS Secrets Manager
aws secretsmanager create-secret \
    --name autograder/openai-key \
    --secret-string "sk-your-key"

# Retrieve in application
import boto3
secrets = boto3.client('secretsmanager')
secret = secrets.get_secret_value(SecretId='autograder/openai-key')
```

### API Authentication

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

@router.post("/assignments/")
async def create_assignment(
    assignment: AssignmentCreate,
    user=Depends(verify_token)
):
    # Only authenticated users can create
    pass
```

## Cost Optimization

### Reduce LLM Costs

1. **Use cheaper models**: GPT-3.5 instead of GPT-4 for simple tasks
2. **Batch processing**: Group similar submissions
3. **Caching**: Cache common grading scenarios
4. **Local models**: Use Ollama for non-critical grading

### Infrastructure Costs

1. **Auto-scaling**: Scale workers based on queue depth
2. **Spot instances**: Use spot/preemptible instances for workers
3. **Right-sizing**: Monitor and adjust instance sizes
4. **Reserved instances**: For predictable workloads

## Troubleshooting Production

### Worker Issues

```bash
# Check queue depth
redis-cli LLEN celery

# Purge stuck tasks
celery -A app.worker.celery_app purge

# Restart workers
kubectl rollout restart deployment/autograder-worker
```

### Database Performance

```sql
-- Check slow queries
SELECT * FROM mysql.slow_log ORDER BY query_time DESC LIMIT 10;

-- Analyze query performance
EXPLAIN SELECT * FROM submissions WHERE status = 'queued';
```

### Memory Leaks

```bash
# Monitor container memory
docker stats

# Get heap dump
python -m memory_profiler app/main.py
```

## Maintenance Windows

Schedule regular maintenance:

```bash
# Sunday 2 AM UTC - Database optimization
0 2 * * 0 /scripts/optimize_db.sh

# Daily - Log rotation
0 0 * * * /scripts/rotate_logs.sh

# Weekly - Dependency updates
0 3 * * 1 /scripts/update_deps.sh
```

## Rollback Procedure

```bash
# 1. Stop new deployments
kubectl scale deployment autograder-backend --replicas=0

# 2. Revert to previous version
kubectl rollout undo deployment/autograder-backend

# 3. Verify health
kubectl get pods
curl https://autograder.example.com/health

# 4. Restore normal operation
kubectl scale deployment autograder-backend --replicas=3
```

## Support & Monitoring

Set up alerts for:
- High error rates (> 5%)
- Slow response times (> 2s p95)
- Queue depth (> 100 tasks)
- Database connections (> 80% pool)
- Disk usage (> 80%)
- Memory usage (> 90%)

---

**Remember**: Always test in staging before deploying to production!
