"""Document ingestion service for loading and processing documents."""

import logging
from pathlib import Path
from typing import List, Optional
import aiofiles
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_core.documents import Document

from app.core.config import settings

logger = logging.getLogger(__name__)


class IngestionService:
    """Service for ingesting documents from various formats."""
    
    def __init__(self, upload_dir: Optional[str] = None):
        """Initialize ingestion service.
        
        Args:
            upload_dir: Directory for uploaded files
        """
        self.upload_dir = Path(upload_dir or settings.UPLOAD_DIR)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Ingestion service initialized with upload_dir: {self.upload_dir}")
    
    async def load_pdf(self, file_path: str) -> List[Document]:
        """Load PDF file and extract text.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            List of Document objects
        """
        try:
            logger.info(f"Loading PDF: {file_path}")
            loader = PyPDFLoader(file_path)
            documents = loader.load()
            logger.info(f"Loaded {len(documents)} pages from PDF")
            return documents
        except Exception as e:
            logger.error(f"Error loading PDF {file_path}: {e}")
            raise
    
    async def load_text(self, file_path: str) -> List[Document]:
        """Load text file.
        
        Args:
            file_path: Path to text file
            
        Returns:
            List of Document objects
        """
        try:
            logger.info(f"Loading text file: {file_path}")
            loader = TextLoader(file_path, encoding='utf-8')
            documents = loader.load()
            logger.info(f"Loaded text file with {len(documents)} documents")
            return documents
        except Exception as e:
            logger.error(f"Error loading text file {file_path}: {e}")
            raise
    
    async def load_file(self, file_path: str) -> List[Document]:
        """Load file based on extension.
        
        Args:
            file_path: Path to file
            
        Returns:
            List of Document objects
        """
        path = Path(file_path)
        extension = path.suffix.lower()
        
        if extension == '.pdf':
            return await self.load_pdf(file_path)
        elif extension in ['.txt', '.md', '.text']:
            return await self.load_text(file_path)
        else:
            raise ValueError(f"Unsupported file type: {extension}")
    
    async def save_uploaded_file(
        self,
        file_content: bytes,
        filename: str
    ) -> str:
        """Save uploaded file to disk.
        
        Args:
            file_content: File content as bytes
            filename: Original filename
            
        Returns:
            Path to saved file
        """
        file_path = self.upload_dir / filename
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(file_content)
        logger.info(f"Saved uploaded file: {file_path}")
        return str(file_path)
    
    def extract_text_from_documents(self, documents: List[Document]) -> List[str]:
        """Extract text content from Document objects.
        
        Args:
            documents: List of Document objects
            
        Returns:
            List of text strings
        """
        return [doc.page_content for doc in documents]
    
    def extract_documents_with_metadata(self, documents: List[Document]) -> List[tuple]:
        """Extract text content and metadata from Document objects.
        
        Args:
            documents: List of Document objects
            
        Returns:
            List of tuples (text, metadata)
        """
        result = []
        for doc in documents:
            # Ensure page number is in metadata
            metadata = doc.metadata.copy() if doc.metadata else {}
            if 'page' not in metadata and 'page_number' not in metadata:
                # Try to infer from source if available
                source = metadata.get('source', '')
                # PyPDFLoader typically includes page in metadata
                pass
            result.append((doc.page_content, metadata))
        return result





