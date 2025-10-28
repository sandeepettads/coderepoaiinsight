import re
import tiktoken
from typing import List, Dict, Tuple
import logging

logger = logging.getLogger(__name__)

class CodeChunker:
    """Handles intelligent code chunking for large files and repositories."""
    
    def __init__(self, max_tokens: int = 100000):
        self.max_tokens = max_tokens
        self.encoding = tiktoken.encoding_for_model("gpt-4")
        
        # Language-specific patterns for function/class detection
        self.function_patterns = {
            'python': [
                r'^def\s+\w+\s*\(',
                r'^class\s+\w+\s*[\(:]',
                r'^async\s+def\s+\w+\s*\('
            ],
            'javascript': [
                r'function\s+\w+\s*\(',
                r'const\s+\w+\s*=\s*\(',
                r'class\s+\w+\s*{',
                r'\w+\s*:\s*function\s*\(',
                r'^\s*\w+\s*\([^)]*\)\s*=>\s*{'
            ],
            'typescript': [
                r'function\s+\w+\s*\(',
                r'const\s+\w+\s*=\s*\(',
                r'class\s+\w+\s*{',
                r'interface\s+\w+\s*{',
                r'type\s+\w+\s*='
            ],
            'java': [
                r'public\s+class\s+\w+',
                r'private\s+class\s+\w+',
                r'protected\s+class\s+\w+',
                r'public\s+\w+\s+\w+\s*\(',
                r'private\s+\w+\s+\w+\s*\(',
                r'protected\s+\w+\s+\w+\s*\('
            ],
            'cobol': [
                r'^\s*\d+\s+PROCEDURE\s+DIVISION',
                r'^\s*\d+\s+WORKING-STORAGE\s+SECTION',
                r'^\s*\d+\s+DATA\s+DIVISION',
                r'^\s*\d+\s+IDENTIFICATION\s+DIVISION',
                r'^\s*\d+\s+\w+-SECTION',
                r'^\s*\d+\s+\w+\s+SECTION'
            ],
            'cpp': [
                r'class\s+\w+\s*{',
                r'struct\s+\w+\s*{',
                r'\w+::\w+\s*\(',
                r'^\w+\s+\w+\s*\('
            ],
            'c': [
                r'^\w+\s+\w+\s*\(',
                r'struct\s+\w+\s*{',
                r'typedef\s+struct\s*{'
            ]
        }
    
    def prepare_code_for_analysis(self, processed_files: List[Dict]) -> Dict:
        """Prepare code content for GPT analysis with intelligent chunking."""
        total_tokens = self._estimate_total_tokens(processed_files)
        
        if total_tokens <= self.max_tokens:
            # Small enough to send as one chunk
            return self._create_single_chunk(processed_files)
        else:
            # Need to chunk the code
            return self._create_chunked_content(processed_files)
    
    def _estimate_total_tokens(self, processed_files: List[Dict]) -> int:
        """Estimate total tokens for all files."""
        total_content = ""
        for file in processed_files:
            total_content += f"\n\n--- {file['path']} ---\n{file['content']}"
        
        return len(self.encoding.encode(total_content))
    
    def _create_single_chunk(self, processed_files: List[Dict]) -> Dict:
        """Create a single chunk with all files."""
        combined_content = ""
        file_summary = []
        
        for file in processed_files:
            combined_content += f"\n\n--- File: {file['path']} ({file['language']}) ---\n"
            combined_content += file['content']
            
            file_summary.append({
                'path': file['path'],
                'language': file['language'],
                'lines': file['lines'],
                'size': file['size']
            })
        
        return {
            'strategy': 'single_chunk',
            'content': combined_content,
            'files': file_summary,
            'total_tokens': len(self.encoding.encode(combined_content))
        }
    
    def _create_chunked_content(self, processed_files: List[Dict]) -> Dict:
        """Create multiple chunks for large repositories."""
        chunks = []
        current_chunk = ""
        current_files = []
        current_tokens = 0
        
        # Sort files by importance (main files first, then by size)
        sorted_files = self._sort_files_by_importance(processed_files)
        
        for file in sorted_files:
            file_content = f"\n\n--- File: {file['path']} ({file['language']}) ---\n{file['content']}"
            file_tokens = len(self.encoding.encode(file_content))
            
            # If single file is too large, chunk it
            if file_tokens > self.max_tokens * 0.8:
                # Save current chunk if it has content
                if current_chunk:
                    chunks.append({
                        'content': current_chunk,
                        'files': current_files.copy(),
                        'tokens': current_tokens
                    })
                    current_chunk = ""
                    current_files = []
                    current_tokens = 0
                
                # Chunk the large file
                file_chunks = self._chunk_large_file(file)
                chunks.extend(file_chunks)
                
            elif current_tokens + file_tokens > self.max_tokens * 0.9:
                # Save current chunk and start new one
                if current_chunk:
                    chunks.append({
                        'content': current_chunk,
                        'files': current_files.copy(),
                        'tokens': current_tokens
                    })
                
                current_chunk = file_content
                current_files = [file['path']]
                current_tokens = file_tokens
                
            else:
                # Add to current chunk
                current_chunk += file_content
                current_files.append(file['path'])
                current_tokens += file_tokens
        
        # Add final chunk if it has content
        if current_chunk:
            chunks.append({
                'content': current_chunk,
                'files': current_files,
                'tokens': current_tokens
            })
        
        return {
            'strategy': 'multi_chunk',
            'chunks': chunks,
            'total_chunks': len(chunks),
            'total_files': len(processed_files)
        }
    
    def _chunk_large_file(self, file: Dict) -> List[Dict]:
        """Chunk a single large file into smaller pieces."""
        content = file['content']
        language = file['language']
        lines = content.splitlines()
        
        # Try to find logical boundaries
        boundaries = self._find_logical_boundaries(lines, language)
        
        if not boundaries:
            # Fall back to simple line-based chunking
            return self._chunk_by_lines(file)
        
        chunks = []
        chunk_size = self.max_tokens // 2  # Conservative chunk size
        
        current_chunk_lines = []
        current_tokens = 0
        
        for i, line in enumerate(lines):
            line_tokens = len(self.encoding.encode(line))
            
            # Check if we're at a boundary and chunk is getting large
            if (i in boundaries and 
                current_tokens > chunk_size * 0.7 and 
                current_chunk_lines):
                
                # Create chunk
                chunk_content = f"--- File: {file['path']} (Part {len(chunks) + 1}) ---\n"
                chunk_content += '\n'.join(current_chunk_lines)
                
                chunks.append({
                    'content': chunk_content,
                    'files': [f"{file['path']} (Part {len(chunks) + 1})"],
                    'tokens': current_tokens
                })
                
                # Start new chunk with some overlap
                overlap_lines = current_chunk_lines[-5:] if len(current_chunk_lines) > 5 else current_chunk_lines
                current_chunk_lines = overlap_lines + [line]
                current_tokens = len(self.encoding.encode('\n'.join(current_chunk_lines)))
                
            else:
                current_chunk_lines.append(line)
                current_tokens += line_tokens
        
        # Add final chunk
        if current_chunk_lines:
            chunk_content = f"--- File: {file['path']} (Part {len(chunks) + 1}) ---\n"
            chunk_content += '\n'.join(current_chunk_lines)
            
            chunks.append({
                'content': chunk_content,
                'files': [f"{file['path']} (Part {len(chunks) + 1})"],
                'tokens': current_tokens
            })
        
        return chunks
    
    def _find_logical_boundaries(self, lines: List[str], language: str) -> List[int]:
        """Find logical boundaries in code (functions, classes, etc.)."""
        boundaries = []
        patterns = self.function_patterns.get(language, [])
        
        for i, line in enumerate(lines):
            for pattern in patterns:
                if re.match(pattern, line.strip(), re.IGNORECASE):
                    boundaries.append(i)
                    break
        
        return boundaries
    
    def _chunk_by_lines(self, file: Dict) -> List[Dict]:
        """Simple line-based chunking as fallback."""
        lines = file['content'].splitlines()
        chunks = []
        chunk_size = 1000  # Lines per chunk
        overlap = 50  # Lines of overlap
        
        for i in range(0, len(lines), chunk_size - overlap):
            chunk_lines = lines[i:i + chunk_size]
            chunk_content = f"--- File: {file['path']} (Lines {i+1}-{i+len(chunk_lines)}) ---\n"
            chunk_content += '\n'.join(chunk_lines)
            
            chunks.append({
                'content': chunk_content,
                'files': [f"{file['path']} (Lines {i+1}-{i+len(chunk_lines)})"],
                'tokens': len(self.encoding.encode(chunk_content))
            })
        
        return chunks
    
    def _sort_files_by_importance(self, processed_files: List[Dict]) -> List[Dict]:
        """Sort files by importance for analysis."""
        def importance_score(file):
            score = 0
            
            # Main files get higher priority
            if any(main in file['name'].lower() for main in ['main', 'index', 'app', 'server']):
                score += 100
            
            # Configuration files get medium priority
            if any(config in file['name'].lower() for config in ['config', 'settings', 'package']):
                score += 50
            
            # Larger files might be more important
            score += min(file['lines'] / 100, 50)
            
            # Certain languages get priority
            if file['language'] in ['python', 'javascript', 'java', 'cobol']:
                score += 25
            
            return score
        
        return sorted(processed_files, key=importance_score, reverse=True)
