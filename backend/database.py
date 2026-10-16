"""Database models and initialization for the AI Assistant."""
import os
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import Column, String, DateTime, Text, Integer, Boolean, create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import StaticPool

Base = declarative_base()


class Conversation(Base):
    """Stores conversation history."""
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    is_sensitive = Column(Boolean, default=False)  # Mark sensitive data for auto-purge


class Memory(Base):
    """Stores semantic memories for retrieval."""
    __tablename__ = "memories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    content = Column(Text, nullable=False)
    embedding_id = Column(String(100), nullable=True)  # ChromaDB ID
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    tags = Column(String(500), nullable=True)  # Comma-separated tags
    is_sensitive = Column(Boolean, default=False)


class Settings(Base):
    """Application settings."""
    __tablename__ = "settings"

    key = Column(String(100), primary_key=True)
    value = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DatabaseManager:
    """Manages database connections and operations."""

    def __init__(self, database_url: str = "sqlite+aiosqlite:///./data/assistant.db"):
        self.database_url = database_url
        self.engine = create_async_engine(
            database_url,
            connect_args={"check_same_thread": False} if "sqlite" in database_url else {},
            poolclass=StaticPool if "sqlite" in database_url else None,
        )
        self.async_session = async_sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def init_db(self):
        """Initialize database tables."""
        # Ensure data directory exists
        os.makedirs("./data", exist_ok=True)

        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def purge_old_sensitive_data(self, retention_days: int = 90):
        """Delete sensitive data older than retention period."""
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

        async with self.async_session() as session:
            # Delete old sensitive conversations
            from sqlalchemy import delete
            stmt = delete(Conversation).where(
                Conversation.is_sensitive == True,
                Conversation.timestamp < cutoff_date
            )
            await session.execute(stmt)

            # Delete old sensitive memories
            stmt = delete(Memory).where(
                Memory.is_sensitive == True,
                Memory.created_at < cutoff_date
            )
            await session.execute(stmt)

            await session.commit()

    async def get_recent_conversations(
        self,
        session_id: str,
        limit: int = 10
    ) -> list[Conversation]:
        """Get recent conversations for context."""
        from sqlalchemy import select

        async with self.async_session() as session:
            stmt = (
                select(Conversation)
                .where(Conversation.session_id == session_id)
                .order_by(Conversation.timestamp.desc())
                .limit(limit)
            )
            result = await session.execute(stmt)
            conversations = result.scalars().all()
            return list(reversed(conversations))  # Return in chronological order

    async def add_conversation(
        self,
        session_id: str,
        role: str,
        content: str,
        is_sensitive: bool = False
    ) -> Conversation:
        """Add a new conversation entry."""
        async with self.async_session() as session:
            conversation = Conversation(
                session_id=session_id,
                role=role,
                content=content,
                is_sensitive=is_sensitive
            )
            session.add(conversation)
            await session.commit()
            await session.refresh(conversation)
            return conversation
