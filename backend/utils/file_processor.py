import os
import mimetypes
from typing import List, Dict, Optional
from fastapi import UploadFile
import logging

from models.schemas import RepositoryInfo, FileInfo

logger = logging.getLogger(__name__)

class FileProcessor:
    """Handles file processing, validation, and metadata extraction."""
    
    def __init__(self):
        self.supported_extensions = {
            # Programming languages
            '.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.cpp', '.c', '.cs', '.php',
            '.rb', '.go', '.rs', '.swift', '.kt', '.scala', '.clj', '.hs', '.ml',
            '.r', '.m', '.pl', '.sh', '.ps1', '.bat',
            # Legacy languages
            '.cob', '.cbl', '.cobol', '.for', '.f90', '.f95', '.pas', '.ada',
            # Web technologies
            '.html', '.htm', '.css', '.scss', '.sass', '.less',
            # Data and config
            '.json', '.xml', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf',
            # Documentation
            '.md', '.rst', '.txt', '.sql'
        }
        
        self.binary_extensions = {
            '.exe', '.dll', '.so', '.dylib', '.bin', '.obj', '.o', '.a', '.lib',
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico', '.svg', '.pdf',
            '.zip', '.tar', '.gz', '.rar', '.7z', '.jar', '.war'
        }
        
        self.ignore_patterns = {
            'node_modules', '.git', '.svn', '.hg', '__pycache__', '.pytest_cache',
            'venv', 'env', '.env', 'dist', 'build', 'target', 'bin', 'obj',
            '.idea', '.vscode', '.vs', 'coverage', '.nyc_output'
        }
    
    async def process_uploaded_files(self, files: List[UploadFile]) -> List[Dict]:
        """Process uploaded files and extract relevant information."""
        processed_files = []
        
        for file in files:
            try:
                # Skip if file should be ignored
                if self._should_ignore_file(file.filename):
                    continue
                
                # Read file content
                content = await file.read()
                
                # Skip binary files
                if self._is_binary_file(file.filename, content):
                    continue
                
                # Decode content
                try:
                    text_content = content.decode('utf-8')
                except UnicodeDecodeError:
                    try:
                        text_content = content.decode('latin-1')
                    except UnicodeDecodeError:
                        logger.warning(f"Could not decode file: {file.filename}")
                        continue
                
                # Extract file information
                file_info = {
                    'name': os.path.basename(file.filename),
                    'path': file.filename,
                    'content': text_content,
                    'size': len(content),
                    'language': self._detect_language(file.filename),
                    'lines': len(text_content.splitlines()),
                    'extension': os.path.splitext(file.filename)[1].lower()
                }
                
                processed_files.append(file_info)
                
            except Exception as e:
                logger.error(f"Error processing file {file.filename}: {str(e)}")
                continue
        
        logger.info(f"Processed {len(processed_files)} files out of {len(files)} uploaded")
        return processed_files
    
    def create_repository_info(self, processed_files: List[Dict], project_name: Optional[str] = None) -> RepositoryInfo:
        """Create repository information from processed files."""
        if not processed_files:
            raise ValueError("No processed files available")
        
        # Calculate statistics
        total_files = len(processed_files)
        total_lines = sum(file['lines'] for file in processed_files)
        total_size = sum(file['size'] for file in processed_files)
        
        # Detect languages
        language_counts = {}
        for file in processed_files:
            lang = file['language']
            language_counts[lang] = language_counts.get(lang, 0) + file['lines']
        
        # Sort languages by line count
        sorted_languages = sorted(language_counts.items(), key=lambda x: x[1], reverse=True)
        primary_language = sorted_languages[0][0] if sorted_languages else 'unknown'
        languages = [lang for lang, _ in sorted_languages]
        
        # Determine project name
        if not project_name:
            # Try to extract from first file path
            if processed_files:
                first_path = processed_files[0]['path']
                project_name = first_path.split('/')[0] if '/' in first_path else 'Unknown Project'
        
        return RepositoryInfo(
            name=project_name,
            total_files=total_files,
            total_lines=total_lines,
            total_size=total_size,
            primary_language=primary_language,
            languages=languages
        )
    
    def _should_ignore_file(self, filename: str) -> bool:
        """Check if file should be ignored based on patterns."""
        path_parts = filename.split('/')
        
        # Check if any part of the path matches ignore patterns
        for part in path_parts:
            if part in self.ignore_patterns:
                return True
        
        # Check file extension
        ext = os.path.splitext(filename)[1].lower()
        if ext in self.binary_extensions:
            return True
        
        return False
    
    def _is_binary_file(self, filename: str, content: bytes) -> bool:
        """Check if file is binary."""
        # Check extension first
        ext = os.path.splitext(filename)[1].lower()
        if ext in self.binary_extensions:
            return True
        
        # Check for null bytes (common in binary files)
        if b'\x00' in content[:1024]:  # Check first 1KB
            return True
        
        return False
    
    def _detect_language(self, filename: str) -> str:
        """Detect programming language from filename."""
        ext = os.path.splitext(filename)[1].lower()
        
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.cs': 'csharp',
            '.php': 'php',
            '.rb': 'ruby',
            '.go': 'go',
            '.rs': 'rust',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.scala': 'scala',
            '.clj': 'clojure',
            '.hs': 'haskell',
            '.ml': 'ocaml',
            '.r': 'r',
            '.m': 'matlab',
            '.pl': 'perl',
            '.sh': 'shell',
            '.ps1': 'powershell',
            '.bat': 'batch',
            '.cob': 'cobol',
            '.cbl': 'cobol',
            '.cobol': 'cobol',
            '.for': 'fortran',
            '.f90': 'fortran',
            '.f95': 'fortran',
            '.pas': 'pascal',
            '.ada': 'ada',
            '.html': 'html',
            '.htm': 'html',
            '.css': 'css',
            '.scss': 'scss',
            '.sass': 'sass',
            '.less': 'less',
            '.json': 'json',
            '.xml': 'xml',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.toml': 'toml',
            '.ini': 'ini',
            '.cfg': 'config',
            '.conf': 'config',
            '.md': 'markdown',
            '.rst': 'restructuredtext',
            '.txt': 'text',
            '.sql': 'sql'
        }
        
        return language_map.get(ext, 'unknown')
