"""
Authentication and authorization utilities.
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog

from ..config import settings
from ..database import get_database_session
from ..models import User
from ..metrics import metrics_collector

logger = structlog.get_logger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT token bearer
security = HTTPBearer()


class AuthService:
    """Authentication service with comprehensive logging and metrics."""
    
    def __init__(self):
        self.secret_key = settings.secret_key
        self.algorithm = settings.algorithm
        self.access_token_expire_minutes = settings.access_token_expire_minutes
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception as e:
            logger.error("Password verification failed", error=str(e))
            return False
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password."""
        return pwd_context.hash(password)
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token."""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        
        try:
            encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
            logger.info("Access token created", 
                       user_id=data.get("sub"), 
                       expires_at=expire.isoformat())
            return encoded_jwt
        except Exception as e:
            logger.error("Token creation failed", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not create access token"
            )
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id: str = payload.get("sub")
            
            if user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            logger.debug("Token verified successfully", user_id=user_id)
            return payload
            
        except JWTError as e:
            logger.warning("Token verification failed", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    async def authenticate_user(self, session: AsyncSession, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password."""
        try:
            # Get user from database
            result = await session.execute(
                select(User).where(User.email == email, User.is_active == True)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                logger.warning("Authentication failed - user not found", email=email)
                metrics_collector.record_login_attempt(success=False)
                return None
            
            if not self.verify_password(password, user.hashed_password):
                logger.warning("Authentication failed - invalid password", email=email, user_id=user.id)
                metrics_collector.record_login_attempt(success=False)
                return None
            
            # Update last login
            user.last_login = datetime.utcnow()
            await session.commit()
            
            logger.info("User authenticated successfully", email=email, user_id=user.id)
            metrics_collector.record_login_attempt(success=True)
            return user
            
        except Exception as e:
            logger.error("Authentication error", email=email, error=str(e))
            metrics_collector.record_error("authentication_error", "auth_service")
            await session.rollback()
            return None
    
    async def get_current_user(
        self,
        session: AsyncSession,
        credentials: HTTPAuthorizationCredentials
    ) -> User:
        """Get current user from JWT token."""
        token = credentials.credentials
        payload = self.verify_token(token)
        user_id = payload.get("sub")
        
        try:
            result = await session.execute(
                select(User).where(User.id == int(user_id), User.is_active == True)
            )
            user = result.scalar_one_or_none()
            
            if user is None:
                logger.warning("User not found for valid token", user_id=user_id)
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            return user
            
        except ValueError:
            logger.warning("Invalid user ID in token", user_id=user_id)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user ID",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except Exception as e:
            logger.error("Error getting current user", user_id=user_id, error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not validate credentials"
            )


# Global auth service instance
auth_service = AuthService()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_database_session)
) -> User:
    """Dependency to get current authenticated user."""
    return await auth_service.get_current_user(session, credentials)


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Dependency to get current active user."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


async def get_current_superuser(current_user: User = Depends(get_current_user)) -> User:
    """Dependency to get current superuser."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user