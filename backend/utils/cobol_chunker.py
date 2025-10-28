import re
import tiktoken
from typing import List, Dict, Tuple
import logging

logger = logging.getLogger(__name__)

class CobolChunker:
    """COBOL-specific chunker that respects language structure."""
    
    def __init__(self, max_tokens: int = 120000):
        self.max_tokens = max_tokens
        self.encoding = tiktoken.encoding_for_model("gpt-4")
        
        # COBOL division patterns
        self.division_patterns = [
            r'^\s*IDENTIFICATION\s+DIVISION\s*\.',
            r'^\s*ENVIRONMENT\s+DIVISION\s*\.',
            r'^\s*DATA\s+DIVISION\s*\.',
            r'^\s*PROCEDURE\s+DIVISION\s*\.'
        ]
        
        # COBOL section patterns
        self.section_patterns = [
            r'^\s*PROGRAM-ID\s*\.',
            r'^\s*AUTHOR\s*\.',
            r'^\s*DATE-WRITTEN\s*\.',
            r'^\s*CONFIGURATION\s+SECTION\s*\.',
            r'^\s*INPUT-OUTPUT\s+SECTION\s*\.',
            r'^\s*FILE\s+SECTION\s*\.',
            r'^\s*WORKING-STORAGE\s+SECTION\s*\.',
            r'^\s*LINKAGE\s+SECTION\s*\.',
            r'^\s*LOCAL-STORAGE\s+SECTION\s*\.',
            r'^\s*\d+\s+\w+-SECTION\s*\.',
            r'^\s*\w+-SECTION\s*\.'
        ]
        
        # COBOL paragraph patterns (numbered and named)
        self.paragraph_patterns = [
            r'^\s*\d{4}-\w+\s*\.',  # 0100-MAIN-PROCESS.
            r'^\s*\d{3}-\w+\s*\.',   # 100-START.
            r'^\s*\d{2}-\w+\s*\.',   # 10-INIT.
            r'^\s*\w+-\w+\s*\.',     # MAIN-PROCESS.
            r'^\s*[A-Z][A-Z0-9-]*\s*\.',  # PARAGRAPH-NAME.
        ]
        
        # COBOL end markers
        self.end_patterns = [
            r'^\s*END\s+PROGRAM\s+\w+\s*\.',
            r'^\s*STOP\s+RUN\s*\.',
            r'^\s*EXIT\s*\.',
            r'^\s*GOBACK\s*\.'
        ]
    
    def chunk_cobol_file(self, file_content: str, file_info: Dict) -> Dict:
        """Chunk COBOL file by divisions/sections while preserving paragraph integrity."""
        lines = file_content.splitlines()
        total_tokens = len(self.encoding.encode(file_content))
        
        logger.info(f"Chunking COBOL file: {file_info['name']} ({len(lines)} lines, {total_tokens} tokens)")
        
        if total_tokens <= self.max_tokens:
            # Small file - return as single chunk
            return self._create_single_cobol_chunk(file_content, file_info)
        
        # Large file - chunk by COBOL structure
        chunks = self._chunk_by_cobol_structure(lines, file_info)
        
        return {
            'strategy': 'cobol_structured',
            'chunks': chunks,
            'total_chunks': len(chunks),
            'total_files': 1,
            'language': 'cobol'
        }
    
    def _create_single_cobol_chunk(self, content: str, file_info: Dict) -> Dict:
        """Create single chunk for small COBOL files."""
        return {
            'strategy': 'single_chunk',
            'content': f"=== COBOL FILE: {file_info['name']} ===\n\n{content}",
            'files': [file_info],
            'total_tokens': len(self.encoding.encode(content)),
            'language': 'cobol'
        }
    
    def _chunk_by_cobol_structure(self, lines: List[str], file_info: Dict) -> List[Dict]:
        """Chunk COBOL code by divisions and sections."""
        chunks = []
        current_chunk_lines = []
        current_tokens = 0
        chunk_number = 1
        current_section = "UNKNOWN"
        
        # Find all structural boundaries
        boundaries = self._find_cobol_boundaries(lines)
        
        for i, line in enumerate(lines):
            line_tokens = len(self.encoding.encode(line))
            
            # Check if we're at a major boundary
            boundary_info = boundaries.get(i)
            if boundary_info:
                current_section = boundary_info['type']
                
                # If chunk is getting large and we're at a good boundary, create chunk
                if (current_tokens > self.max_tokens * 0.7 and 
                    current_chunk_lines and 
                    boundary_info['level'] in ['division', 'section']):
                    
                    chunk = self._create_cobol_chunk(
                        current_chunk_lines, 
                        file_info, 
                        chunk_number, 
                        current_section
                    )
                    chunks.append(chunk)
                    chunk_number += 1
                    
                    # Start new chunk with overlap for context
                    overlap_lines = self._get_context_overlap(current_chunk_lines, boundary_info)
                    current_chunk_lines = overlap_lines + [line]
                    current_tokens = len(self.encoding.encode('\n'.join(current_chunk_lines)))
                    continue
            
            # Add line to current chunk
            current_chunk_lines.append(line)
            current_tokens += line_tokens
            
            # Emergency split if chunk gets too large
            if current_tokens > self.max_tokens * 0.9:
                # Find the last paragraph boundary to split at
                split_point = self._find_safe_split_point(current_chunk_lines)
                
                if split_point > 0:
                    # Create chunk up to split point
                    chunk_lines = current_chunk_lines[:split_point]
                    chunk = self._create_cobol_chunk(
                        chunk_lines, 
                        file_info, 
                        chunk_number, 
                        current_section
                    )
                    chunks.append(chunk)
                    chunk_number += 1
                    
                    # Continue with remaining lines
                    remaining_lines = current_chunk_lines[split_point-5:]  # Keep some overlap
                    current_chunk_lines = remaining_lines
                    current_tokens = len(self.encoding.encode('\n'.join(current_chunk_lines)))
        
        # Add final chunk
        if current_chunk_lines:
            chunk = self._create_cobol_chunk(
                current_chunk_lines, 
                file_info, 
                chunk_number, 
                current_section
            )
            chunks.append(chunk)
        
        logger.info(f"Created {len(chunks)} COBOL chunks")
        return chunks
    
    def _find_cobol_boundaries(self, lines: List[str]) -> Dict[int, Dict]:
        """Find all COBOL structural boundaries."""
        boundaries = {}
        
        for i, line in enumerate(lines):
            line_upper = line.upper().strip()
            
            # Check for divisions (highest level)
            for pattern in self.division_patterns:
                if re.match(pattern, line_upper):
                    division_name = self._extract_division_name(line_upper)
                    boundaries[i] = {
                        'type': division_name,
                        'level': 'division',
                        'line': line.strip()
                    }
                    break
            
            # Check for sections
            if i not in boundaries:
                for pattern in self.section_patterns:
                    if re.match(pattern, line_upper):
                        section_name = self._extract_section_name(line_upper)
                        boundaries[i] = {
                            'type': section_name,
                            'level': 'section',
                            'line': line.strip()
                        }
                        break
            
            # Check for paragraphs
            if i not in boundaries:
                for pattern in self.paragraph_patterns:
                    if re.match(pattern, line_upper):
                        paragraph_name = self._extract_paragraph_name(line_upper)
                        boundaries[i] = {
                            'type': paragraph_name,
                            'level': 'paragraph',
                            'line': line.strip()
                        }
                        break
        
        return boundaries
    
    def _extract_division_name(self, line: str) -> str:
        """Extract division name from line."""
        if 'IDENTIFICATION' in line:
            return 'IDENTIFICATION_DIVISION'
        elif 'ENVIRONMENT' in line:
            return 'ENVIRONMENT_DIVISION'
        elif 'DATA' in line:
            return 'DATA_DIVISION'
        elif 'PROCEDURE' in line:
            return 'PROCEDURE_DIVISION'
        return 'UNKNOWN_DIVISION'
    
    def _extract_section_name(self, line: str) -> str:
        """Extract section name from line."""
        if 'WORKING-STORAGE' in line:
            return 'WORKING_STORAGE_SECTION'
        elif 'FILE' in line:
            return 'FILE_SECTION'
        elif 'LINKAGE' in line:
            return 'LINKAGE_SECTION'
        elif 'CONFIGURATION' in line:
            return 'CONFIGURATION_SECTION'
        elif 'INPUT-OUTPUT' in line:
            return 'INPUT_OUTPUT_SECTION'
        elif 'PROGRAM-ID' in line:
            return 'PROGRAM_ID'
        return 'UNKNOWN_SECTION'
    
    def _extract_paragraph_name(self, line: str) -> str:
        """Extract paragraph name from line."""
        # Remove trailing period and extract name
        clean_line = line.rstrip('.').strip()
        if clean_line:
            return clean_line.replace(' ', '_')
        return 'UNKNOWN_PARAGRAPH'
    
    def _get_context_overlap(self, chunk_lines: List[str], boundary_info: Dict) -> List[str]:
        """Get context overlap for new chunk."""
        # For divisions/sections, include last few lines for context
        if boundary_info['level'] in ['division', 'section']:
            return chunk_lines[-3:] if len(chunk_lines) > 3 else chunk_lines
        return []
    
    def _find_safe_split_point(self, lines: List[str]) -> int:
        """Find safe point to split COBOL code (at paragraph boundary)."""
        # Look backwards for a paragraph boundary
        for i in range(len(lines) - 1, max(0, len(lines) - 50), -1):
            line_upper = lines[i].upper().strip()
            
            # Check if this line starts a paragraph
            for pattern in self.paragraph_patterns:
                if re.match(pattern, line_upper):
                    return i
        
        # If no paragraph found, split at 80% of chunk
        return int(len(lines) * 0.8)
    
    def _create_cobol_chunk(self, lines: List[str], file_info: Dict, chunk_number: int, section: str) -> Dict:
        """Create a COBOL chunk with proper metadata."""
        content = f"=== COBOL FILE: {file_info['name']} - CHUNK {chunk_number} ({section}) ===\n\n"
        content += '\n'.join(lines)
        
        return {
            'content': content,
            'files': [{
                'path': f"{file_info['path']} (Chunk {chunk_number})",
                'language': 'cobol',
                'lines': len(lines),
                'section': section
            }],
            'tokens': len(self.encoding.encode(content)),
            'chunk_number': chunk_number,
            'section': section,
            'language': 'cobol'
        }
