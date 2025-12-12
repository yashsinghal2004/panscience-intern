"""Diagnostic routes for debugging the RAG pipeline."""

import logging
from fastapi import APIRouter, HTTPException
from app.services.vector_store import VectorStoreService
from app.services.retrieval import RetrievalService
from app.services.embedder import EmbeddingService
from app.api.routes import vector_store_service, retrieval_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/diagnostic/search-test")
async def test_search(query: str = "test"):
    """Test the search pipeline end-to-end."""
    try:
        # Test 1: Check vector store
        stats = vector_store_service.get_stats()
        logger.info(f"Vector store stats: {stats}")
        
        if stats['total_vectors'] == 0:
            return {
                "error": "No vectors in index",
                "stats": stats,
                "steps": []
            }
        
        # Test 2: Generate query embedding
        embedding_service = EmbeddingService()
        query_embedding = await embedding_service.embed_text(query)
        logger.info(f"Query embedding generated: {len(query_embedding)} dimensions")
        
        # Test 3: Search
        results = await vector_store_service.search(
            query=query,
            top_k=5,
            threshold=0.0  # No threshold filtering
        )
        logger.info(f"Search returned {len(results)} results")
        
        # Test 4: Retrieval service
        retrieval_results = await retrieval_service.retrieve(
            query=query,
            top_k=5,
            threshold=0.0
        )
        logger.info(f"Retrieval service returned {len(retrieval_results)} results")
        
        return {
            "success": True,
            "stats": stats,
            "query": query,
            "embedding_dimension": len(query_embedding),
            "vector_store_results": len(results),
            "retrieval_service_results": len(retrieval_results),
            "sample_results": [
                {
                    "chunk_preview": chunk[:100] + "..." if len(chunk) > 100 else chunk,
                    "similarity": score,
                    "has_metadata": bool(metadata)
                }
                for chunk, score, metadata in results[:3]
            ] if results else [],
            "retrieval_sample": [
                {
                    "chunk_preview": chunk[:100] + "..." if len(chunk) > 100 else chunk,
                    "score": score,
                    "has_metadata": bool(metadata)
                }
                for chunk, score, metadata in retrieval_results[:3]
            ] if retrieval_results else []
        }
    except Exception as e:
        logger.error(f"Diagnostic test failed: {e}", exc_info=True)
        return {
            "error": str(e),
            "error_type": type(e).__name__
        }






