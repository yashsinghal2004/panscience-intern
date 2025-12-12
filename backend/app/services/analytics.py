"""Analytics service for tracking queries and metrics."""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy import func, desc
from sqlalchemy.orm import Session

from app.models.database import Query, Document, Metric, get_db

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for tracking and retrieving analytics."""
    
    def log_query(
        self,
        query_text: str,
        answer: Optional[str] = None,
        sources_count: int = 0,
        response_time_ms: Optional[float] = None,
        embedding_time_ms: Optional[float] = None,
        retrieval_time_ms: Optional[float] = None,
        synthesis_time_ms: Optional[float] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> None:
        """Log a query to the database.
        
        Args:
            query_text: The query text
            answer: Generated answer
            sources_count: Number of sources retrieved
            response_time_ms: Total response time in milliseconds
            embedding_time_ms: Embedding generation time
            retrieval_time_ms: Retrieval time
            synthesis_time_ms: Synthesis time
            success: Whether query was successful
            error_message: Error message if failed
            metadata: Additional metadata
        """
        try:
            with get_db() as db:
                query = Query(
                    query_text=query_text,
                    answer=answer,
                    sources_count=sources_count,
                    response_time_ms=response_time_ms,
                    embedding_time_ms=embedding_time_ms,
                    retrieval_time_ms=retrieval_time_ms,
                    synthesis_time_ms=synthesis_time_ms,
                    success=success,
                    error_message=error_message,
                    extra_metadata=metadata or {}
                )
                db.add(query)
                db.commit()
        except Exception as e:
            logger.error(f"Error logging query: {e}")
    
    def get_query_history(self, limit: int = 50) -> List[Dict]:
        """Get recent query history.
        
        Args:
            limit: Maximum number of queries to return
            
        Returns:
            List of query dictionaries
        """
        try:
            with get_db() as db:
                queries = db.query(Query).order_by(desc(Query.created_at)).limit(limit).all()
                return [
                    {
                        "id": q.id,
                        "query": q.query_text,
                        "answer": q.answer[:200] + "..." if q.answer and len(q.answer) > 200 else q.answer,
                        "sources_count": q.sources_count,
                        "response_time_ms": q.response_time_ms,
                        "success": q.success,
                        "created_at": q.created_at.isoformat() if q.created_at else None
                    }
                    for q in queries
                ]
        except Exception as e:
            logger.error(f"Error getting query history: {e}")
            return []
    
    def get_analytics(self, days: int = 30) -> Dict:
        """Get analytics for the specified time period.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dictionary with analytics data
        """
        try:
            with get_db() as db:
                cutoff_date = datetime.utcnow() - timedelta(days=days)
                
                # Total queries
                total_queries = db.query(Query).filter(Query.created_at >= cutoff_date).count()
                
                # Successful queries
                successful_queries = db.query(Query).filter(
                    Query.created_at >= cutoff_date,
                    Query.success == True
                ).count()
                
                # Average response time
                avg_response_time = db.query(func.avg(Query.response_time_ms)).filter(
                    Query.created_at >= cutoff_date,
                    Query.response_time_ms.isnot(None)
                ).scalar() or 0
                
                # Queries per day (handle SQLite vs PostgreSQL)
                try:
                    # Try PostgreSQL/MySQL date function
                    queries_per_day = db.query(
                        func.date(Query.created_at).label('date'),
                        func.count(Query.id).label('count')
                    ).filter(
                        Query.created_at >= cutoff_date
                    ).group_by(
                        func.date(Query.created_at)
                    ).all()
                except Exception:
                    # Fallback for SQLite - use strftime
                    queries_per_day = db.query(
                        func.strftime('%Y-%m-%d', Query.created_at).label('date'),
                        func.count(Query.id).label('count')
                    ).filter(
                        Query.created_at >= cutoff_date
                    ).group_by(
                        func.strftime('%Y-%m-%d', Query.created_at)
                    ).all()
                
                # Most common queries
                top_queries = db.query(
                    Query.query_text,
                    func.count(Query.id).label('count')
                ).filter(
                    Query.created_at >= cutoff_date
                ).group_by(
                    Query.query_text
                ).order_by(desc('count')).limit(10).all()
                
                # Average sources per query
                avg_sources = db.query(func.avg(Query.sources_count)).filter(
                    Query.created_at >= cutoff_date,
                    Query.sources_count > 0
                ).scalar() or 0
                
                # Time breakdown averages
                avg_embedding_time = db.query(func.avg(Query.embedding_time_ms)).filter(
                    Query.created_at >= cutoff_date,
                    Query.embedding_time_ms.isnot(None)
                ).scalar() or 0
                
                avg_retrieval_time = db.query(func.avg(Query.retrieval_time_ms)).filter(
                    Query.created_at >= cutoff_date,
                    Query.retrieval_time_ms.isnot(None)
                ).scalar() or 0
                
                avg_synthesis_time = db.query(func.avg(Query.synthesis_time_ms)).filter(
                    Query.created_at >= cutoff_date,
                    Query.synthesis_time_ms.isnot(None)
                ).scalar() or 0
                
                return {
                    "total_queries": total_queries,
                    "successful_queries": successful_queries,
                    "failed_queries": total_queries - successful_queries,
                    "success_rate": (successful_queries / total_queries * 100) if total_queries > 0 else 0,
                    "avg_response_time_ms": round(avg_response_time, 2),
                    "avg_embedding_time_ms": round(avg_embedding_time, 2),
                    "avg_retrieval_time_ms": round(avg_retrieval_time, 2),
                    "avg_synthesis_time_ms": round(avg_synthesis_time, 2),
                    "avg_sources_per_query": round(avg_sources, 2),
                    "queries_per_day": [
                        {"date": str(date), "count": count}
                        for date, count in queries_per_day
                    ],
                    "top_queries": [
                        {"query": query, "count": count}
                        for query, count in top_queries
                    ]
                }
        except Exception as e:
            logger.error(f"Error getting analytics: {e}")
            return {}
    
    def register_document(
        self,
        filename: str,
        file_path: str,
        file_size_bytes: int,
        file_type: str,
        pages: Optional[int] = None,
        chunks_count: int = 0,
        vectors_count: int = 0,
        metadata: Optional[Dict] = None
    ) -> int:
        """Register a document in the database.
        
        Args:
            filename: Document filename
            file_path: Path to document file
            file_size_bytes: File size in bytes
            file_type: File type/extension
            pages: Number of pages (for PDFs)
            chunks_count: Number of chunks created
            vectors_count: Number of vectors added
            metadata: Additional metadata
            
        Returns:
            Document ID
        """
        try:
            with get_db() as db:
                doc = Document(
                    filename=filename,
                    file_path=file_path,
                    file_size_bytes=file_size_bytes,
                    file_type=file_type,
                    pages=pages,
                    chunks_count=chunks_count,
                    vectors_count=vectors_count,
                    extra_metadata=metadata or {}
                )
                db.add(doc)
                db.commit()
                db.refresh(doc)
                return doc.id
        except Exception as e:
            logger.error(f"Error registering document: {e}")
            return -1
    
    def get_documents(self) -> List[Dict]:
        """Get all documents.
        
        Returns:
            List of document dictionaries
        """
        try:
            with get_db() as db:
                docs = db.query(Document).order_by(desc(Document.upload_date)).all()
                return [
                    {
                        "id": d.id,
                        "filename": d.filename,
                        "file_size_bytes": d.file_size_bytes,
                        "file_size_mb": round(d.file_size_bytes / (1024 * 1024), 2),
                        "file_type": d.file_type,
                        "pages": d.pages,
                        "chunks_count": d.chunks_count,
                        "vectors_count": d.vectors_count,
                        "upload_date": d.upload_date.isoformat() if d.upload_date else None,
                        "status": d.status,
                        "query_count": d.query_count
                    }
                    for d in docs
                ]
        except Exception as e:
            logger.error(f"Error getting documents: {e}")
            return []
    
    def delete_document(self, document_id: int) -> bool:
        """Delete a document record.
        
        Args:
            document_id: Document ID to delete
            
        Returns:
            True if deleted successfully
        """
        try:
            with get_db() as db:
                doc = db.query(Document).filter(Document.id == document_id).first()
                if doc:
                    db.delete(doc)
                    db.commit()
                    return True
                return False
        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            return False

