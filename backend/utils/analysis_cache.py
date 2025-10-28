import os
import json
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class AnalysisCache:
    """Cache system for storing and retrieving LLM analysis responses."""
    
    def __init__(self, cache_dir: str = "temp_cache", cache_duration_hours: int = 24):
        self.cache_dir = Path(cache_dir)
        self.cache_duration = timedelta(hours=cache_duration_hours)
        
        # Create cache directory if it doesn't exist
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Analysis cache initialized at: {self.cache_dir.absolute()}")
    
    def _generate_cache_key(self, content: str, file_info: Dict[str, Any]) -> str:
        """Generate a unique cache key based on file content and metadata."""
        # Create a hash from file content and relevant metadata
        hash_input = f"{content}_{file_info.get('name', '')}_{file_info.get('language', '')}"
        return hashlib.sha256(hash_input.encode()).hexdigest()
    
    def _get_cache_file_path(self, cache_key: str) -> Path:
        """Get the full path for a cache file."""
        return self.cache_dir / f"{cache_key}.json"
    
    def _is_cache_valid(self, cache_file: Path) -> bool:
        """Check if cache file exists and is within the valid duration."""
        if not cache_file.exists():
            return False
        
        # Check file modification time
        file_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
        return datetime.now() - file_time < self.cache_duration
    
    def get_cached_analysis(self, content: str, file_info: Dict[str, Any]) -> Optional[str]:
        """Retrieve cached analysis if available and valid."""
        try:
            cache_key = self._generate_cache_key(content, file_info)
            cache_file = self._get_cache_file_path(cache_key)
            
            if self._is_cache_valid(cache_file):
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                
                logger.info(f"Cache hit for file: {file_info.get('name', 'unknown')}")
                return cache_data.get('analysis_response')
            else:
                # Clean up expired cache file
                if cache_file.exists():
                    cache_file.unlink()
                    logger.info(f"Removed expired cache file: {cache_key}")
                
        except Exception as e:
            logger.error(f"Error reading cache: {str(e)}")
        
        return None
    
    def save_analysis(self, content: str, file_info: Dict[str, Any], analysis_response: str) -> None:
        """Save analysis response to cache."""
        try:
            cache_key = self._generate_cache_key(content, file_info)
            cache_file = self._get_cache_file_path(cache_key)
            
            cache_data = {
                'timestamp': datetime.now().isoformat(),
                'file_info': file_info,
                'content_hash': hashlib.sha256(content.encode()).hexdigest(),
                'analysis_response': analysis_response
            }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Analysis cached for file: {file_info.get('name', 'unknown')}")
            
        except Exception as e:
            logger.error(f"Error saving to cache: {str(e)}")
    
    def clear_cache(self) -> int:
        """Clear all cached files and return count of files removed."""
        removed_count = 0
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
                removed_count += 1
            
            logger.info(f"Cleared {removed_count} cache files")
            
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")
        
        return removed_count
    
    def cleanup_expired_cache(self) -> int:
        """Remove expired cache files and return count of files removed."""
        removed_count = 0
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                if not self._is_cache_valid(cache_file):
                    cache_file.unlink()
                    removed_count += 1
            
            if removed_count > 0:
                logger.info(f"Cleaned up {removed_count} expired cache files")
                
        except Exception as e:
            logger.error(f"Error during cache cleanup: {str(e)}")
        
        return removed_count
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        try:
            cache_files = list(self.cache_dir.glob("*.json"))
            valid_files = [f for f in cache_files if self._is_cache_valid(f)]
            expired_files = [f for f in cache_files if not self._is_cache_valid(f)]
            
            total_size = sum(f.stat().st_size for f in cache_files)
            
            return {
                'total_files': len(cache_files),
                'valid_files': len(valid_files),
                'expired_files': len(expired_files),
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'cache_directory': str(self.cache_dir.absolute())
            }
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {str(e)}")
            return {}
