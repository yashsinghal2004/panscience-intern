"""Embedding service using nomic-embed-text-v1."""

import logging
import os
from typing import List, Optional
import numpy as np
from langchain_nomic import NomicEmbeddings
from langchain_core.embeddings import Embeddings

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating embeddings using nomic-embed-text-v1."""
    
    def __init__(self, model_name: Optional[str] = None):
        """Initialize embedding service.
        
        Args:
            model_name: Optional model name override
        """
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self.embeddings: Optional[Embeddings] = None
        self._initialize_embeddings()
    
    def _initialize_embeddings(self) -> None:
        """Initialize the embedding model."""
        try:
            # Set NOMIC_API_KEY environment variable if available in settings
            # NomicEmbeddings reads from NOMIC_API_KEY environment variable
            if settings.NOMIC_API_KEY:
                os.environ["NOMIC_API_KEY"] = settings.NOMIC_API_KEY
                logger.info("NOMIC_API_KEY set from configuration")
            elif not os.environ.get("NOMIC_API_KEY"):
                logger.warning(
                    "NOMIC_API_KEY not found in settings or environment. "
                    "NomicEmbeddings may fail. Please add NOMIC_API_KEY to your .env file."
                )
            
            logger.info(f"Initializing embedding model: {self.model_name}")
            self.embeddings = NomicEmbeddings(model=self.model_name)
            logger.info("Embedding model initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize embedding model: {e}")
            if not settings.NOMIC_API_KEY and not os.environ.get("NOMIC_API_KEY"):
                logger.error(
                    "NOMIC_API_KEY is required. Please add it to your .env file: "
                    "NOMIC_API_KEY=your_api_key_here"
                )
            raise
    
    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text.
        
        Args:
            text: Input text to embed
            
        Returns:
            List of embedding values
        """
        if not self.embeddings:
            raise RuntimeError("Embedding model not initialized")
        
        try:
            embedding = await self.embeddings.aembed_query(text)
            return embedding
        except Exception as e:
            logger.error(f"Error embedding text: {e}")
            raise
    
    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
            
        Raises:
            RuntimeError: If embedding model is not initialized
            Exception: If embedding generation fails
        """
        if not self.embeddings:
            error_msg = (
                "Embedding model not initialized. "
                "Please check your NOMIC_API_KEY configuration."
            )
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        # Verify API key is set
        if not settings.NOMIC_API_KEY and not os.environ.get("NOMIC_API_KEY"):
            error_msg = (
                "NOMIC_API_KEY is required but not set. "
                "Please add NOMIC_API_KEY to your .env file."
            )
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        try:
            logger.info(f"Generating embeddings for {len(texts)} texts...")
            embeddings = await self.embeddings.aembed_documents(texts)
            
            if not embeddings:
                raise ValueError("No embeddings returned from model")
            
            logger.info(f"Successfully generated {len(embeddings)} embeddings")
            return embeddings
            
        except Exception as e:
            error_msg = f"Error embedding documents: {e}"
            logger.error(error_msg)
            
            # Provide helpful error message for common issues
            if "Nomic API token" in str(e) or "nomic login" in str(e).lower():
                error_msg += (
                    "\nPlease ensure NOMIC_API_KEY is set in your .env file: "
                    "NOMIC_API_KEY=your_api_key_here"
                )
            
            raise Exception(error_msg) from e
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings.
        
        Returns:
            Embedding dimension
        """
        return settings.EMBEDDING_DIMENSION


