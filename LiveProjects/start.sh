#!/bin/bash

# Production Observability App - Start Script

echo "🚀 Starting Production Observability Application..."

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your configuration before running in production!"
fi

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "🐍 Creating Python virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Start the application
echo "🌟 Starting FastAPI application..."
echo "📍 Application will be available at: http://localhost:8000"
echo "📖 API Documentation: http://localhost:8000/docs"
echo "📊 Metrics: http://localhost:8000/metrics"
echo ""
echo "Press Ctrl+C to stop the application"
echo ""

python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload