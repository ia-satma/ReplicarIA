"""
PostgreSQL User Database Service for Authentication
Uses SQLAlchemy with async support for PostgreSQL
"""
import os
import logging
from datetime import datetime, timezone
from typing import Optional, List, Sequence, Any
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, String, Boolean, DateTime, Text, select, update, delete
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

logger = logging.getLogger(__name__)

def prepare_database_url(url: str) -> str:
    """Prepare the DATABASE_URL for asyncpg by handling SSL mode"""
    if not url:
        return url
    
    if url.startswith('postgres://'):
        url = url.replace('postgres://', 'postgresql+asyncpg://', 1)
    elif url.startswith('postgresql://'):
        url = url.replace('postgresql://', 'postgresql+asyncpg://', 1)
    
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)
    
    if 'sslmode' in query_params:
        del query_params['sslmode']
    
    new_query = urlencode(query_params, doseq=True)
    new_url = urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        new_query,
        parsed.fragment
    ))
    
    return new_url

DATABASE_URL = prepare_database_url(os.environ.get('DATABASE_URL', ''))

class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'
    
    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=True)
    full_name = Column(String, nullable=True)
    company = Column(String, nullable=True)
    role = Column(String, default='user')
    is_active = Column(Boolean, default=False)
    approval_status = Column(String, default='pending')
    approval_token = Column(String, nullable=True)
    auth_provider = Column(String, default='email')
    profile_image_url = Column(Text, nullable=True)
    allowed_companies = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    approved_at = Column(DateTime(timezone=True), nullable=True)
    approved_by = Column(String, nullable=True)

    def to_dict(self) -> dict[str, Any]:
        created_at_val = self.created_at
        updated_at_val = self.updated_at
        allowed = []
        if self.allowed_companies:
            try:
                import json
                allowed = json.loads(self.allowed_companies)
            except (json.JSONDecodeError, TypeError, ValueError):
                # Fallback: treat as comma-separated string
                allowed = [c.strip() for c in self.allowed_companies.split(',') if c.strip()]
        return {
            'user_id': self.id,
            'email': self.email,
            'full_name': self.full_name,
            'company': self.company,
            'role': self.role,
            'is_active': self.is_active,
            'approval_status': self.approval_status,
            'auth_provider': self.auth_provider,
            'profile_image_url': self.profile_image_url,
            'allowed_companies': allowed,
            'created_at': created_at_val.isoformat() if created_at_val is not None else None,
            'updated_at': updated_at_val.isoformat() if updated_at_val is not None else None,
        }


engine = None
async_session_factory = None


async def init_db():
    """Initialize the database connection and create tables"""
    global engine, async_session_factory
    
    if not DATABASE_URL:
        logger.warning("DATABASE_URL not set - user authentication will not work")
        return False
    
    try:
        engine = create_async_engine(
            DATABASE_URL,
            echo=False,
            pool_pre_ping=True,
            pool_recycle=300,
        )
        
        async_session_factory = async_sessionmaker(
            engine, 
            class_=AsyncSession, 
            expire_on_commit=False
        )
        
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("PostgreSQL user database initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize PostgreSQL user database: {e}")
        return False


@asynccontextmanager
async def get_session():
    """Get an async database session"""
    if async_session_factory is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    
    session = async_session_factory()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


class UserService:
    """Service for user database operations"""
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        async with get_session() as session:
            result = await session.execute(
                select(User).where(User.email == email)
            )
            return result.scalar_one_or_none()
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        async with get_session() as session:
            result = await session.execute(
                select(User).where(User.id == user_id)
            )
            return result.scalar_one_or_none()
    
    async def create_user(self, user_data: dict) -> User:
        """Create a new user"""
        async with get_session() as session:
            user = User(
                id=user_data['user_id'],
                email=user_data['email'],
                password_hash=user_data.get('password_hash'),
                full_name=user_data.get('full_name'),
                company=user_data.get('company'),
                role=user_data.get('role', 'user'),
                is_active=user_data.get('is_active', False),
                approval_status=user_data.get('approval_status', 'pending'),
                approval_token=user_data.get('approval_token'),
                auth_provider=user_data.get('auth_provider', 'email'),
                profile_image_url=user_data.get('profile_image_url'),
            )
            session.add(user)
            await session.flush()
            await session.refresh(user)
            return user
    
    async def update_user(self, user_id: str, update_data: dict) -> bool:
        """Update user by ID"""
        async with get_session() as session:
            result = await session.execute(
                update(User).where(User.id == user_id).values(**update_data)
            )
            rowcount: int = getattr(result, 'rowcount', 0) or 0
            return rowcount > 0
    
    async def delete_user(self, user_id: str) -> bool:
        """Delete user by ID"""
        async with get_session() as session:
            result = await session.execute(
                delete(User).where(User.id == user_id)
            )
            rowcount: int = getattr(result, 'rowcount', 0) or 0
            return rowcount > 0
    
    async def get_user_by_approval_token(self, user_id: str, token: str) -> Optional[User]:
        """Get user by ID and approval token"""
        async with get_session() as session:
            result = await session.execute(
                select(User).where(
                    User.id == user_id,
                    User.approval_token == token
                )
            )
            return result.scalar_one_or_none()
    
    async def get_pending_users(self) -> Sequence[User]:
        """Get all users with pending approval status"""
        async with get_session() as session:
            result = await session.execute(
                select(User).where(User.approval_status == 'pending').order_by(User.created_at.desc())
            )
            return result.scalars().all()
    
    async def get_all_users(self) -> Sequence[User]:
        """Get all users"""
        async with get_session() as session:
            result = await session.execute(
                select(User).order_by(User.created_at.desc())
            )
            return result.scalars().all()
    
    async def update_user_approval(self, user_id: str, approval_status: str, is_active: bool, approved_by: Optional[str] = None) -> bool:
        """Update user approval status and active state"""
        async with get_session() as session:
            update_data = {
                'approval_status': approval_status,
                'is_active': is_active,
                'updated_at': datetime.now(timezone.utc)
            }
            if approved_by:
                update_data['approved_by'] = approved_by
                update_data['approved_at'] = datetime.now(timezone.utc)
            
            result = await session.execute(
                update(User).where(User.id == user_id).values(**update_data)
            )
            rowcount: int = getattr(result, 'rowcount', 0) or 0
            return rowcount > 0
    
    async def update_user_allowed_companies(self, user_id: str, allowed_companies: List[str]) -> bool:
        """Update user's allowed companies list"""
        import json
        async with get_session() as session:
            companies_json = json.dumps(allowed_companies)
            result = await session.execute(
                update(User).where(User.id == user_id).values(
                    allowed_companies=companies_json,
                    updated_at=datetime.now(timezone.utc)
                )
            )
            rowcount: int = getattr(result, 'rowcount', 0) or 0
            return rowcount > 0


user_service = UserService()
