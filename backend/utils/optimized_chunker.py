import re
import tiktoken
from typing import List, Dict, Tuple
import logging

logger = logging.getLogger(__name__)

class OptimizedChunker:
    """Optimized code chunker that creates fewer, more intelligent chunks."""
    
    def __init__(self, max_tokens: int = 120000):  # Increased chunk size
        self.max_tokens = max_tokens
        self.encoding = tiktoken.encoding_for_model("gpt-4")
        
        # File importance weights
        self.importance_weights = {
            'main': 100, 'index': 90, 'app': 85, 'server': 80,
            'config': 70, 'settings': 65, 'package': 60,
            'model': 75, 'controller': 75, 'service': 75,
            'component': 70, 'util': 50, 'helper': 50,
            'test': 30, 'spec': 30, 'readme': 20
        }
        
        # Language priorities
        self.language_priorities = {
            'cobol': 100, 'python': 90, 'javascript': 85, 'typescript': 85,
            'java': 80, 'cpp': 75, 'c': 75, 'go': 70,
            'json': 40, 'yaml': 40, 'xml': 35, 'txt': 20
        }
    
    def prepare_code_for_analysis(self, processed_files: List[Dict]) -> Dict:
        """Prepare code with optimized chunking strategy."""
        # Check if this is COBOL code - use specialized chunking
        if processed_files and processed_files[0].get('language', '').lower() == 'cobol':
            from utils.cobol_chunker import CobolChunker
            cobol_chunker = CobolChunker(self.max_tokens)
            return cobol_chunker.chunk_cobol_file(processed_files[0]['content'], processed_files[0])
        
        total_tokens = self._estimate_total_tokens(processed_files)
        
        if total_tokens <= self.max_tokens:
            return self._create_single_chunk(processed_files)
        
        # Use smart chunking that creates fewer, more meaningful chunks
        return self._create_smart_chunks(processed_files)
    
    def _create_smart_chunks(self, processed_files: List[Dict]) -> Dict:
        """Create intelligent chunks based on file relationships and importance."""
        # Group files by type and importance
        file_groups = self._group_files_by_type(processed_files)
        
        chunks = []
        
        # Process each group
        for group_name, files in file_groups.items():
            if not files:
                continue
                
            group_tokens = sum(len(self.encoding.encode(f['content'])) for f in files)
            
            if group_tokens <= self.max_tokens * 0.8:
                # Entire group fits in one chunk
                chunk = self._create_group_chunk(files, group_name)
                chunks.append(chunk)
            else:
                # Split group into sub-chunks
                sub_chunks = self._split_group_intelligently(files, group_name)
                chunks.extend(sub_chunks)
        
        return {
            'strategy': 'smart_chunk',
            'chunks': chunks,
            'total_chunks': len(chunks),
            'total_files': len(processed_files),
            'grouping_strategy': 'type_based'
        }
    
    def _group_files_by_type(self, processed_files: List[Dict]) -> Dict[str, List[Dict]]:
        """Group files by their type and importance."""
        groups = {
            'core': [],           # Main application files
            'business_logic': [], # Models, services, controllers
            'configuration': [],  # Config files
            'utilities': [],      # Helper functions, utilities
            'tests': [],         # Test files
            'documentation': []   # README, docs
        }
        
        for file in processed_files:
            file_name = file['name'].lower()
            file_path = file['path'].lower()
            
            # Categorize files
            if any(main in file_name for main in ['main', 'index', 'app', 'server']):
                groups['core'].append(file)
            elif any(bl in file_path for bl in ['model', 'service', 'controller', 'business', 'logic']):
                groups['business_logic'].append(file)
            elif any(config in file_name for config in ['config', 'settings', 'package', '.env']):
                groups['configuration'].append(file)
            elif any(test in file_path for test in ['test', 'spec', '__test__']):
                groups['tests'].append(file)
            elif any(doc in file_name for doc in ['readme', 'doc', 'guide']):
                groups['documentation'].append(file)
            else:
                groups['utilities'].append(file)
        
        # Sort each group by importance
        for group_name in groups:
            groups[group_name] = sorted(groups[group_name], 
                                      key=self._calculate_file_importance, 
                                      reverse=True)
        
        return groups
    
    def _calculate_file_importance(self, file: Dict) -> int:
        """Calculate importance score for a file."""
        score = 0
        file_name = file['name'].lower()
        
        # Name-based importance
        for keyword, weight in self.importance_weights.items():
            if keyword in file_name:
                score += weight
                break
        
        # Language-based importance
        language = file.get('language', '').lower()
        score += self.language_priorities.get(language, 30)
        
        # Size-based importance (larger files might be more important)
        score += min(file.get('lines', 0) / 50, 30)
        
        return score
    
    def _create_group_chunk(self, files: List[Dict], group_name: str) -> Dict:
        """Create a chunk from a group of related files."""
        combined_content = f"=== {group_name.upper()} FILES GROUP ===\n\n"
        file_list = []
        
        for file in files:
            combined_content += f"\n--- File: {file['path']} ({file['language']}) ---\n"
            combined_content += file['content']
            combined_content += "\n\n"
            
            file_list.append({
                'path': file['path'],
                'language': file['language'],
                'lines': file['lines'],
                'importance': self._calculate_file_importance(file)
            })
        
        return {
            'content': combined_content,
            'files': file_list,
            'group': group_name,
            'tokens': len(self.encoding.encode(combined_content)),
            'file_count': len(files)
        }
    
    def _split_group_intelligently(self, files: List[Dict], group_name: str) -> List[Dict]:
        """Split a large group into intelligent sub-chunks."""
        chunks = []
        current_chunk_files = []
        current_tokens = 0
        chunk_number = 1
        
        for file in files:
            file_tokens = len(self.encoding.encode(file['content']))
            
            # If single file is too large, handle it separately
            if file_tokens > self.max_tokens * 0.7:
                # Save current chunk if it has content
                if current_chunk_files:
                    chunk = self._create_sub_chunk(current_chunk_files, group_name, chunk_number)
                    chunks.append(chunk)
                    chunk_number += 1
                    current_chunk_files = []
                    current_tokens = 0
                
                # Create chunk for large file (potentially split it)
                large_file_chunks = self._handle_large_file(file, group_name, chunk_number)
                chunks.extend(large_file_chunks)
                chunk_number += len(large_file_chunks)
                
            elif current_tokens + file_tokens > self.max_tokens * 0.8:
                # Save current chunk and start new one
                if current_chunk_files:
                    chunk = self._create_sub_chunk(current_chunk_files, group_name, chunk_number)
                    chunks.append(chunk)
                    chunk_number += 1
                
                current_chunk_files = [file]
                current_tokens = file_tokens
                
            else:
                # Add to current chunk
                current_chunk_files.append(file)
                current_tokens += file_tokens
        
        # Add final chunk if it has content
        if current_chunk_files:
            chunk = self._create_sub_chunk(current_chunk_files, group_name, chunk_number)
            chunks.append(chunk)
        
        return chunks
    
    def _create_sub_chunk(self, files: List[Dict], group_name: str, chunk_number: int) -> Dict:
        """Create a sub-chunk from files."""
        combined_content = f"=== {group_name.upper()} GROUP - PART {chunk_number} ===\n\n"
        file_list = []
        
        for file in files:
            combined_content += f"\n--- File: {file['path']} ({file['language']}) ---\n"
            combined_content += file['content']
            combined_content += "\n\n"
            
            file_list.append({
                'path': file['path'],
                'language': file['language'],
                'lines': file['lines']
            })
        
        return {
            'content': combined_content,
            'files': file_list,
            'group': f"{group_name}_part_{chunk_number}",
            'tokens': len(self.encoding.encode(combined_content)),
            'file_count': len(files)
        }
    
    def _handle_large_file(self, file: Dict, group_name: str, start_chunk_number: int) -> List[Dict]:
        """Handle a single large file by splitting it intelligently."""
        content = file['content']
        lines = content.splitlines()
        
        # Try to find logical boundaries
        boundaries = self._find_logical_boundaries(lines, file.get('language', ''))
        
        if not boundaries or len(boundaries) < 2:
            # Simple split if no logical boundaries
            return self._simple_split_large_file(file, group_name, start_chunk_number)
        
        chunks = []
        chunk_number = start_chunk_number
        current_lines = []
        current_tokens = 0
        
        for i, line in enumerate(lines):
            line_tokens = len(self.encoding.encode(line))
            
            # Check if we're at a boundary and chunk is getting large
            if (i in boundaries and 
                current_tokens > self.max_tokens * 0.5 and 
                current_lines):
                
                # Create chunk
                chunk_content = f"=== {group_name.upper()} - {file['path']} (Part {chunk_number - start_chunk_number + 1}) ===\n"
                chunk_content += '\n'.join(current_lines)
                
                chunks.append({
                    'content': chunk_content,
                    'files': [{'path': f"{file['path']} (Part {chunk_number - start_chunk_number + 1})", 
                              'language': file['language'], 'lines': len(current_lines)}],
                    'group': f"{group_name}_large_file",
                    'tokens': current_tokens,
                    'file_count': 1
                })
                
                chunk_number += 1
                current_lines = [line]  # Start new chunk with current line
                current_tokens = line_tokens
                
            else:
                current_lines.append(line)
                current_tokens += line_tokens
        
        # Add final chunk
        if current_lines:
            chunk_content = f"=== {group_name.upper()} - {file['path']} (Part {chunk_number - start_chunk_number + 1}) ===\n"
            chunk_content += '\n'.join(current_lines)
            
            chunks.append({
                'content': chunk_content,
                'files': [{'path': f"{file['path']} (Part {chunk_number - start_chunk_number + 1})", 
                          'language': file['language'], 'lines': len(current_lines)}],
                'group': f"{group_name}_large_file",
                'tokens': current_tokens,
                'file_count': 1
            })
        
        return chunks
    
    def _simple_split_large_file(self, file: Dict, group_name: str, start_chunk_number: int) -> List[Dict]:
        """Simple split for large files without logical boundaries."""
        lines = file['content'].splitlines()
        chunks = []
        chunk_size = 2000  # Lines per chunk
        
        for i in range(0, len(lines), chunk_size):
            chunk_lines = lines[i:i + chunk_size]
            chunk_content = f"=== {group_name.upper()} - {file['path']} (Lines {i+1}-{i+len(chunk_lines)}) ===\n"
            chunk_content += '\n'.join(chunk_lines)
            
            chunks.append({
                'content': chunk_content,
                'files': [{'path': f"{file['path']} (Lines {i+1}-{i+len(chunk_lines)})", 
                          'language': file['language'], 'lines': len(chunk_lines)}],
                'group': f"{group_name}_large_file",
                'tokens': len(self.encoding.encode(chunk_content)),
                'file_count': 1
            })
        
        return chunks
    
    def _find_logical_boundaries(self, lines: List[str], language: str) -> List[int]:
        """Find logical boundaries in code."""
        boundaries = []
        
        # Language-specific patterns
        patterns = {
            'cobol': [r'^\s*\d+\s+PROCEDURE\s+DIVISION', r'^\s*\d+\s+\w+-SECTION'],
            'python': [r'^def\s+\w+', r'^class\s+\w+', r'^async\s+def\s+\w+'],
            'javascript': [r'function\s+\w+', r'class\s+\w+', r'const\s+\w+\s*='],
            'java': [r'public\s+class\s+\w+', r'public\s+\w+\s+\w+\s*\('],
        }
        
        language_patterns = patterns.get(language.lower(), patterns.get('python', []))
        
        for i, line in enumerate(lines):
            for pattern in language_patterns:
                if re.match(pattern, line.strip(), re.IGNORECASE):
                    boundaries.append(i)
                    break
        
        return boundaries
    
    def _estimate_total_tokens(self, processed_files: List[Dict]) -> int:
        """Estimate total tokens for all files."""
        total_content = ""
        for file in processed_files:
            total_content += f"\n\n--- {file['path']} ---\n{file['content']}"
        
        return len(self.encoding.encode(total_content))
    
    def _create_single_chunk(self, processed_files: List[Dict]) -> Dict:
        """Create a single chunk with all files."""
        combined_content = "=== COMPLETE REPOSITORY ANALYSIS ===\n\n"
        file_summary = []
        
        # Sort files by importance
        sorted_files = sorted(processed_files, key=self._calculate_file_importance, reverse=True)
        
        for file in sorted_files:
            combined_content += f"\n--- File: {file['path']} ({file['language']}) ---\n"
            combined_content += file['content']
            combined_content += "\n\n"
            
            file_summary.append({
                'path': file['path'],
                'language': file['language'],
                'lines': file['lines'],
                'size': file['size'],
                'importance': self._calculate_file_importance(file)
            })
        
        return {
            'strategy': 'single_chunk',
            'content': combined_content,
            'files': file_summary,
            'total_tokens': len(self.encoding.encode(combined_content))
        }
