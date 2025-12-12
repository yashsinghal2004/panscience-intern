"""Document chunking service."""

import logging
from typing import List, Tuple, Dict, Optional
import tiktoken
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from app.core.config import settings

logger = logging.getLogger(__name__)


class ChunkingService:
    """Service for splitting documents into chunks using token-aware splitting."""
    
    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None,
        tokenizer_name: str = None,
    ):
        """Initialize chunking service.
        
        Args:
            chunk_size: Size of each chunk in tokens (default: 600)
            chunk_overlap: Overlap between chunks in tokens (default: 100)
            tokenizer_name: tiktoken encoding name (default: cl100k_base)
        """
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP
        self.tokenizer_name = tokenizer_name or settings.CHUNK_TOKENIZER
        
        # Initialize tokenizer
        try:
            self.tokenizer = tiktoken.get_encoding(self.tokenizer_name)
        except Exception as e:
            logger.warning(f"Failed to load tokenizer {self.tokenizer_name}: {e}. Falling back to cl100k_base")
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        
        # Token-aware text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=self._count_tokens,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        logger.info(
            f"Chunking service initialized: chunk_size={self.chunk_size} tokens, "
            f"chunk_overlap={self.chunk_overlap} tokens, tokenizer={self.tokenizer_name}"
        )
    
    def _count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken.
        
        Args:
            text: Input text
            
        Returns:
            Number of tokens
        """
        try:
            return len(self.tokenizer.encode(text))
        except Exception as e:
            logger.warning(f"Error counting tokens: {e}. Falling back to character count")
            return len(text)
    
    def chunk_text(self, text: str) -> List[str]:
        """Split text into chunks.
        
        Args:
            text: Input text to chunk
            
        Returns:
            List of text chunks (filtered to remove empty/short chunks)
        """
        try:
            chunks = self.text_splitter.split_text(text)
            
            # Filter out empty or very short chunks (less than 10 tokens)
            filtered_chunks = []
            for chunk in chunks:
                token_count = self._count_tokens(chunk)
                if token_count >= 10:  # Minimum 10 tokens
                    filtered_chunks.append(chunk)
                else:
                    logger.debug(f"Filtered out short chunk ({token_count} tokens): {chunk[:50]}...")
            
            logger.info(f"Split text into {len(chunks)} chunks, {len(filtered_chunks)} after filtering")
            return filtered_chunks
        except Exception as e:
            logger.error(f"Error chunking text: {e}")
            raise
    
    def chunk_documents(self, documents: List[str]) -> List[str]:
        """Split multiple documents into chunks.
        
        Args:
            documents: List of document texts
            
        Returns:
            List of all chunks from all documents
        """
        all_chunks = []
        for doc in documents:
            chunks = self.chunk_text(doc)
            all_chunks.extend(chunks)
        return all_chunks
    
    def chunk_documents_with_metadata(
        self, 
        documents: List[Tuple[str, Dict]]
    ) -> List[Tuple[str, Dict]]:
        """Split documents with metadata into chunks, preserving metadata.
        
        Args:
            documents: List of tuples (text, metadata)
            
        Returns:
            List of tuples (chunk_text, metadata)
        """
        all_chunks = []
        for text, metadata in documents:
            # Create Document object for LangChain splitter
            doc = Document(page_content=text, metadata=metadata)
            chunks = self.text_splitter.split_documents([doc])
            
            for chunk in chunks:
                # Preserve original metadata and add chunk info
                chunk_metadata = chunk.metadata.copy()
                # Ensure page number is preserved
                if 'page' in chunk_metadata:
                    chunk_metadata['page_number'] = chunk_metadata['page']
                elif 'page_number' not in chunk_metadata:
                    # Try to extract from source if available
                    source = chunk_metadata.get('source', '')
                    # If source contains page info, extract it
                    pass
                
                all_chunks.append((chunk.page_content, chunk_metadata))
        
        logger.info(f"Split {len(documents)} documents into {len(all_chunks)} chunks with metadata")
        return all_chunks





