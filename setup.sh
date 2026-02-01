#!/bin/bash

# AutoGrader RAG Setup Script

echo "🚀 AutoGrader RAG System Setup"
echo "================================"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"
echo ""

# Start infrastructure
echo "📦 Starting infrastructure services..."
cd infra
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service health
echo ""
echo "🔍 Checking service health..."

# MySQL
until docker exec autograder_mysql mysqladmin ping -h localhost --silent; do
    echo "   MySQL is starting..."
    sleep 2
done
echo "   ✅ MySQL is ready"

# Redis
until docker exec autograder_redis redis-cli ping | grep -q PONG; do
    echo "   Redis is starting..."
    sleep 2
done
echo "   ✅ Redis is ready"

# MinIO
until curl -f http://localhost:9000/minio/health/live &> /dev/null; do
    echo "   MinIO is starting..."
    sleep 2
done
echo "   ✅ MinIO is ready"

# Qdrant
until curl -f http://localhost:6333/healthz &> /dev/null; do
    echo "   Qdrant is starting..."
    sleep 2
done
echo "   ✅ Qdrant is ready"

echo ""
echo "✅ All services are healthy!"
echo ""

# Create .env if it doesn't exist
cd ../backend
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "   ⚠️  Please edit backend/.env and add your OpenAI API key"
else
    echo "✅ .env file already exists"
fi

echo ""
echo "================================"
echo "🎉 Setup Complete!"
echo "================================"
echo ""
echo "Next steps:"
echo "1. Edit backend/.env and add your OpenAI API key (or configure Ollama)"
echo "2. Install Python dependencies: cd backend && pip install -r requirements.txt"
echo "3. Start the backend: uvicorn app.main:app --reload"
echo "4. Start the worker: celery -A app.worker.celery_app worker -Q grading"
echo "5. Open frontend/index.html in your browser"
echo ""
echo "For more details, see README.md"
echo ""
