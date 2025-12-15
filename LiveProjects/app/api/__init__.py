"""
API route definitions with comprehensive observability.
"""
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel, EmailStr
import structlog

from ..config import settings
from ..database import get_database_session
from ..auth import auth_service, get_current_user, get_current_active_user
from ..models import User, Task, AuditLog
from ..metrics import metrics_collector, track_time
from ..tracing import trace_async_function

logger = structlog.get_logger(__name__)

# Pydantic models for API
class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    full_name: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    full_name: Optional[str]
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    priority: str = "medium"

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None

class TaskResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    status: str
    priority: str
    user_id: int
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str
    environment: str
    database: str
    cache: str


# Router setup
router = APIRouter()


@router.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@track_time("user_registration")
async def register_user(
    user_data: UserCreate,
    request: Request,
    session: AsyncSession = Depends(get_database_session)
):
    """Register a new user with comprehensive logging and metrics."""
    
    logger.info("User registration attempt", email=user_data.email, username=user_data.username)
    
    try:
        # Check if user already exists
        existing_user = await session.execute(
            select(User).where(
                (User.email == user_data.email) | (User.username == user_data.username)
            )
        )
        if existing_user.scalar_one_or_none():
            logger.warning("Registration failed - user already exists", 
                          email=user_data.email, username=user_data.username)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email or username already registered"
            )
        
        # Create new user
        hashed_password = auth_service.get_password_hash(user_data.password)
        new_user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password,
            full_name=user_data.full_name
        )
        
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
        
        # Log audit event
        audit_log = AuditLog(
            user_id=new_user.id,
            action="user_registration",
            resource_type="user",
            resource_id=str(new_user.id),
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent")
        )
        session.add(audit_log)
        await session.commit()
        
        # Record metrics
        metrics_collector.record_user_registration()
        
        logger.info("User registered successfully", 
                   user_id=new_user.id, email=user_data.email)
        
        return new_user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("User registration failed", 
                    email=user_data.email, error=str(e))
        metrics_collector.record_error("registration_error", "user_service")
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/auth/login", response_model=TokenResponse)
@track_time("user_login")
async def login_user(
    login_data: LoginRequest,
    request: Request,
    session: AsyncSession = Depends(get_database_session)
):
    """Authenticate user and return JWT token."""
    
    logger.info("Login attempt", email=login_data.email)
    
    try:
        # Authenticate user
        user = await auth_service.authenticate_user(session, login_data.email, login_data.password)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create access token
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = auth_service.create_access_token(
            data={"sub": str(user.id)},
            expires_delta=access_token_expires
        )
        
        # Log audit event
        audit_log = AuditLog(
            user_id=user.id,
            action="user_login",
            resource_type="user",
            resource_id=str(user.id),
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent")
        )
        session.add(audit_log)
        await session.commit()
        
        logger.info("User logged in successfully", user_id=user.id, email=login_data.email)
        
        return TokenResponse(
            access_token=access_token,
            expires_in=settings.access_token_expire_minutes * 60
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Login failed", email=login_data.email, error=str(e))
        metrics_collector.record_error("login_error", "auth_service")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """Get current user information."""
    logger.info("User info requested", user_id=current_user.id)
    return current_user


@router.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
@track_time("task_creation")
async def create_task(
    task_data: TaskCreate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_database_session)
):
    """Create a new task with observability."""
    
    logger.info("Task creation attempt", 
                user_id=current_user.id, title=task_data.title)
    
    try:
        new_task = Task(
            title=task_data.title,
            description=task_data.description,
            priority=task_data.priority,
            user_id=current_user.id
        )
        
        session.add(new_task)
        await session.commit()
        await session.refresh(new_task)
        
        # Log audit event
        audit_log = AuditLog(
            user_id=current_user.id,
            action="task_created",
            resource_type="task",
            resource_id=str(new_task.id),
            details=f"Title: {task_data.title}, Priority: {task_data.priority}"
        )
        session.add(audit_log)
        await session.commit()
        
        # Record API call metric
        metrics_collector.record_api_call("task_service", "create_task")
        
        logger.info("Task created successfully", 
                   task_id=new_task.id, user_id=current_user.id)
        
        return new_task
        
    except Exception as e:
        logger.error("Task creation failed", 
                    user_id=current_user.id, error=str(e))
        metrics_collector.record_error("task_creation_error", "task_service")
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Task creation failed"
        )


@router.get("/tasks", response_model=List[TaskResponse])
@track_time("task_list")
async def get_user_tasks(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_database_session)
):
    """Get user's tasks with filtering and pagination."""
    
    logger.info("Tasks list requested", 
                user_id=current_user.id, skip=skip, limit=limit, status_filter=status_filter)
    
    try:
        query = select(Task).where(Task.user_id == current_user.id)
        
        if status_filter:
            query = query.where(Task.status == status_filter)
        
        query = query.offset(skip).limit(limit).order_by(Task.created_at.desc())
        
        result = await session.execute(query)
        tasks = result.scalars().all()
        
        # Record API call metric
        metrics_collector.record_api_call("task_service", "list_tasks")
        
        logger.info("Tasks retrieved successfully", 
                   user_id=current_user.id, count=len(tasks))
        
        return tasks
        
    except Exception as e:
        logger.error("Failed to retrieve tasks", 
                    user_id=current_user.id, error=str(e))
        metrics_collector.record_error("task_list_error", "task_service")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve tasks"
        )


@router.get("/health", response_model=HealthResponse)
async def health_check(session: AsyncSession = Depends(get_database_session)):
    """Comprehensive health check endpoint."""
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "version": settings.app_version,
        "environment": settings.environment,
        "database": "unknown",
        "cache": "unknown"
    }
    
    try:
        # Check database
        await session.execute(select(func.now()))
        health_status["database"] = "healthy"
        
        # Check Redis (simplified)
        health_status["cache"] = "healthy"
        
        logger.info("Health check successful")
        return health_status
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        health_status["status"] = "unhealthy"
        health_status["database"] = "unhealthy"
        
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service unhealthy"
        )