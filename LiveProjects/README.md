# Production Python Application with Observability

A comprehensive, production-ready Python application demonstrating modern observability practices including structured logging, metrics collection, and distributed tracing. Perfect for demonstrating enterprise-level Python development skills in interviews.

## 🌟 Key Features

### Core Application
- **FastAPI Framework**: High-performance async web framework
- **SQLite Database**: Lightweight database for development (PostgreSQL ready for production)
- **JWT Authentication**: Secure user authentication and authorization
- **RESTful API**: Well-designed API endpoints with proper HTTP status codes
- **Input Validation**: Comprehensive request/response validation with Pydantic

### Observability Stack
- **Structured Logging**: JSON-formatted logs with contextual information
- **Prometheus Metrics**: Business and technical metrics collection
- **OpenTelemetry Tracing**: Distributed tracing across all components (configurable)
- **Health Checks**: Kubernetes-ready health endpoints

### Production Features
- **Environment Configuration**: Proper configuration management with .env support
- **Database Operations**: SQLAlchemy async operations with proper session management
- **Error Handling**: Comprehensive error handling with proper logging
- **Security**: Password hashing, JWT tokens, input sanitization
- **CORS Support**: Cross-origin resource sharing configuration
- **Request Correlation**: Every request tracked with unique correlation IDs

### DevOps & Monitoring
- **Docker Support**: Multi-stage Dockerfile with security best practices
- **Docker Compose**: Complete development environment
- **Prometheus Integration**: Metrics scraping configuration
- **Health Endpoints**: Ready for Kubernetes deployments

## 🚀 Step-by-Step Setup Guide

### Prerequisites Check
Before starting, ensure you have:
- **Python 3.9 or higher**: Check with `python3 --version`
- **Git**: Check with `git --version`
- **curl**: Check with `curl --version` (for testing)

### Method 1: One-Command Setup (Easiest)

#### Single Command to Setup and Run
```bash
# Navigate to project directory and run the setup script
cd "/Users/venkatesh/Devops Sucess Batch/LiveProjects"
./run.sh
```

**What this script does:**
1. ✅ Checks Python installation
2. ✅ Creates virtual environment
3. ✅ Installs all dependencies
4. ✅ Creates .env configuration
5. ✅ Starts the application

**Expected Final Output:**
```
🚀 Production Observability App - Setup & Run
================================================
✅ Current directory: /Users/venkatesh/Devops Sucess Batch/LiveProjects
✅ Python version: 3.11.9
✅ Virtual environment activated
✅ Dependencies installed
✅ All critical packages installed correctly
✅ .env file created with development settings
✅ Port 8888 is available

ℹ️  Starting the FastAPI application...
ℹ️  The application will be available at: http://127.0.0.1:8888
ℹ️  API Documentation will be at: http://127.0.0.1:8888/docs

INFO:     Uvicorn running on http://127.0.0.1:8888 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

#### Test Everything Works
```bash
# In a new terminal window, run the comprehensive test
cd "/Users/venkatesh/Devops Sucess Batch/LiveProjects"
./test_api.sh
```

### Method 2: Manual Step-by-Step Setup

#### Step 1: Navigate to Project Directory
```bash
cd "/Users/venkatesh/Devops Sucess Batch/LiveProjects"
```

#### Step 2: Set Up Python Virtual Environment
```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment (macOS/Linux)
source .venv/bin/activate

# Verify virtual environment is active (should show (.venv) in prompt)
which python
```

#### Step 3: Install Dependencies
```bash
# Upgrade pip first
pip install --upgrade pip

# Install all required packages
pip install -r requirements.txt

# Verify critical packages are installed
python -c "import fastapi, uvicorn, sqlalchemy; print('✅ Core packages installed')"
```

#### Step 4: Configure Environment
```bash
# The .env file is already configured for development
# Verify it exists
ls -la .env

# Check configuration
cat .env
```

#### Step 5: Start the Application
```bash
# Start the FastAPI application
python -m uvicorn app.main:app --host 127.0.0.1 --port 8888 --reload
```

**Expected Output:**
```
INFO:     Will watch for changes in these directories: ['/Users/venkatesh/Devops Sucess Batch/LiveProjects']
INFO:     Uvicorn running on http://127.0.0.1:8888 (Press CTRL+C to quit)
INFO:     Started reloader process [xxxxx] using WatchFiles
Metrics collector initialized enabled=True
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
{"app_name": "Production Observability App", "version": "1.0.0", "environment": "development", "event": "Starting application", "level": "info"}
Database initialized successfully
{"event": "Application startup completed successfully", "level": "info"}
INFO:     Application startup complete.
```

### Method 3: Background Process (For Continuous Running)

#### Step 1-3: Same as Method 2

#### Step 4: Start in Background
```bash
# Start application in background
nohup python -m uvicorn app.main:app --host 127.0.0.1 --port 8888 > server.log 2>&1 &

# Check if it's running
curl -s http://127.0.0.1:8888/ | python -c "import sys, json; print('Status:', json.load(sys.stdin)['status'])"
```

### Access Points
Once running, access the application at:
- **Main Application**: http://127.0.0.1:8888/
- **Interactive API Documentation**: http://127.0.0.1:8888/docs
- **Health Check**: http://127.0.0.1:8888/api/v1/health
- **Prometheus Metrics**: http://127.0.0.1:8888/metrics

## 🧪 Testing the Application

### Step 1: Verify Application is Running
```bash
# Test root endpoint
curl -s http://127.0.0.1:8888/ | python -c "import sys, json; print(json.dumps(json.load(sys.stdin), indent=2))"
```

**Expected Response:**
```json
{
  "message": "Production Observability Application",
  "version": "1.0.0",
  "environment": "development",
  "status": "running"
}
```

### Step 2: Check Health Status
```bash
# Test health endpoint
curl -s http://127.0.0.1:8888/api/v1/health | python -c "import sys, json; print(json.dumps(json.load(sys.stdin), indent=2))"
```

**Expected Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-04T06:34:28.247589",
  "version": "1.0.0",
  "environment": "development",
  "database": "healthy",
  "cache": "healthy"
}
```

### Step 3: Test User Registration
```bash
# Register a new user
curl -s -X POST http://127.0.0.1:8888/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "test123",
    "full_name": "Test User"
  }' | python -c "import sys, json; print(json.dumps(json.load(sys.stdin), indent=2))"
```

**Expected Response:**
```json
{
  "id": 1,
  "email": "test@example.com",
  "username": "testuser",
  "full_name": "Test User",
  "is_active": true,
  "created_at": "2025-11-04T06:36:21"
}
```

### Step 4: Test User Login
```bash
# Login to get JWT token
curl -s -X POST http://127.0.0.1:8888/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "test123"
  }' | python -c "import sys, json; print(json.dumps(json.load(sys.stdin), indent=2))"
```

**Expected Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### Step 5: Test Task Creation (with Authentication)
```bash
# Save the token from login response
TOKEN="your-jwt-token-here"

# Create a task
curl -s -X POST http://127.0.0.1:8888/api/v1/tasks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "title": "Sample Task",
    "description": "This is a test task",
    "priority": "high"
  }' | python -c "import sys, json; print(json.dumps(json.load(sys.stdin), indent=2))"
```

### Step 6: Test Task Retrieval
```bash
# Get user's tasks
curl -s -X GET http://127.0.0.1:8888/api/v1/tasks \
  -H "Authorization: Bearer $TOKEN" | python -c "import sys, json; print(json.dumps(json.load(sys.stdin), indent=2))"
```

### Step 7: Check Metrics Collection
```bash
# View Prometheus metrics
curl -s http://127.0.0.1:8888/metrics | head -20
```

## 🚨 Troubleshooting Guide

### Common Issues and Solutions

#### Issue 1: Port Already in Use
**Error:** `ERROR: [Errno 48] Address already in use`

**Solution:**
```bash
# Find process using the port
lsof -i :8888

# Kill the process (replace PID with actual process ID)
kill -9 <PID>

# Or kill all uvicorn processes
pkill -f "python.*uvicorn"

# Then restart the application
python -m uvicorn app.main:app --host 127.0.0.1 --port 8888
```

#### Issue 2: Module Not Found
**Error:** `ModuleNotFoundError: No module named 'xxx'`

**Solution:**
```bash
# Ensure virtual environment is activated
source .venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt

# For specific missing modules
pip install <module-name>
```

#### Issue 3: Permission Denied
**Error:** `Permission denied` when running scripts

**Solution:**
```bash
# Make script executable
chmod +x start.sh

# Or run with python directly
python -m uvicorn app.main:app --host 127.0.0.1 --port 8888
```

#### Issue 4: Database Connection Error
**Error:** Database-related errors

**Solution:**
```bash
# Check if app.db file exists
ls -la app.db

# If missing, restart the application (it will recreate)
python -m uvicorn app.main:app --host 127.0.0.1 --port 8888
```

#### Issue 5: Import Errors
**Error:** Various import errors

**Solution:**
```bash
# Ensure you're in the correct directory
pwd  # Should show: /Users/venkatesh/Devops Sucess Batch/LiveProjects

# Activate virtual environment
source .venv/bin/activate

# Check Python path
python -c "import sys; print(sys.path)"
```

## 🔄 Starting/Stopping the Application

### Starting the Application
```bash
# Method 1: Foreground (with logs visible)
python -m uvicorn app.main:app --host 127.0.0.1 --port 8888 --reload

# Method 2: Background process
nohup python -m uvicorn app.main:app --host 127.0.0.1 --port 8888 > server.log 2>&1 &

# Method 3: Using the start script
./start.sh
```

### Stopping the Application
```bash
# If running in foreground: Press Ctrl+C

# If running in background:
pkill -f "python.*uvicorn"

# Or find and kill specific process:
ps aux | grep uvicorn
kill -9 <PID>
```

### Checking if Application is Running
```bash
# Check if process is running
ps aux | grep uvicorn

# Test if responding
curl -s http://127.0.0.1:8888/ | grep -o '"status":"running"' && echo " ✅ Application is running"

# Check logs (if running in background)
tail -f server.log
```

## 📊 Observability Features

### Structured Logging
The application automatically logs all requests with correlation IDs:
```json
{
  "method": "POST",
  "path": "/api/v1/auth/login",
  "status_code": 200,
  "duration": "0.025s",
  "request_id": "baceb34d-20b2-413a-9652-33d407a5cee0",
  "level": "info"
}
```

### Metrics Collection
View real-time metrics at: http://127.0.0.1:8888/metrics

Key metrics include:
- `http_requests_total`: Total HTTP requests by method, endpoint, status
- `http_request_duration_seconds`: Request duration histogram
- `user_registrations_total`: Business metric for user registrations
- `login_attempts_total`: Login attempts by success/failure
- `errors_total`: Error count by type and service

### Health Monitoring
Multiple health check endpoints:
- `/api/v1/health`: Comprehensive health check with database status
- `/ready`: Kubernetes readiness probe
- `/live`: Kubernetes liveness probe

## 🏗️ Project Architecture

### Application Structure
```
app/
├── __init__.py
├── main.py              # FastAPI application and middleware
├── config.py            # Configuration management
├── logging_config.py    # Structured logging setup
├── metrics.py           # Prometheus metrics
├── tracing.py           # OpenTelemetry configuration
├── database.py          # Database connection and session management
├── models/              # SQLAlchemy models
│   └── __init__.py      # User, Task, AuditLog, MetricSnapshot models
├── api/                 # API route handlers
│   └── __init__.py      # Authentication and task endpoints
└── auth/                # Authentication and authorization
    └── __init__.py      # JWT handling, password hashing
```

### Key Design Patterns

#### Configuration Management
- Environment-based configuration with Pydantic Settings
- Development/production environment detection
- Secure default configurations

#### Database Layer
- Async SQLAlchemy with proper session management
- Automatic table creation on startup
- Proper indexing for performance
- Audit logging for important events

#### Authentication & Security
- JWT token-based authentication with configurable expiration
- Bcrypt password hashing with proper salt rounds
- Request validation and sanitization
- CORS configuration for cross-origin requests

#### Observability Integration
- Request correlation IDs for tracing requests across logs
- Prometheus metrics for monitoring and alerting
- Structured JSON logging for log aggregation
- Health check endpoints for container orchestration

## 📈 Production Deployment Considerations

### Environment Variables for Production
```bash
# Application
APP_NAME=Production Observability App
ENVIRONMENT=production
DEBUG=false

# Database (switch to PostgreSQL for production)
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db

# Security (generate secure keys)
SECRET_KEY=your-super-secure-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Monitoring
METRICS_ENABLED=true
TRACING_ENABLED=true
JAEGER_ENDPOINT=http://jaeger:14268/api/traces
```

### Docker Deployment
```bash
# Build production image
docker build -t observability-app:latest .

# Run with production settings
docker run -p 8888:8888 \
  -e ENVIRONMENT=production \
  -e DATABASE_URL=postgresql+asyncpg://... \
  -e SECRET_KEY=your-production-secret \
  observability-app:latest
```

### Kubernetes Deployment
The application includes built-in support for:
- **Readiness probe**: `GET /ready` (checks if app can serve traffic)
- **Liveness probe**: `GET /live` (checks if app is alive)
- **Health check**: `GET /api/v1/health` (comprehensive health status)
- **Metrics endpoint**: `GET /metrics` (Prometheus scraping)

### Monitoring and Alerting
Pre-configured metrics suitable for:
- Application performance monitoring (APM)
- Business metrics tracking
- Error rate monitoring
- Infrastructure monitoring
- Custom dashboard creation

## 🧪 Testing

### Run Automated Tests
```bash
# Install test dependencies (included in requirements.txt)
pip install pytest pytest-asyncio pytest-cov httpx

# Run all tests
pytest

# Run tests with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_api.py -v

# Run tests and generate coverage report
pytest --cov=app tests/ --cov-report=term-missing
```

### Test Structure
- **conftest.py**: Test configuration and fixtures
- **test_api.py**: API endpoint tests covering authentication and task management
- **Integration tests**: Database and external service testing
- **Coverage reporting**: HTML and terminal coverage reports

### Manual Testing Checklist
1. ✅ Application starts without errors
2. ✅ Health check returns healthy status
3. ✅ User registration works
4. ✅ User login returns valid JWT token
5. ✅ Authenticated endpoints require valid token
6. ✅ Task creation and retrieval works
7. ✅ Metrics endpoint returns Prometheus format
8. ✅ Logs show structured JSON format
9. ✅ API documentation is accessible

## 🎯 Interview Demonstration Guide

### What to Show
1. **Application Running**: Live demo of all endpoints
2. **Code Architecture**: Clean, modular, production-ready code
3. **Observability**: Logs, metrics, health checks in action
4. **Security**: Authentication flow and token validation
5. **Testing**: Comprehensive test coverage
6. **Documentation**: Complete API documentation

### Key Talking Points
1. **Modern Python**: Async/await patterns, type hints, context managers
2. **Production Patterns**: Proper error handling, configuration management
3. **Observability**: Structured logging, metrics collection, health monitoring
4. **Security**: JWT authentication, password hashing, input validation
5. **Performance**: Async database operations, proper indexing
6. **Maintainability**: Clean architecture, comprehensive documentation
7. **DevOps Ready**: Docker support, health checks, metrics endpoints

### Sample Interview Questions & Answers

**Q: How do you handle database connections in production?**
A: Using SQLAlchemy's async engine with connection pooling, proper session management with dependency injection, and graceful shutdown handling.

**Q: How do you implement observability?**
A: Three pillars - structured JSON logging with correlation IDs, Prometheus metrics for monitoring, and health checks for operational visibility.

**Q: How do you ensure security?**
A: JWT token authentication, bcrypt password hashing, input validation with Pydantic, CORS configuration, and secure configuration management.

**Q: How would you scale this application?**
A: Horizontal scaling with multiple instances, database read replicas, Redis for caching, load balancer with health checks, and metrics-based auto-scaling.

## � API Documentation

### Authentication Endpoints
- `POST /api/v1/auth/register`: User registration
- `POST /api/v1/auth/login`: User authentication
- `GET /api/v1/auth/me`: Current user information

### Task Management Endpoints
- `POST /api/v1/tasks`: Create new task (requires authentication)
- `GET /api/v1/tasks`: List user tasks with filtering (requires authentication)

### System Endpoints
- `GET /`: Application information
- `GET /docs`: Interactive API documentation
- `GET /api/v1/health`: Comprehensive health check
- `GET /metrics`: Prometheus metrics
- `GET /ready`: Readiness probe
- `GET /live`: Liveness probe

### Response Formats
All API responses follow consistent JSON format with proper HTTP status codes:
- `200 OK`: Successful requests
- `201 Created`: Resource creation
- `400 Bad Request`: Invalid input
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server errors

## 🤝 Contributing

This is a demonstration project showcasing production-ready Python development patterns. The code demonstrates:

- Clean architecture and separation of concerns
- Comprehensive error handling and logging
- Proper security implementations
- Production deployment readiness
- Extensive documentation and testing

## 📄 License

MIT License - This is a demonstration project for educational and interview purposes.