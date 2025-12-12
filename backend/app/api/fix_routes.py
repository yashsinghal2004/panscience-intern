"""Routes for fixing data consistency issues."""

import logging
from fastapi import APIRouter, HTTPException
from app.services.vector_store import VectorStoreService
from app.models.database import ChunkMetadata, get_db
from app.api.routes import vector_store_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/fix-metadata-mismatch")
async def fix_metadata_mismatch():
    """Fix the mismatch between FAISS index and database metadata.
    
    WARNING: This will clear the FAISS index and require re-uploading all documents!
    """
    try:
        stats = vector_store_service.get_stats()
        
        if stats['is_synced']:
            return {
                "message": "No mismatch detected. Index and database are in sync.",
                "vectors": stats['total_vectors'],
                "chunks": stats['chunks_count']
            }
        
        logger.warning(
            f"Fixing mismatch: {stats['total_vectors']} vectors in index, "
            f"{stats['chunks_count']} chunks in database"
        )
        
        # Option 1: Clear database to match index (loses metadata but keeps vectors)
        # Option 2: Clear index to match database (loses vectors but keeps metadata)
        # Option 3: Clear both and start fresh (recommended)
        
        # We'll clear both since having orphaned data is worse
        from pathlib import Path
        import shutil
        
        # Backup current state
        backup_dir = vector_store_service.store_path / "backup"
        backup_dir.mkdir(exist_ok=True)
        
        if vector_store_service.index_path.exists():
            backup_path = backup_dir / f"faiss.index.backup.{int(__import__('time').time())}"
            shutil.copy(vector_store_service.index_path, backup_path)
            logger.info(f"Backed up index to {backup_path}")
        
        # Clear database chunks
        with get_db() as db:
            count = db.query(ChunkMetadata).count()
            db.query(ChunkMetadata).delete()
            db.commit()
            logger.info(f"Cleared {count} chunk metadata records from database")
        
        # Delete FAISS index
        if vector_store_service.index_path.exists():
            vector_store_service.index_path.unlink()
            logger.info("Deleted FAISS index")
        
        # Recreate index
        vector_store_service._create_new_index()
        
        return {
            "message": "Mismatch fixed. Both index and database have been cleared. Please re-upload your documents.",
            "old_vectors": stats['total_vectors'],
            "old_chunks": stats['chunks_count'],
            "backup_location": str(backup_dir),
            "action_required": "reupload_all_documents"
        }
        
    except Exception as e:
        logger.error(f"Error fixing metadata mismatch: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fixing mismatch: {str(e)}")


@router.get("/check-sync")
async def check_sync():
    """Check synchronization status between FAISS index and database."""
    try:
        stats = vector_store_service.get_stats()
        
        # Get sample of FAISS IDs to check
        sample_ids = []
        if vector_store_service.index and vector_store_service.index.ntotal > 0:
            # Check first 100 IDs
            sample_ids = list(range(min(100, vector_store_service.index.ntotal)))
        
        missing_count = 0
        found_count = 0
        
        if sample_ids:
            with get_db() as db:
                for faiss_id in sample_ids:
                    exists = db.query(ChunkMetadata).filter(
                        ChunkMetadata.faiss_id == faiss_id
                    ).first()
                    if exists:
                        found_count += 1
                    else:
                        missing_count += 1
        
        return {
            "is_synced": stats['is_synced'],
            "total_vectors": stats['total_vectors'],
            "chunks_in_database": stats['chunks_count'],
            "mismatch": stats['total_vectors'] - stats['chunks_count'],
            "sample_check": {
                "checked_ids": len(sample_ids),
                "found": found_count,
                "missing": missing_count,
                "match_rate": found_count / len(sample_ids) if sample_ids else 0
            },
            "recommendation": (
                "reupload_documents" if not stats['is_synced'] else "system_healthy"
            )
        }
        
    except Exception as e:
        logger.error(f"Error checking sync: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error checking sync: {str(e)}")





