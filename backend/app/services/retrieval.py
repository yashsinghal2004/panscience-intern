"""Retrieval service for RAG pipeline."""

import logging
from typing import List, Tuple, Optional
from app.services.vector_store import VectorStoreService
from app.services.reranker import RerankerService

logger = logging.getLogger(__name__)


class RetrievalService:
    """Service for retrieving relevant documents from vector store."""
    
    def __init__(
        self,
        vector_store: Optional[VectorStoreService] = None,
        reranker: Optional[RerankerService] = None,
        use_reranker: bool = True
    ):
        """Initialize retrieval service.
        
        Args:
            vector_store: Vector store service instance
            reranker: Reranker service instance
            use_reranker: Whether to use reranker (default: True)
        """
        self.vector_store = vector_store or VectorStoreService()
        
        # Initialize reranker gracefully - don't fail if API keys are missing
        if reranker is not None:
            self.reranker = reranker
            self.use_reranker = use_reranker
        elif use_reranker:
            try:
                self.reranker = RerankerService()
                self.use_reranker = True
            except (ValueError, Exception) as e:
                logger.warning(f"Reranker initialization failed (missing API keys?): {e}. Continuing without reranker.")
                self.reranker = None
                self.use_reranker = False
        else:
            self.reranker = None
            self.use_reranker = False
            
        logger.info(f"Retrieval service initialized (reranker: {'enabled' if self.use_reranker else 'disabled'})")
    
    async def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        threshold: Optional[float] = None,
        rerank_top_k: Optional[int] = None
    ) -> List[Tuple[str, float, dict]]:
        """Retrieve relevant chunks for a query.
        
        Args:
            query: User query
            top_k: Number of results to retrieve from FAISS (before reranking)
            threshold: Minimum similarity threshold
            rerank_top_k: Number of results to return after reranking (default: same as top_k)
            
        Returns:
            List of tuples (chunk_text, rerank_score, metadata)
        """
        try:
            logger.info(f"Retrieving documents for query: {query[:50]}...")
            
            # Retrieve initial results from FAISS
            # Reduced multiplier to avoid token limits during reranking
            if self.use_reranker and top_k is not None:
                initial_top_k = min(top_k * 2, 30)  # Cap at 30 to avoid token limits
            else:
                initial_top_k = top_k
                
            results = await self.vector_store.search(
                query=query,
                top_k=initial_top_k,
                threshold=threshold
            )
            logger.info(f"Retrieved {len(results)} relevant chunks from FAISS (query: '{query[:50]}...')")
            
            # CRITICAL: If vector store has results but retrieval returns empty, log it
            if len(results) == 0:
                stats = self.vector_store.get_stats()
                logger.error(
                    f"CRITICAL: Vector store search returned 0 results! "
                    f"Index has {stats['total_vectors']} vectors, "
                    f"query='{query[:100]}', threshold={threshold}"
                )
            
            # Rerank results if enabled
            if self.use_reranker and results:
                logger.info(f"Reranking {len(results)} results for improved relevance...")
                try:
                    reranked_results = await self.reranker.rerank(
                        query=query,
                        results=results,
                        top_k=rerank_top_k or top_k
                    )
                    if reranked_results:
                        results = reranked_results
                        logger.info(f"Reranked to {len(results)} top results")
                    else:
                        logger.warning("Reranker returned empty results, using original FAISS results")
                except Exception as e:
                    logger.warning(f"Reranker failed: {e}. Using original FAISS results.")
                    # Continue with original results if reranking fails
            
            return results
        except Exception as e:
            logger.error(f"Error in retrieval: {e}")
            raise
    
    def format_context(self, results: List[Tuple[str, float, dict]]) -> str:
        """Format retrieved chunks into context string.
        
        Args:
            results: List of retrieved chunks with scores
            
        Returns:
            Formatted context string
        """
        if not results:
            logger.error("format_context called with empty results list!")
            return "No relevant context found."
        
        logger.info(f"Formatting context from {len(results)} results")
        
        context_parts = []
        for i, (chunk, score, metadata) in enumerate(results, 1):
            # Validate chunk
            if not chunk or len(chunk.strip()) == 0:
                logger.warning(f"Skipping empty chunk at index {i}")
                continue
            
            # Extract page number from metadata
            page_num = None
            if metadata:
                page_num = metadata.get('page') or metadata.get('page_number') or metadata.get('pageNumber')
                if page_num is not None:
                    try:
                        page_num = int(page_num)
                    except (ValueError, TypeError):
                        page_num = None
            
            page_citation = f" - Page {page_num}" if page_num else ""
            context_parts.append(f"[Context {i}{page_citation} (relevance: {score:.3f})]\n{chunk}\n")
        
        formatted = "\n".join(context_parts)
        logger.info(f"Formatted context: {len(formatted)} chars from {len(context_parts)} chunks")
        
        if len(formatted.strip()) == 0:
            logger.error("Formatted context is empty after processing results!")
            return "No relevant context found."
        
        return formatted





