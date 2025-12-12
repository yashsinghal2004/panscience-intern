"""Migration routes for fixing index compatibility issues."""

import logging
from fastapi import APIRouter, HTTPException
from pathlib import Path
import shutil
from app.services.vector_store import VectorStoreService
from app.models.database import ChunkMetadata, get_db

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/migrate-index")
async def migrate_index_to_cosine():
    """Migrate existing L2 index to cosine similarity (IndexFlatIP).
    
    WARNING: This will delete the old index and require re-uploading documents!
    """
    try:
        vector_store = VectorStoreService()
        
        # Check current index type
        if vector_store.index is None:
            return {"message": "No index exists", "action": "none"}
        
        index_type = type(vector_store.index).__name__
        
        if "IndexFlatIP" in index_type or "IP" in index_type:
            return {
                "message": "Index is already using cosine similarity (IndexFlatIP)",
                "index_type": index_type,
                "action": "none"
            }
        
        if "L2" in index_type:
            # Backup old index
            backup_path = vector_store.index_path.with_suffix('.index.backup')
            if vector_store.index_path.exists():
                shutil.copy(vector_store.index_path, backup_path)
                logger.info(f"Backed up old index to {backup_path}")
            
            # Clear database chunks (they need to be re-indexed)
            with get_db() as db:
                count = db.query(ChunkMetadata).count()
                db.query(ChunkMetadata).delete()
                db.commit()
                logger.info(f"Cleared {count} chunk metadata records from database")
            
            # Delete old index
            vector_store.index_path.unlink()
            logger.info("Deleted old L2 index")
            
            # Create new index
            vector_store._create_new_index()
            
            return {
                "message": "Index migrated successfully. Please re-upload your documents.",
                "old_index_type": index_type,
                "new_index_type": "IndexFlatIP",
                "backup_location": str(backup_path),
                "action": "reupload_required"
            }
        
        return {
            "message": f"Unknown index type: {index_type}",
            "index_type": index_type,
            "action": "unknown"
        }
        
    except Exception as e:
        logger.error(f"Error migrating index: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error migrating index: {str(e)}")





