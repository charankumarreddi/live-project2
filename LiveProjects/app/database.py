"""
Database connection and session management.
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
import structlog

from .config import settings
from .models import Base

logger = structlog.get_logger(__name__)

# Database engine
engine = None
async_session_maker = None


async def init_database():
    """Initialize database connection and create tables."""
    global engine, async_session_maker
    
    try:
        # Create async engine with SQLite-compatible settings
        if settings.database_url.startswith("sqlite"):
            engine = create_async_engine(
                settings.database_url,
                pool_pre_ping=True,
                echo=not settings.is_production,  # Log SQL in development
                poolclass=NullPool,
                connect_args={"check_same_thread": False}
            )
        else:
            engine = create_async_engine(
                settings.database_url,
                pool_size=settings.database_pool_size,
                max_overflow=settings.database_max_overflow,
                pool_pre_ping=True,
                echo=not settings.is_production,  # Log SQL in development
                poolclass=NullPool if settings.is_development else None
            )
        
        # Create session maker
        async_session_maker = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        # Create tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("Database initialized successfully",
                   database_url=settings.database_url.split('@')[0] + '@***')
        
    except Exception as e:
        logger.error("Failed to initialize database", error=str(e))
        raise


async def get_database_session():
    """Get database session for dependency injection."""
    if async_session_maker is None:
        raise RuntimeError("Database not initialized")
    
    async with async_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def close_database():
    """Close database connections."""
    global engine
    
    if engine:
        await engine.dispose()
        logger.info("Database connections closed")