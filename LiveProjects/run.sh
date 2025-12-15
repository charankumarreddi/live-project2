#!/bin/bash

# Production Observability App - Complete Setup and Run Script
# This script handles the complete setup and running of the application

set -e  # Exit on any error

echo "🚀 Production Observability App - Setup & Run"
echo "================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if we're in the correct directory
CURRENT_DIR=$(pwd)
if [[ ! "$CURRENT_DIR" == *"LiveProjects"* ]]; then
    print_error "Please run this script from the LiveProjects directory"
    exit 1
fi

print_status "Current directory: $CURRENT_DIR"

# Step 1: Check Python version
print_info "Checking Python version..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
    print_status "Python version: $PYTHON_VERSION"
else
    print_error "Python 3 is not installed. Please install Python 3.9 or higher."
    exit 1
fi

# Step 2: Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    print_info "Creating Python virtual environment..."
    python3 -m venv .venv
    print_status "Virtual environment created"
else
    print_status "Virtual environment already exists"
fi

# Step 3: Activate virtual environment
print_info "Activating virtual environment..."
source .venv/bin/activate
print_status "Virtual environment activated"

# Step 4: Upgrade pip and install dependencies
print_info "Installing dependencies..."
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
print_status "Dependencies installed"

# Step 5: Verify critical packages
print_info "Verifying installation..."
python -c "import fastapi, uvicorn, sqlalchemy; print('Core packages verified')" 2>/dev/null
if [ $? -eq 0 ]; then
    print_status "All critical packages installed correctly"
else
    print_error "Package verification failed"
    exit 1
fi

# Step 6: Check if .env file exists, create if not
if [ ! -f ".env" ]; then
    print_info "Creating .env configuration file..."
    cat > .env << EOF
# Application Settings
APP_NAME=Production Observability App
APP_VERSION=1.0.0
ENVIRONMENT=development
DEBUG=true

# Server Settings
HOST=127.0.0.1
PORT=8888

# Database Settings (using SQLite for development)
DATABASE_URL=sqlite+aiosqlite:///./app.db

# Security Settings
SECRET_KEY=dev-secret-key-change-in-production-12345
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Logging Settings
LOG_LEVEL=INFO
LOG_FORMAT=json

# Monitoring Settings
METRICS_ENABLED=true
TRACING_ENABLED=false
JAEGER_ENDPOINT=http://localhost:14268/api/traces
EOF
    print_status ".env file created with development settings"
else
    print_status ".env file already exists"
fi

# Step 7: Check if port 8888 is available
print_info "Checking if port 8888 is available..."
if lsof -i :8888 >/dev/null 2>&1; then
    print_warning "Port 8888 is in use. Attempting to stop existing processes..."
    pkill -f "python.*uvicorn" 2>/dev/null || true
    sleep 2
    if lsof -i :8888 >/dev/null 2>&1; then
        print_error "Could not free port 8888. Please stop the process manually:"
        lsof -i :8888
        exit 1
    fi
fi
print_status "Port 8888 is available"

# Step 8: Start the application
echo ""
print_info "Starting the FastAPI application..."
print_info "The application will be available at: http://127.0.0.1:8888"
print_info "API Documentation will be at: http://127.0.0.1:8888/docs"
echo ""
print_warning "Press Ctrl+C to stop the application"
echo ""

# Start the application
python -m uvicorn app.main:app --host 127.0.0.1 --port 8888 --reload