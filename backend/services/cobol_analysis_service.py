import os
import json
import asyncio
import logging
from typing import List, Dict, Optional
from models.schemas import ArchitecturalAnalysis, ArchitecturalComponent, ArchitecturalPattern, RepositoryInfo, DiagramData
from services.openai_service import OpenAIService
from utils.cobol_chunker import CobolChunker
from utils.analysis_cache import AnalysisCache

logger = logging.getLogger(__name__)

class CobolAnalysisService:
    """COBOL-specific analysis service with domain expertise."""
    
    def __init__(self):
        self.openai_service = OpenAIService()
        self.analysis_cache = AnalysisCache(cache_dir="temp_cache/cobol_analysis")
        self.cache = {}
        
    async def analyze_cobol_architecture(self, code_content: Dict, repo_info: RepositoryInfo) -> ArchitecturalAnalysis:
        """Analyze COBOL code with domain-specific understanding."""
        try:
            if code_content['strategy'] == 'single_chunk':
                return await self._analyze_single_cobol_file(code_content, repo_info)
            elif code_content['strategy'] == 'cobol_structured':
                return await self._analyze_cobol_chunks(code_content, repo_info)
            else:
                # Fallback to single file analysis
                return await self._analyze_single_cobol_file(code_content, repo_info)
                
        except Exception as e:
            logger.error(f"Error in COBOL architectural analysis: {str(e)}")
            raise
    
    async def _analyze_single_cobol_file(self, code_content: Dict, repo_info: RepositoryInfo) -> ArchitecturalAnalysis:
        """Analyze single COBOL file with COBOL-specific prompts and caching."""
        content = code_content['content']
        file_info = {
            'name': repo_info.name,
            'language': 'COBOL',
            'strategy': 'single_chunk'
        }
        
        # Check cache first
        cached_response = self.analysis_cache.get_cached_analysis(content, file_info)
        if cached_response:
            logger.info(f"Using cached analysis for {repo_info.name}")
            return self._parse_cobol_response(cached_response)
        
        # If not cached, call LLM
        logger.info(f"Calling LLM for fresh analysis of {repo_info.name}")
        system_prompt = self._get_cobol_system_prompt()
        user_prompt = self._create_cobol_analysis_prompt(content, repo_info)
        
        response = await self.openai_service.client.chat.completions.create(
            model=self.openai_service.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            max_tokens=3000
        )
        
        response_content = response.choices[0].message.content
        
        # Cache the response
        self.analysis_cache.save_analysis(content, file_info, response_content)
        
        return self._parse_cobol_response(response_content)
    
    async def _analyze_cobol_chunks(self, code_content: Dict, repo_info: RepositoryInfo) -> ArchitecturalAnalysis:
        """Analyze COBOL chunks and merge results."""
        chunks = code_content['chunks']
        chunk_analyses = []
        
        # Analyze each chunk with COBOL context
        for i, chunk in enumerate(chunks):
            logger.info(f"Analyzing COBOL chunk {i+1}/{len(chunks)}: {chunk.get('section', 'UNKNOWN')}")
            
            analysis = await self._analyze_cobol_chunk(chunk, i+1, len(chunks))
            chunk_analyses.append(analysis)
        
        # Merge chunk analyses into unified COBOL analysis
        return await self._merge_cobol_analyses(chunk_analyses, repo_info)
    
    async def _analyze_cobol_chunk(self, chunk: Dict, chunk_num: int, total_chunks: int) -> Dict:
        """Analyze individual COBOL chunk with caching."""
        content = chunk['content']
        file_info = {
            'name': f"chunk_{chunk_num}_{chunk.get('section', 'UNKNOWN')}",
            'language': 'COBOL',
            'strategy': 'cobol_structured',
            'chunk_num': chunk_num,
            'total_chunks': total_chunks
        }
        
        # Check cache first
        cached_response = self.analysis_cache.get_cached_analysis(content, file_info)
        if cached_response:
            logger.info(f"Using cached analysis for chunk {chunk_num}/{total_chunks}")
            return json.loads(cached_response) if isinstance(cached_response, str) else cached_response
        
        # If not cached, call LLM
        logger.info(f"Calling LLM for fresh analysis of chunk {chunk_num}/{total_chunks}")
        system_prompt = self._get_cobol_chunk_system_prompt()
        user_prompt = f"""
Analyze this COBOL code chunk ({chunk_num}/{total_chunks}):

Section: {chunk.get('section', 'UNKNOWN')}
Lines: {chunk.get('files', [{}])[0].get('lines', 0)}

Code:
{content}

Focus on COBOL-specific elements:
1. Division/Section structure
2. Data definitions and usage
3. Paragraph logic and flow
4. File operations and I/O
5. Business logic patterns
6. COBOL-specific constructs (MOVE, PERFORM, etc.)
"""
        
        response = await self.openai_service.client.chat.completions.create(
            model=self.openai_service.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            max_tokens=1500
        )
        
        response_content = response.choices[0].message.content
        
        # Cache the chunk analysis
        self.analysis_cache.save_analysis(content, file_info, response_content)
        
        return {
            'section': chunk.get('section', 'UNKNOWN'),
            'analysis': response_content,
            'chunk_number': chunk_num
        }
    
    async def _merge_cobol_analyses(self, chunk_analyses: List[Dict], repo_info: RepositoryInfo) -> ArchitecturalAnalysis:
        """Merge COBOL chunk analyses into unified view."""
        system_prompt = self._get_cobol_merge_system_prompt()
        
        # Organize analyses by section
        sections_analysis = {}
        for chunk_analysis in chunk_analyses:
            section = chunk_analysis['section']
            if section not in sections_analysis:
                sections_analysis[section] = []
            sections_analysis[section].append(chunk_analysis['analysis'])
        
        # Create merge prompt
        merge_content = f"""
COBOL Program: {repo_info.name}
Total Lines: {repo_info.total_lines}

Section Analyses:
"""
        
        for section, analyses in sections_analysis.items():
            merge_content += f"\n=== {section} ===\n"
            for i, analysis in enumerate(analyses):
                merge_content += f"Part {i+1}: {analysis}\n\n"
        
        user_prompt = f"""
{merge_content}

Merge these COBOL section analyses into a unified architectural view.
Focus on:
1. Overall program structure and flow
2. Data architecture (files, records, working storage)
3. Business logic organization
4. Integration points and dependencies
5. COBOL-specific patterns and practices
6. Recommendations for improvement
"""
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            max_tokens=3000
        )
        
        return self._parse_cobol_response(response.choices[0].message.content)
    
    def _get_cobol_system_prompt(self) -> str:
        """COBOL-specific system prompt from cobolinstructions.md."""
        return """You are a senior COBOL code analyst. Your job: read the supplied COBOL source and produce a precise, self-contained analysis with zero external assumptions. Do not invent paragraphs or data that aren't present. If something is missing, say so briefly and continue with what is available.

Analyze the following COBOL program and produce THREE deliverables in this exact order and formatting.

RESPONSE REQUIREMENTS (STRICT)
1) Call Tree + Pseudocode (Step-by-step mental model)
   - Title: "Call Tree + Pseudocode"
   - First, a monospace call tree showing PERFORM/call relationships from entry paragraph downward.
     * Show each paragraph label exactly as in code.
     * Use indentation and box-drawing or ASCII tree. Example:
   0000-Mainline
    ├─ 1000-Begin-Job
    │   └─ 1100-Load-WS-Tables
    ├─ 2000-Process
    │   └─ 2200-Do-Some-Searching
    └─ 3000-End-Job
   - Then provide concise pseudocode blocks for each major paragraph (top-level first), summarizing loops, SEARCH/WHEN, IF/ELSE, table traversals (1D/2D/3D), accumulators, and DISPLAY side effects.
   - Note whether tables use SUBSCRIPTS or INDEXED BY and where 88-level condition names are used.

2) Data Dictionary & Structural Layout (Tabular)
   - Title: "Data Dictionary & Structural Layout"
   - Two subtables minimum:
     A) "Orchestration paragraphs" with columns: Paragraph | Role/Responsibility.
     B) "Working-Storage structures" with columns: Group/Area | Structure name | Purpose | Key fields/occurs/indexing.
   - If present, also add a short "Traversal mechanics & invariants" bullet list (subscripts vs indexes, element counters, search indexes), and "Outputs" (what the program prints/returns).
   - Pull names exactly from WORKING-STORAGE/PARAMETERS/FD/01-level groups, including OCCURS counts, INDEXED BY names, and 88-level condition names.

3) PlantUML Sequence Diagrams
   - Title: "PlantUML Diagrams"
   - Provide TWO separate code blocks, both fenced with ```plantuml
     A) High-Level Orchestration: show the call flow among paragraphs (actors/participants may be: Runtime, 0000-Mainline, 1000-Begin-Job, 1100-Load-WS-Tables, 2000-Process, 2200-Do-Some-Searching, 3000-End-Job, and a database/collections lifeline for Working-Storage tables).
     B) Processing Deep-Dive (if 3D tables or complex loops exist): contrast "Subscripts" vs "Indexes" paths, or otherwise focus on the densest processing area identified.
   - Avoid decorative text; use clear groups for phases (e.g., "1D Numeric Analytics", "2D Student–Course–Grade", "3D Totals (Subscripts)", "3D Totals (Indexes)").
   - Do not embed rendered images; output only the PlantUML source.

GENERAL RULES
- Base everything strictly on the provided code; do not import outside knowledge.
- Quote paragraph and data names verbatim.
- If a section is absent in the code, include the section heading with a one-line note: "Not present in source."
- Keep each section concise but complete; no fluff.
- Use consistent headings exactly as specified so my UI can split sections reliably."""
    
    def _get_cobol_chunk_system_prompt(self) -> str:
        """System prompt for COBOL chunk analysis."""
        return """You are a COBOL expert analyzing a section of COBOL code. 

Focus on:
1. COBOL division/section structure
2. Data definitions and usage patterns
3. Paragraph logic and control flow
4. File I/O operations
5. Business logic implementation
6. COBOL-specific constructs and patterns

Provide concise analysis highlighting the most important architectural aspects of this code section."""
    
    def _get_cobol_merge_system_prompt(self) -> str:
        """System prompt for merging COBOL analyses."""
        return """You are a COBOL architect merging multiple section analyses into a unified view.

Create a comprehensive architectural analysis that:
1. Combines insights from all sections
2. Identifies overall program structure and flow
3. Maps data architecture and dependencies
4. Highlights business logic patterns
5. Provides actionable recommendations

Return the same JSON structure as individual analyses but with merged, comprehensive content."""
    
    def _create_cobol_analysis_prompt(self, content: str, repo_info: RepositoryInfo) -> str:
        """Create COBOL-specific analysis prompt using the template from cobolinstructions.md."""
        return f"""INPUT METADATA
- File name: {repo_info.name}
- Language: COBOL
- Purpose: Architectural & Structural understanding for a code-analysis app
- Source Code (verbatim, unchanged) begins after the line "<<<CODE>>>":
<<<CODE>>>
{content}
<<<END-CODE>>>"""
    
    def _parse_cobol_response(self, response_content: str) -> ArchitecturalAnalysis:
        """Parse COBOL analysis response following the THREE deliverables format."""
        try:
            # DEBUG: Log the full response content
            logger.info(f"COBOL Analysis Response Length: {len(response_content)} characters")
            logger.info(f"COBOL Analysis Response Preview (first 500 chars): {response_content[:500]}")
            
            # The response should contain the three sections as specified in cobolinstructions.md
            # Parse the structured response directly instead of looking for JSON
            
            # Extract the three main sections
            call_tree_section = self._extract_section(response_content, "Call Tree + Pseudocode")
            data_dict_section = self._extract_section(response_content, "Data Dictionary & Structural Layout")
            plantuml_section = self._extract_section(response_content, "PlantUML Diagrams")
            
            # DEBUG: Log extracted sections
            logger.info(f"Call Tree Section Length: {len(call_tree_section)} characters")
            logger.info(f"Call Tree Section Preview: {call_tree_section[:300] if call_tree_section else 'EMPTY'}")
            logger.info(f"Data Dict Section Length: {len(data_dict_section)} characters")
            logger.info(f"PlantUML Section Length: {len(plantuml_section)} characters")
            
            # Create components from the orchestration paragraphs
            components = self._extract_components_from_data_dict(data_dict_section)
            
            # Extract patterns from call tree and pseudocode
            patterns = self._extract_patterns_from_call_tree(call_tree_section)
            
            # Create overview from all sections
            overview = self._create_overview_from_sections(call_tree_section, data_dict_section, plantuml_section)
            
            # DEBUG: Log the final overview content
            logger.info(f"Final Overview Length: {len(overview)} characters")
            logger.info(f"Final Overview Preview: {overview[:500] if overview else 'EMPTY'}")
            
            return ArchitecturalAnalysis(
                overview=overview,
                components=components,
                patterns=patterns,
                dependencies=[],  # Will be extracted from working storage analysis
                external_integrations=[],  # Will be extracted from file operations
                recommendations=[]  # Can be generated based on analysis
            )
            
        except Exception as e:
            logger.error(f"Error parsing COBOL response: {str(e)}")
            # Return the raw response as overview for debugging
            return ArchitecturalAnalysis(
                overview=f"COBOL Analysis Results:\n\n{response_content}",
                components=[],
                patterns=[],
                dependencies=[],
                external_integrations=[],
                recommendations=[]
            )
    
    def _extract_section(self, content: str, section_title: str) -> str:
        """Extract a specific section from the COBOL analysis response."""
        try:
            # Look for the section title
            start_marker = f"# {section_title}"
            alt_start_marker = section_title
            
            start_pos = content.find(start_marker)
            if start_pos == -1:
                start_pos = content.find(alt_start_marker)
            
            if start_pos == -1:
                return ""
            
            # Find the next section or end of content
            next_section_pos = len(content)
            for next_title in ["Call Tree + Pseudocode", "Data Dictionary & Structural Layout", "PlantUML Diagrams"]:
                if next_title != section_title:
                    next_pos = content.find(f"# {next_title}", start_pos + 1)
                    if next_pos == -1:
                        next_pos = content.find(next_title, start_pos + 1)
                    if next_pos != -1 and next_pos < next_section_pos:
                        next_section_pos = next_pos
            
            return content[start_pos:next_section_pos].strip()
        except Exception as e:
            logger.error(f"Error extracting section {section_title}: {str(e)}")
            return ""
    
    def _extract_components_from_data_dict(self, data_dict_section: str) -> List[ArchitecturalComponent]:
        """Extract components from the Data Dictionary section."""
        components = []
        try:
            # Look for orchestration paragraphs table
            lines = data_dict_section.split('\n')
            in_orchestration_table = False
            
            for line in lines:
                if "Orchestration paragraphs" in line or "Paragraph | Role" in line:
                    in_orchestration_table = True
                    continue
                elif "Working-Storage structures" in line or in_orchestration_table and line.strip() and not line.startswith('|'):
                    in_orchestration_table = False
                
                if in_orchestration_table and '|' in line and not line.startswith('|---'):
                    parts = [part.strip() for part in line.split('|')]
                    if len(parts) >= 3:  # Skip header separators
                        paragraph_name = parts[1].strip()
                        role = parts[2].strip()
                        if paragraph_name and role and paragraph_name != "Paragraph":
                            components.append(ArchitecturalComponent(
                                component_name=paragraph_name,
                                type="paragraph",
                                responsibilities=[role],
                                dependencies=[]
                            ))
        except Exception as e:
            logger.error(f"Error extracting components: {str(e)}")
        
        return components
    
    def _extract_patterns_from_call_tree(self, call_tree_section: str) -> List[ArchitecturalPattern]:
        """Extract patterns from the Call Tree section."""
        patterns = []
        try:
            # Look for common COBOL patterns in the pseudocode
            if "PERFORM" in call_tree_section:
                patterns.append(ArchitecturalPattern(
                    pattern="PERFORM Statement Pattern",
                    description="Uses PERFORM statements for modular paragraph execution",
                    confidence=0.9
                ))
            
            if "SEARCH" in call_tree_section or "table" in call_tree_section.lower():
                patterns.append(ArchitecturalPattern(
                    pattern="Table Processing Pattern",
                    description="Implements table search and processing operations",
                    confidence=0.8
                ))
            
            if "88-level" in call_tree_section or "condition" in call_tree_section.lower():
                patterns.append(ArchitecturalPattern(
                    pattern="Condition Name Pattern",
                    description="Uses 88-level condition names for data validation",
                    confidence=0.7
                ))
        except Exception as e:
            logger.error(f"Error extracting patterns: {str(e)}")
        
        return patterns
    
    def _create_overview_from_sections(self, call_tree: str, data_dict: str, plantuml: str) -> str:
        """Create overview from all three sections."""
        overview = "COBOL Program Analysis\n\n"
        
        if call_tree:
            overview += "## Call Tree & Program Flow\n"
            # Include the COMPLETE call tree, not just first 10 lines
            overview += call_tree + "\n\n"
        
        if data_dict:
            overview += "## Data Structures\n"
            overview += data_dict + "\n\n"
        
        if plantuml:
            overview += "## Sequence Diagrams\n"
            overview += plantuml + "\n\n"
        
        return overview
    
    async def generate_cobol_diagrams(self, analysis: ArchitecturalAnalysis, code_content: Dict) -> List[DiagramData]:
        """Generate COBOL-specific diagrams."""
        diagrams = []
        
        try:
            # Generate COBOL program flow diagram
            flow_diagram = await self._generate_cobol_flow_diagram(analysis)
            if flow_diagram:
                diagrams.append(flow_diagram)
            
            # Generate data structure diagram
            data_diagram = await self._generate_cobol_data_diagram(analysis)
            if data_diagram:
                diagrams.append(data_diagram)
                
        except Exception as e:
            logger.error(f"Error generating COBOL diagrams: {str(e)}")
        
        return diagrams
    
    async def _generate_cobol_flow_diagram(self, analysis: ArchitecturalAnalysis) -> Optional[DiagramData]:
        """Generate COBOL program flow diagram."""
        if not analysis.components:
            return None
            
        prompt = f"""
Create a Mermaid flowchart for this COBOL program:

Components: {[comp.component_name for comp in analysis.components]}
Overview: {analysis.overview}

Create a flowchart showing:
1. Main program flow
2. Paragraph calls and relationships
3. Decision points
4. File operations

Return ONLY JSON: {{"mermaid_code": "flowchart TD\\n...", "description": "COBOL program flow"}}
"""
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Create COBOL-specific Mermaid diagrams. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=800
            )
            
            result = json.loads(response.choices[0].message.content)
            
            return DiagramData(
                title="COBOL Program Flow",
                diagram_type="flowchart",
                mermaid_code=result.get("mermaid_code", "flowchart TD\nA[Main Program]"),
                description=result.get("description", "COBOL program execution flow")
            )
            
        except Exception as e:
            logger.error(f"Error generating COBOL flow diagram: {str(e)}")
            return None
    
    async def _generate_cobol_data_diagram(self, analysis: ArchitecturalAnalysis) -> Optional[DiagramData]:
        """Generate COBOL data structure diagram."""
        prompt = f"""
Create a Mermaid diagram showing COBOL data structures:

Dependencies: {analysis.dependencies}
Components: {[comp.component_name for comp in analysis.components]}

Show:
1. File definitions and records
2. Working storage variables
3. Data relationships
4. COPY book usage

Return ONLY JSON: {{"mermaid_code": "graph TD\\n...", "description": "COBOL data structures"}}
"""
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Create COBOL data structure diagrams. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=800
            )
            
            result = json.loads(response.choices[0].message.content)
            
            return DiagramData(
                title="COBOL Data Structures",
                diagram_type="graph",
                mermaid_code=result.get("mermaid_code", "graph TD\nA[Data Structure]"),
                description=result.get("description", "COBOL data organization")
            )
            
        except Exception as e:
            logger.error(f"Error generating COBOL data diagram: {str(e)}")
            return None
