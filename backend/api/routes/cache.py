from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Any
import logging

from utils.analysis_cache import AnalysisCache

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize cache instance
analysis_cache = AnalysisCache(cache_dir="temp_cache/cobol_analysis")

@router.get("/cache/stats")
async def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics."""
    try:
        stats = analysis_cache.get_cache_stats()
        return {
            "status": "success",
            "cache_stats": stats
        }
    except Exception as e:
        logger.error(f"Error getting cache stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get cache stats: {str(e)}")

@router.post("/cache/cleanup")
async def cleanup_expired_cache() -> Dict[str, Any]:
    """Clean up expired cache files."""
    try:
        removed_count = analysis_cache.cleanup_expired_cache()
        return {
            "status": "success",
            "message": f"Cleaned up {removed_count} expired cache files",
            "removed_files": removed_count
        }
    except Exception as e:
        logger.error(f"Error cleaning up cache: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to cleanup cache: {str(e)}")

@router.delete("/cache/clear")
async def clear_all_cache() -> Dict[str, Any]:
    """Clear all cached files."""
    try:
        removed_count = analysis_cache.clear_cache()
        return {
            "status": "success",
            "message": f"Cleared {removed_count} cache files",
            "removed_files": removed_count
        }
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")
