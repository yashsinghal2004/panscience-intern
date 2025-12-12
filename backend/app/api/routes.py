"""FastAPI routes for RAG application."""

import logging
import time
from fastapi import APIRouter, HTTPException, UploadFile, File
from app.api.models import (
    QueryRequest,
    QueryResponse,
    IngestRequest,
    IngestResponse,
    HealthResponse,
)
from app.services.ingestion import IngestionService
from app.services.chunker import ChunkingService
from app.services.vector_store import VectorStoreService
from app.services.retrieval import RetrievalService
from app.services.synthesis import SynthesisService
from app.services.analytics import AnalyticsService
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize services (in production, use dependency injection)
ingestion_service = IngestionService()
chunking_service = ChunkingService()
vector_store_service = VectorStoreService()
retrieval_service = RetrievalService(vector_store_service)
synthesis_service = SynthesisService()
analytics_service = AnalyticsService()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    try:
        stats = vector_store_service.get_stats()
        
        # Add diagnostic information
        status = "healthy"
        if stats['total_vectors'] == 0 and stats['chunks_count'] > 0:
            status = "warning - chunks exist but no vectors in index"
        elif stats['total_vectors'] == 0:
            status = "empty - no documents ingested"
        
        return HealthResponse(
            status=status,
            vector_store_stats=stats
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset-vector-store")
async def reset_vector_store():
    """Reset/clear the vector store (for debugging)."""
    try:
        import shutil
        import os
        
        # Clear the vector store directory
        store_path = vector_store_service.store_path
        if store_path.exists():
            for file in store_path.iterdir():
                if file.is_file():
                    file.unlink()
                    logger.info(f"Deleted {file}")
        
        # Reset in-memory state
        vector_store_service.index = None
        vector_store_service._create_new_index()
        
        # Clear database metadata
        try:
            from app.models.database import ChunkMetadata, get_db
            with get_db() as db:
                db.query(ChunkMetadata).delete()
                db.commit()
            logger.info("Cleared chunk metadata from database")
        except Exception as e:
            logger.warning(f"Failed to clear database metadata: {e}")
        
        logger.info("Vector store reset successfully")
        return {
            "message": "Vector store reset successfully",
            "stats": vector_store_service.get_stats()
        }
    except Exception as e:
        logger.error(f"Error resetting vector store: {e}")
        raise HTTPException(status_code=500, detail=f"Error resetting vector store: {str(e)}")


@router.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """Query documents using RAG pipeline.
    
    Args:
        request: Query request with question
        
    Returns:
        Answer with sources
    """
    start_time = time.time()
    embedding_time = 0
    retrieval_time = 0
    synthesis_time = 0
    success = False
    answer = None
    sources = []
    error_message = None
    
    try:
        logger.info(f"Processing query: {request.query}")
        
        # Check vector store status before querying
        stats = vector_store_service.get_stats()
        logger.info(f"Vector store stats: {stats}")
        
        if stats['total_vectors'] == 0:
            logger.warning("Vector store is empty - no documents have been successfully embedded")
            answer = (
                f"⚠️ The vector store is empty (0 vectors). "
                f"Although {stats.get('chunks_count', 0)} chunks exist in memory, "
                f"no embeddings were successfully added to the search index. "
                f"Please re-upload your documents. "
                f"If this persists, check your NOMIC_API_KEY configuration and server logs."
            )
            response = QueryResponse(
                answer=answer,
                sources=[],
                query=request.query
            )
            # Log failed query
            total_time = (time.time() - start_time) * 1000
            analytics_service.log_query(
                query_text=request.query,
                answer=answer,
                sources_count=0,
                response_time_ms=total_time,
                success=False,
                error_message="Vector store empty"
            )
            return response
        
        # Retrieve relevant chunks (track retrieval time)
        retrieval_start = time.time()
        results = await retrieval_service.retrieve(
            query=request.query,
            top_k=request.top_k,
            threshold=request.threshold
        )
        retrieval_time = (time.time() - retrieval_start) * 1000
        
        if not results:
            # Try with very low threshold and more results
            logger.info(f"No results with threshold {request.threshold or settings.SIMILARITY_THRESHOLD}, trying with minimal threshold")
            retrieval_start = time.time()
            results = await retrieval_service.retrieve(
                query=request.query,
                top_k=(request.top_k or settings.TOP_K_RESULTS) * 2,  # Get more candidates
                threshold=0.0  # Accept any similarity (let reranker/synthesis filter)
            )
            retrieval_time = (time.time() - retrieval_start) * 1000
            
            if not results:
                answer = (
                    f"⚠️ No relevant documents found for your query. "
                    f"The vector store has {stats['total_vectors']} vectors, "
                    f"but none matched your question. Try rephrasing your question or checking if the document contains relevant information."
                )
                response = QueryResponse(
                    answer=answer,
                    sources=[],
                    query=request.query
                )
                # Log query with no results
                total_time = (time.time() - start_time) * 1000
                analytics_service.log_query(
                    query_text=request.query,
                    answer=answer,
                    sources_count=0,
                    response_time_ms=total_time,
                    retrieval_time_ms=retrieval_time,
                    success=True  # Query succeeded, just no results
                )
                return response
        
        # Format context
        logger.info(f"Formatting context from {len(results)} results")
        context = retrieval_service.format_context(results)
        
        if not context or len(context.strip()) == 0:
            logger.error("Context is empty after formatting! Results were: " + str([(len(chunk), score) for chunk, score, _ in results]))
            answer = (
                f"⚠️ Retrieved {len(results)} results but could not format context. "
                f"This may indicate an issue with the retrieved chunks. Please check server logs."
            )
        else:
            # Synthesize answer (track synthesis time)
            logger.info(f"Synthesizing answer with context length: {len(context)} chars")
            synthesis_start = time.time()
            try:
                answer = await synthesis_service.synthesize(
                    question=request.query,
                    context=context
                )
                synthesis_time = (time.time() - synthesis_start) * 1000
            except Exception as e:
                logger.error(f"Synthesis failed: {e}", exc_info=True)
                synthesis_time = (time.time() - synthesis_start) * 1000
                answer = (
                    f"⚠️ Error generating answer: {str(e)}. "
                    f"However, {len(results)} relevant chunks were found. "
                    f"Please check server logs for details."
                )
        
        # Format sources
        sources = [
            {
                "chunk": chunk[:200] + "..." if len(chunk) > 200 else chunk,
                "similarity": score,
                "metadata": metadata
            }
            for chunk, score, metadata in results
        ]
        
        success = True
        total_time = (time.time() - start_time) * 1000
        
        # Log successful query
        analytics_service.log_query(
            query_text=request.query,
            answer=answer,
            sources_count=len(sources),
            response_time_ms=total_time,
            retrieval_time_ms=retrieval_time,
            synthesis_time_ms=synthesis_time,
            success=True
        )
        
        return QueryResponse(
            answer=answer,
            sources=sources,
            query=request.query
        )
        
    except Exception as e:
        error_message = str(e)
        logger.error(f"Error processing query: {e}")
        total_time = (time.time() - start_time) * 1000
        
        # Log failed query
        analytics_service.log_query(
            query_text=request.query,
            answer=None,
            sources_count=0,
            response_time_ms=total_time,
            embedding_time_ms=embedding_time,
            retrieval_time_ms=retrieval_time,
            synthesis_time_ms=synthesis_time,
            success=False,
            error_message=error_message
        )
        
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")


@router.post("/ingest", response_model=IngestResponse)
async def ingest_documents(request: IngestRequest):
    """Ingest documents into the vector store.
    
    Args:
        request: Ingest request with file path or text
        
    Returns:
        Status message with chunk counts
    """
    try:
        if request.file_path:
            # Load from file
            logger.info(f"Ingesting file: {request.file_path}")
            documents = await ingestion_service.load_file(request.file_path)
            # Extract documents with metadata
            documents_with_metadata = ingestion_service.extract_documents_with_metadata(documents)
            
            # Add filename to all metadata (create copy to avoid mutation)
            from pathlib import Path
            file_path_obj = Path(request.file_path)
            filename = file_path_obj.name
            updated_documents = []
            for text, metadata in documents_with_metadata:
                # Create a copy of metadata to avoid mutating original
                metadata_copy = metadata.copy() if metadata else {}
                metadata_copy['filename'] = filename
                metadata_copy['source'] = filename  # Also add to source for compatibility
                updated_documents.append((text, metadata_copy))
            documents_with_metadata = updated_documents
            
            # Chunk documents with metadata preservation
            chunks_with_metadata = chunking_service.chunk_documents_with_metadata(documents_with_metadata)
            chunks = [chunk for chunk, _ in chunks_with_metadata]
            metadata_list = [metadata for _, metadata in chunks_with_metadata]
        elif request.text:
            # Use direct text
            logger.info("Ingesting direct text")
            chunks = chunking_service.chunk_documents([request.text])
            metadata_list = [{}] * len(chunks)
        else:
            raise HTTPException(
                status_code=400,
                detail="Either 'file_path' or 'text' must be provided"
            )
        
        if not chunks:
            raise HTTPException(
                status_code=400,
                detail="No chunks generated from input"
            )
        
        # Add to vector store with metadata
        try:
            await vector_store_service.add_documents(chunks, metadata=metadata_list)
        except Exception as e:
            logger.error(f"Failed to add documents to vector store: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate embeddings and add to vector store: {str(e)}. "
                       f"Please check your NOMIC_API_KEY configuration."
            )
        
        stats = vector_store_service.get_stats()
        
        # Verify that vectors were actually added
        if stats['total_vectors'] == 0:
            logger.error("No vectors were added to the index despite successful chunking")
            raise HTTPException(
                status_code=500,
                detail="Document was chunked but embeddings failed. "
                       "Please check your NOMIC_API_KEY and try again."
            )
        
        return IngestResponse(
            message="Documents ingested successfully",
            chunks_added=len(chunks),
            total_chunks=stats['total_vectors']  # Use total_vectors instead of chunks_count
        )
        
    except Exception as e:
        logger.error(f"Error ingesting documents: {e}")
        raise HTTPException(status_code=500, detail=f"Error ingesting documents: {str(e)}")


@router.post("/ingest/upload", response_model=IngestResponse)
async def upload_and_ingest(file: UploadFile = File(...)):
    """Upload and ingest a file.
    
    Args:
        file: Uploaded file
        
    Returns:
        Status message with chunk counts
    """
    try:
        # Check file size
        file_content = await file.read()
        file_size_mb = len(file_content) / (1024 * 1024)
        
        if file_size_mb > settings.MAX_FILE_SIZE_MB:
            raise HTTPException(
                status_code=400,
                detail=f"File size ({file_size_mb:.2f} MB) exceeds maximum ({settings.MAX_FILE_SIZE_MB} MB)"
            )
        
        # Save file
        file_path = await ingestion_service.save_uploaded_file(
            file_content=file_content,
            filename=file.filename
        )
        
        # Load and process
        documents = await ingestion_service.load_file(file_path)
        # Extract documents with metadata
        documents_with_metadata = ingestion_service.extract_documents_with_metadata(documents)
        
        # Add filename to all metadata (create copy to avoid mutation)
        filename = file.filename or "unknown"
        updated_documents = []
        for text, metadata in documents_with_metadata:
            # Create a copy of metadata to avoid mutating original
            metadata_copy = metadata.copy() if metadata else {}
            metadata_copy['filename'] = filename
            metadata_copy['source'] = filename  # Also add to source for compatibility
            updated_documents.append((text, metadata_copy))
        documents_with_metadata = updated_documents
        
        # Chunk documents with metadata preservation
        chunks_with_metadata = chunking_service.chunk_documents_with_metadata(documents_with_metadata)
        chunks = [chunk for chunk, _ in chunks_with_metadata]
        metadata_list = [metadata for _, metadata in chunks_with_metadata]
        
        if not chunks:
            raise HTTPException(
                status_code=400,
                detail="No chunks generated from file"
            )
        
        # Add to vector store with metadata
        try:
            await vector_store_service.add_documents(chunks, metadata=metadata_list)
        except Exception as e:
            logger.error(f"Failed to add documents to vector store: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate embeddings and add to vector store: {str(e)}. "
                       f"Please check your NOMIC_API_KEY configuration."
            )
        
        stats = vector_store_service.get_stats()
        
        # Verify that vectors were actually added
        if stats['total_vectors'] == 0:
            logger.error("No vectors were added to the index despite successful chunking")
            raise HTTPException(
                status_code=500,
                detail="Document was chunked but embeddings failed. "
                       "Please check your NOMIC_API_KEY and try again."
            )
        
        # Register document in database
        from pathlib import Path
        file_path_obj = Path(file_path)
        pages = len(documents) if documents else None
        doc_id = analytics_service.register_document(
            filename=file.filename or "unknown",
            file_path=file_path,
            file_size_bytes=len(file_content),
            file_type=file_path_obj.suffix.lower() or "unknown",
            pages=pages,
            chunks_count=len(chunks),
            vectors_count=stats['total_vectors']
        )
        
        return IngestResponse(
            message=f"File '{file.filename}' ingested successfully",
            chunks_added=len(chunks),
            total_chunks=stats['total_vectors']  # Use total_vectors instead of chunks_count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading and ingesting file: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")



