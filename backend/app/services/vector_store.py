"""Vector store service using FAISS for similarity search."""

import logging
import os
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
import numpy as np
import faiss

from app.services.embedder import EmbeddingService
from app.core.config import settings
from app.models.database import ChunkMetadata, get_db

logger = logging.getLogger(__name__)


class VectorStoreService:
    """Service for managing vector store using FAISS."""
    
    def __init__(self, store_path: Optional[str] = None):
        """Initialize vector store service.
        
        Args:
            store_path: Path to store FAISS index (default: from settings)
        """
        self.store_path = Path(store_path or settings.VECTOR_STORE_DIR)
        self.store_path.mkdir(parents=True, exist_ok=True)
        
        self.index_path = self.store_path / settings.VECTOR_STORE_INDEX_NAME
        self.index: Optional[faiss.Index] = None
        self.embedding_service = EmbeddingService()
        self.embedding_dim = settings.EMBEDDING_DIMENSION
        
        # Track chunks in memory (for stats)
        self._chunks: List[str] = []
        self._metadata_list: List[Dict[str, Any]] = []
        
        # Load or create index
        self._load_or_create_index()
        logger.info(f"Vector store initialized at {self.store_path}")
    
    def _load_or_create_index(self) -> None:
        """Load existing FAISS index or create a new one."""
        if self.index_path.exists():
            try:
                logger.info(f"Loading existing FAISS index from {self.index_path}")
                self.index = faiss.read_index(str(self.index_path))
                
                # Load chunks and metadata from database
                self._load_metadata_from_db()
                
                logger.info(f"Loaded index with {self.index.ntotal} vectors")
            except Exception as e:
                logger.warning(f"Failed to load existing index: {e}. Creating new index.")
                self._create_new_index()
        else:
            logger.info("No existing index found. Creating new FAISS index.")
            self._create_new_index()
    
    def _create_new_index(self) -> None:
        """Create a new FAISS index."""
        # Create L2 (Euclidean) distance index
        # For cosine similarity, we normalize vectors
        self.index = faiss.IndexFlatL2(self.embedding_dim)
        self._chunks = []
        self._metadata_list = []
        logger.info(f"Created new FAISS index with dimension {self.embedding_dim}")
    
    def _load_metadata_from_db(self) -> None:
        """Load chunk metadata from database."""
        try:
            with get_db() as db:
                metadata_records = db.query(ChunkMetadata).all()
                self._chunks = [record.chunk_text for record in metadata_records]
                self._metadata_list = [
                    record.extra_metadata or {} 
                    for record in metadata_records
                ]
            logger.info(f"Loaded {len(self._chunks)} chunks from database")
        except Exception as e:
            logger.warning(f"Failed to load metadata from database: {e}")
            self._chunks = []
            self._metadata_list = []
    
    async def add_documents(
        self, 
        chunks: List[str], 
        metadata: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        """Add documents to the vector store.
        
        Args:
            chunks: List of text chunks to add
            metadata: Optional list of metadata dicts (one per chunk)
        """
        if not chunks:
            logger.warning("No chunks provided to add_documents")
            return
        
        if metadata is None:
            metadata = [{}] * len(chunks)
        
        if len(metadata) != len(chunks):
            logger.warning(
                f"Metadata count ({len(metadata)}) doesn't match chunks count ({len(chunks)}). "
                "Using empty metadata for missing entries."
            )
            metadata = metadata + [{}] * (len(chunks) - len(metadata))
        
        try:
            logger.info(f"Generating embeddings for {len(chunks)} chunks...")
            embeddings = await self.embedding_service.embed_documents(chunks)
            
            if not embeddings:
                raise ValueError("No embeddings generated")
            
            if len(embeddings) != len(chunks):
                raise ValueError(
                    f"Embedding count ({len(embeddings)}) doesn't match chunk count ({len(chunks)})"
                )
            
            # Convert to numpy array and normalize for cosine similarity
            embeddings_array = np.array(embeddings, dtype=np.float32)
            faiss.normalize_L2(embeddings_array)
            
            # Add to FAISS index
            logger.info(f"Adding {len(embeddings)} embeddings to FAISS index...")
            self.index.add(embeddings_array)
            
            # Store chunks and metadata
            start_id = len(self._chunks)
            self._chunks.extend(chunks)
            self._metadata_list.extend(metadata)
            
            # Save metadata to database
            self._save_metadata_to_db(chunks, metadata, start_id)
            
            # Save index to disk
            self._save_index()
            
            logger.info(
                f"Successfully added {len(chunks)} chunks. "
                f"Total vectors in index: {self.index.ntotal}"
            )
            
        except Exception as e:
            logger.error(f"Error adding documents to vector store: {e}", exc_info=True)
            raise
    
    def _save_metadata_to_db(
        self, 
        chunks: List[str], 
        metadata: List[Dict[str, Any]], 
        start_id: int
    ) -> None:
        """Save chunk metadata to database.
        
        Args:
            chunks: List of chunks
            metadata: List of metadata dicts
            start_id: Starting FAISS index ID
        """
        try:
            with get_db() as db:
                for i, (chunk, meta) in enumerate(zip(chunks, metadata)):
                    faiss_id = start_id + i
                    chunk_metadata = ChunkMetadata(
                        faiss_id=faiss_id,
                        chunk_text=chunk,
                        extra_metadata=meta
                    )
                    db.add(chunk_metadata)
                db.commit()
            logger.info(f"Saved {len(chunks)} metadata records to database")
        except Exception as e:
            logger.warning(f"Failed to save metadata to database: {e}")
    
    def _save_index(self) -> None:
        """Save FAISS index to disk."""
        try:
            faiss.write_index(self.index, str(self.index_path))
            logger.debug(f"Saved FAISS index to {self.index_path}")
        except Exception as e:
            logger.error(f"Failed to save FAISS index: {e}")
    
    async def search(
        self,
        query: str,
        top_k: Optional[int] = None,
        threshold: Optional[float] = None
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """Search for similar documents.
        
        Args:
            query: Query text
            top_k: Number of results to return
            threshold: Minimum similarity threshold (0.0 to 1.0)
            
        Returns:
            List of tuples (chunk_text, similarity_score, metadata)
        """
        if self.index is None or self.index.ntotal == 0:
            logger.warning("Vector store is empty. Cannot search.")
            return []
        
        top_k = top_k or settings.TOP_K_RESULTS
        threshold = threshold if threshold is not None else settings.SIMILARITY_THRESHOLD
        
        try:
            # Generate query embedding
            query_embedding = await self.embedding_service.embed_text(query)
            query_vector = np.array([query_embedding], dtype=np.float32)
            faiss.normalize_L2(query_vector)
            
            # Search in FAISS
            k = min(top_k, self.index.ntotal)
            distances, indices = self.index.search(query_vector, k)
            
            # Convert distances to similarity scores (1 - normalized distance)
            # For L2 distance on normalized vectors: similarity = 1 - (distance / 2)
            similarities = 1 - (distances[0] / 2.0)
            
            # Filter by threshold and format results
            results = []
            for i, (idx, sim) in enumerate(zip(indices[0], similarities)):
                if sim >= threshold and idx < len(self._chunks):
                    chunk_text = self._chunks[idx]
                    metadata = self._metadata_list[idx] if idx < len(self._metadata_list) else {}
                    results.append((chunk_text, float(sim), metadata))
            
            logger.info(
                f"Search returned {len(results)} results "
                f"(query: '{query[:50]}...', threshold: {threshold})"
            )
            return results
            
        except Exception as e:
            logger.error(f"Error searching vector store: {e}", exc_info=True)
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get vector store statistics.
        
        Returns:
            Dictionary with stats
        """
        total_vectors = self.index.ntotal if self.index else 0
        chunks_count = len(self._chunks)
        
        return {
            "total_vectors": total_vectors,
            "chunks_count": chunks_count,
            "is_synced": total_vectors == chunks_count,
            "index_path": str(self.index_path),
            "index_exists": self.index_path.exists()
        }
