"""
Main FastAPI application with comprehensive observability features.
Production-ready Python application demonstrating logging, metrics, and tracing.
"""
import asyncio
import uuid
from contextlib import asynccontextmanager
from typing import Dict, Any
import time

from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
import structlog

from .config import settings
from .logging_config import setup_logging, get_logger, add_request_context
from .metrics import metrics_collector, CONTENT_TYPE_LATEST
from .tracing import setup_tracing, instrument_app
from .database import init_database, close_database
from .api import router

# Setup logging first
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager with proper startup and shutdown."""
    
    # Startup
    logger.info("Starting application", 
                app_name=settings.app_name,
                version=settings.app_version,
                environment=settings.environment)
    
    try:
        # Initialize tracing
        setup_tracing()
        
        # Initialize database
        await init_database()
        
        # Instrument the app for tracing
        instrument_app(app)
        
        logger.info("Application startup completed successfully")
        
        yield
        
    except Exception as e:
        logger.error("Application startup failed", error=str(e))
        raise
    
    finally:
        # Shutdown
        logger.info("Shutting down application")
        
        try:
            await close_database()
            logger.info("Application shutdown completed successfully")
        except Exception as e:
            logger.error("Error during application shutdown", error=str(e))


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Production-ready Python application with comprehensive observability",
    lifespan=lifespan,
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.is_development else ["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Comprehensive request/response logging and metrics middleware."""
    
    # Generate request ID
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    # Start timing
    start_time = time.time()
    
    # Extract request info
    method = request.method
    url = str(request.url)
    path = request.url.path
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    
    # Get request size
    request_size = int(request.headers.get("content-length", 0))
    
    # Add request context for structured logging
    with structlog.contextvars.bound_contextvars(**add_request_context(request_id)):
        
        logger.info("Request started",
                   method=method,
                   path=path,
                   client_ip=client_ip,
                   user_agent=user_agent,
                   request_size=request_size)
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Get response size
            response_size = 0
            if hasattr(response, 'body'):
                response_size = len(response.body) if response.body else 0
            
            # Record metrics
            metrics_collector.record_request(
                method=method,
                endpoint=path,
                status_code=response.status_code,
                duration=duration,
                request_size=request_size,
                response_size=response_size
            )
            
            # Log response
            logger.info("Request completed",
                       method=method,
                       path=path,
                       status_code=response.status_code,
                       duration=f"{duration:.3f}s",
                       response_size=response_size)
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            # Calculate duration for failed request
            duration = time.time() - start_time
            
            # Record error metrics
            status_code = 500
            if isinstance(e, HTTPException):
                status_code = e.status_code
            
            metrics_collector.record_request(
                method=method,
                endpoint=path,
                status_code=status_code,
                duration=duration,
                request_size=request_size
            )
            
            metrics_collector.record_error("request_error", "middleware")
            
            logger.error("Request failed",
                        method=method,
                        path=path,
                        status_code=status_code,
                        duration=f"{duration:.3f}s",
                        error=str(e))
            
            raise


# Include API routes
app.include_router(router, prefix="/api/v1")


@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint with basic application info."""
    return {
        "message": "Production Observability Application",
        "version": settings.app_version,
        "environment": settings.environment,
        "status": "running"
    }


@app.get("/metrics", response_class=PlainTextResponse, include_in_schema=False)
async def metrics():
    """Prometheus metrics endpoint."""
    if not settings.metrics_enabled:
        raise HTTPException(status_code=404, detail="Metrics not enabled")
    
    return Response(
        content=metrics_collector.get_metrics(),
        media_type=CONTENT_TYPE_LATEST
    )


@app.get("/ready", include_in_schema=False)
async def readiness_check():
    """Kubernetes readiness probe."""
    return {"status": "ready", "timestamp": time.time()}


@app.get("/live", include_in_schema=False)
async def liveness_check():
    """Kubernetes liveness probe."""
    return {"status": "alive", "timestamp": time.time()}


def main():
    """Main entry point for running the application."""
    import uvicorn
    
    logger.info("Starting server",
                host=settings.host,
                port=settings.port,
                workers=settings.workers)
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        workers=settings.workers if settings.is_production else 1,
        reload=settings.is_development,
        log_config=None,  # Use our custom logging
        access_log=False,  # Handle access logging in middleware
    )


if __name__ == "__main__":
    main()