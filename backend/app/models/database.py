"""Database models using SQLAlchemy."""

from datetime import datetime
from typing import Optional
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, JSON, Boolean, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
import os

Base = declarative_base()


class Query(Base):
    """Model for storing query history."""
    __tablename__ = "queries"
    
    id = Column(Integer, primary_key=True, index=True)
    query_text = Column(Text, nullable=False)
    answer = Column(Text, nullable=True)
    sources_count = Column(Integer, default=0)
    response_time_ms = Column(Float, nullable=True)
    embedding_time_ms = Column(Float, nullable=True)
    retrieval_time_ms = Column(Float, nullable=True)
    synthesis_time_ms = Column(Float, nullable=True)
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    extra_metadata = Column(JSON, nullable=True)  # Renamed from 'metadata' (reserved in SQLAlchemy)


class Document(Base):
    """Model for storing document metadata."""
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    file_type = Column(String(50), nullable=False)
    pages = Column(Integer, nullable=True)
    chunks_count = Column(Integer, default=0)
    vectors_count = Column(Integer, default=0)
    upload_date = Column(DateTime, default=datetime.utcnow)
    status = Column(String(50), default="processed")  # processed, processing, failed
    extra_metadata = Column(JSON, nullable=True)  # Renamed from 'metadata' (reserved in SQLAlchemy)
    query_count = Column(Integer, default=0)  # How many times this doc was queried


class Metric(Base):
    """Model for storing system metrics."""
    __tablename__ = "metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    metric_type = Column(String(100), nullable=False)  # query_count, avg_response_time, etc.
    metric_value = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    extra_metadata = Column(JSON, nullable=True)  # Renamed from 'metadata' (reserved in SQLAlchemy)


class ChunkMetadata(Base):
    """Model for storing chunk metadata mapped to FAISS index IDs."""
    __tablename__ = "chunk_metadata"
    
    id = Column(Integer, primary_key=True, index=True)
    faiss_id = Column(Integer, nullable=False, unique=True, index=True)  # FAISS index ID
    chunk_text = Column(Text, nullable=False)
    extra_metadata = Column(JSON, nullable=True)  # Additional metadata (page, source, etc.) - renamed from 'metadata' (reserved in SQLAlchemy)
    created_at = Column(DateTime, default=datetime.utcnow)


# Database setup
# Import settings if available, otherwise use environment variable
try:
    from app.core.config import settings
    DATABASE_URL = settings.DATABASE_URL
except ImportError:
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/app.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)
    print("Database initialized")


@contextmanager
def get_db():
    """Database session context manager."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

