import os
import json
import asyncio
import hashlib
from typing import List, Dict, Optional, Tuple
from openai import AsyncOpenAI
import logging
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from models.schemas import (
    ArchitecturalAnalysis, ArchitecturalComponent, ArchitecturalPattern,
    DiagramData, Recommendation, RepositoryInfo
)

logger = logging.getLogger(__name__)

class EnhancedAnalysisService:
    """Enhanced analysis service with RAG patterns and performance optimizations."""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4-turbo-preview"
        self.cache = {}  # Simple in-memory cache
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        
    async def analyze_architecture_fast(self, code_content: Dict, repo_info: RepositoryInfo) -> ArchitecturalAnalysis:
        """Fast architectural analysis with optimizations."""
        try:
            # Generate cache key
            cache_key = self._generate_cache_key(code_content, repo_info)
            
            # Check cache first
            if cache_key in self.cache:
                logger.info("Returning cached analysis result")
                return self.cache[cache_key]
            
            # Check if this is COBOL code - use specialized analysis
            if repo_info.primary_language.lower() == 'cobol':
                from services.cobol_analysis_service import CobolAnalysisService
                cobol_service = CobolAnalysisService()
                result = await cobol_service.analyze_cobol_architecture(code_content, repo_info)
            # Check if this is a single file analysis
            elif repo_info.total_files == 1:
                result = await self._analyze_single_file(code_content, repo_info)
            elif code_content['strategy'] == 'single_chunk':
                result = await self._analyze_single_chunk_fast(code_content, repo_info)
            else:
                result = await self._analyze_multi_chunk_parallel(code_content, repo_info)
            
            # Cache the result
            self.cache[cache_key] = result
            return result
            
        except Exception as e:
            logger.error(f"Error in enhanced architectural analysis: {str(e)}")
            raise
    
    async def _analyze_single_chunk_fast(self, code_content: Dict, repo_info: RepositoryInfo) -> ArchitecturalAnalysis:
        """Optimized single chunk analysis with focused prompts."""
        # Use a more focused, efficient prompt
        system_prompt = self._get_focused_system_prompt()
        user_prompt = self._create_focused_analysis_prompt(code_content['content'], repo_info)
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            max_tokens=3000,  # Reduced for faster response
            stream=False
        )
        
        return self._parse_architectural_response(response.choices[0].message.content)
    
    async def _analyze_multi_chunk_parallel(self, code_content: Dict, repo_info: RepositoryInfo) -> ArchitecturalAnalysis:
        """Parallel chunk analysis with intelligent grouping."""
        chunks = code_content['chunks']
        
        # Group similar chunks using RAG patterns
        grouped_chunks = self._group_similar_chunks(chunks)
        logger.info(f"Grouped {len(chunks)} chunks into {len(grouped_chunks)} groups")
        
        # Analyze groups in parallel
        tasks = []
        for i, chunk_group in enumerate(grouped_chunks):
            task = self._analyze_chunk_group(chunk_group, i+1, len(grouped_chunks))
            tasks.append(task)
        
        # Execute all tasks in parallel
        chunk_analyses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and log them
        valid_analyses = []
        for i, analysis in enumerate(chunk_analyses):
            if isinstance(analysis, Exception):
                logger.error(f"Error in chunk group {i+1}: {str(analysis)}")
            else:
                valid_analyses.append(analysis)
        
        # Quick synthesis instead of full re-analysis
        return await self._quick_synthesis(valid_analyses, repo_info)
    
    def _group_similar_chunks(self, chunks: List[Dict]) -> List[List[Dict]]:
        """Group similar chunks using TF-IDF and cosine similarity."""
        if len(chunks) <= 3:
            return [[chunk] for chunk in chunks]
        
        # Extract text content for vectorization
        chunk_texts = [chunk['content'] for chunk in chunks]
        
        try:
            # Create TF-IDF vectors
            tfidf_matrix = self.vectorizer.fit_transform(chunk_texts)
            
            # Calculate similarity matrix
            similarity_matrix = cosine_similarity(tfidf_matrix)
            
            # Group chunks with similarity > 0.3
            groups = []
            used_indices = set()
            
            for i in range(len(chunks)):
                if i in used_indices:
                    continue
                
                group = [chunks[i]]
                used_indices.add(i)
                
                for j in range(i+1, len(chunks)):
                    if j not in used_indices and similarity_matrix[i][j] > 0.3:
                        group.append(chunks[j])
                        used_indices.add(j)
                
                groups.append(group)
            
            return groups
            
        except Exception as e:
            logger.warning(f"Error in chunk grouping: {str(e)}, falling back to individual chunks")
            return [[chunk] for chunk in chunks]
    
    async def _analyze_chunk_group(self, chunk_group: List[Dict], group_num: int, total_groups: int) -> str:
        """Analyze a group of similar chunks together."""
        logger.info(f"Analyzing chunk group {group_num}/{total_groups} ({len(chunk_group)} chunks)")
        
        # Combine chunks in the group
        combined_content = "\n\n--- CHUNK SEPARATOR ---\n\n".join([chunk['content'] for chunk in chunk_group])
        
        system_prompt = self._get_chunk_group_analysis_prompt()
        user_prompt = f"""
Analyze this group of related code chunks (Group {group_num}/{total_groups}):

{combined_content}

Focus on:
1. Main architectural components
2. Key patterns and relationships
3. Important dependencies
4. Business logic flow

Provide a concise analysis focusing on the most important architectural aspects.
"""
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            max_tokens=1500  # Reduced for faster processing
        )
        
        return response.choices[0].message.content
    
    async def _quick_synthesis(self, chunk_analyses: List[str], repo_info: RepositoryInfo) -> ArchitecturalAnalysis:
        """Quick synthesis using summarization instead of full re-analysis."""
        # Create a condensed summary of all analyses
        analysis_summary = self._create_analysis_summary(chunk_analyses)
        
        synthesis_prompt = self._get_quick_synthesis_prompt()
        user_prompt = f"""
Repository: {repo_info.name} ({repo_info.primary_language})
Files: {repo_info.total_files}, Lines: {repo_info.total_lines}

Analysis Summary:
{analysis_summary}

Synthesize into a unified architectural analysis with focus on:
1. Main components and their relationships
2. Key architectural patterns
3. Critical dependencies
4. 2-3 most important recommendations
"""
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": synthesis_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            max_tokens=2500
        )
        
        return self._parse_architectural_response(response.choices[0].message.content)
    
    def _create_analysis_summary(self, chunk_analyses: List[str]) -> str:
        """Create a condensed summary of chunk analyses."""
        # Extract key points from each analysis
        summary_points = []
        
        for i, analysis in enumerate(chunk_analyses):
            # Simple extraction of key sentences (first 2-3 sentences of each paragraph)
            paragraphs = analysis.split('\n\n')
            key_points = []
            
            for para in paragraphs[:3]:  # Take first 3 paragraphs
                sentences = para.split('. ')
                if sentences:
                    key_points.append(sentences[0] + '.')
            
            if key_points:
                summary_points.append(f"Group {i+1}: " + " ".join(key_points))
        
        return "\n\n".join(summary_points)
    
    def _generate_cache_key(self, code_content: Dict, repo_info: RepositoryInfo) -> str:
        """Generate cache key for analysis results."""
        # Create hash from repository info and content structure
        key_data = {
            'name': repo_info.name,
            'files': repo_info.total_files,
            'lines': repo_info.total_lines,
            'language': repo_info.primary_language,
            'strategy': code_content['strategy']
        }
        
        if code_content['strategy'] == 'single_chunk':
            # Hash a portion of the content
            content_hash = hashlib.md5(code_content['content'][:1000].encode()).hexdigest()
            key_data['content_hash'] = content_hash
        else:
            # Hash chunk count and first chunk snippet
            key_data['chunk_count'] = len(code_content['chunks'])
            if code_content['chunks']:
                first_chunk_hash = hashlib.md5(code_content['chunks'][0]['content'][:500].encode()).hexdigest()
                key_data['first_chunk_hash'] = first_chunk_hash
        
        return hashlib.md5(json.dumps(key_data, sort_keys=True).encode()).hexdigest()
    
    def _get_focused_system_prompt(self) -> str:
        """Focused system prompt for faster analysis."""
        return """You are an expert software architect. Analyze code repositories quickly and efficiently.

Focus on:
1. Main architectural components (3-5 key components)
2. Primary design patterns (2-3 most important)
3. Critical dependencies and integrations
4. Top 3 architectural recommendations

Be concise but comprehensive. Provide actionable insights.

Return analysis as JSON with this structure:
{
  "overview": "Brief architectural overview",
  "components": [{"component_name": "name", "type": "type", "responsibilities": ["resp1", "resp2"], "dependencies": ["dep1"]}],
  "patterns": [{"pattern": "pattern_name", "description": "brief_desc", "confidence": 0.8}],
  "dependencies": ["dep1", "dep2"],
  "external_integrations": ["integration1"],
  "recommendations": [{"title": "title", "description": "desc", "priority": "high|medium|low", "impact": "impact"}]
}"""
    
    def _get_chunk_group_analysis_prompt(self) -> str:
        """System prompt for chunk group analysis."""
        return """You are a software architect analyzing related code chunks.

Provide concise analysis focusing on:
1. Architectural components in this code group
2. Design patterns and relationships
3. Key dependencies
4. Business logic flow

Be brief but capture the essential architectural aspects."""
    
    def _get_quick_synthesis_prompt(self) -> str:
        """System prompt for quick synthesis."""
        return """You are a software architect synthesizing multiple code analyses.

Create a unified architectural view from the provided analysis summaries.

Return JSON with the same structure as individual analyses but focus on:
1. Most important components across all analyses
2. Key patterns that appear multiple times
3. Critical dependencies
4. Top recommendations based on all findings

Be comprehensive but concise."""
    
    def _create_focused_analysis_prompt(self, content: str, repo_info: RepositoryInfo) -> str:
        """Create focused analysis prompt."""
        return f"""
Analyze this {repo_info.primary_language} repository:

Repository: {repo_info.name}
Files: {repo_info.total_files}, Lines: {repo_info.total_lines}

Code:
{content[:15000]}  # Limit content for faster processing

Provide architectural analysis focusing on the most important aspects.
"""
    
    def _parse_architectural_response(self, response_content: str) -> ArchitecturalAnalysis:
        """Parse OpenAI response into ArchitecturalAnalysis object."""
        try:
            # Try to extract JSON from response
            json_start = response_content.find('{')
            json_end = response_content.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = response_content[json_start:json_end]
                data = json.loads(json_str)
            else:
                # Fallback: create structured data from text
                data = self._extract_structured_data_from_text(response_content)
            
            # Convert to ArchitecturalAnalysis object
            components = [
                ArchitecturalComponent(
                    component_name=comp.get('component_name', 'Unknown'),
                    type=comp.get('type', 'Component'),
                    responsibilities=comp.get('responsibilities', []),
                    dependencies=comp.get('dependencies', [])
                ) for comp in data.get('components', [])
            ]
            
            patterns = [
                ArchitecturalPattern(
                    pattern=pat.get('pattern', 'Unknown'),
                    description=pat.get('description', ''),
                    confidence=pat.get('confidence', 0.5)
                ) for pat in data.get('patterns', [])
            ]
            
            recommendations = [
                Recommendation(
                    title=rec.get('title', 'Recommendation'),
                    description=rec.get('description', ''),
                    priority=rec.get('priority', 'medium'),
                    impact=rec.get('impact', '')
                ) for rec in data.get('recommendations', [])
            ]
            
            return ArchitecturalAnalysis(
                overview=data.get('overview', 'Architectural analysis completed'),
                components=components,
                patterns=patterns,
                dependencies=data.get('dependencies', []),
                external_integrations=data.get('external_integrations', []),
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Error parsing architectural response: {str(e)}")
            # Return minimal analysis
            return ArchitecturalAnalysis(
                overview="Analysis completed with limited data",
                components=[],
                patterns=[],
                dependencies=[],
                external_integrations=[],
                recommendations=[]
            )
    
    async def _analyze_single_file(self, code_content: Dict, repo_info: RepositoryInfo) -> ArchitecturalAnalysis:
        """Optimized analysis for single file."""
        logger.info(f"Analyzing single file: {repo_info.name}")
        
        system_prompt = self._get_single_file_system_prompt()
        user_prompt = self._create_single_file_analysis_prompt(code_content['content'], repo_info)
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            max_tokens=2000  # Reduced for single file
        )
        
        return self._parse_architectural_response(response.choices[0].message.content)
    
    def _get_single_file_system_prompt(self) -> str:
        """System prompt optimized for single file analysis."""
        return """You are an expert code analyst. Analyze a single code file and provide architectural insights.

Focus on:
1. File structure and organization
2. Functions/procedures and their purposes
3. Data structures and variables
4. Dependencies and external calls
5. Code patterns and design approach
6. Potential improvements

Return analysis as JSON with this structure:
{
  "overview": "Brief description of what this file does",
  "components": [{"component_name": "name", "type": "function|procedure|class", "responsibilities": ["resp1"], "dependencies": []}],
  "patterns": [{"pattern": "pattern_name", "description": "brief_desc", "confidence": 0.8}],
  "dependencies": ["external_dep1"],
  "external_integrations": ["integration1"],
  "recommendations": [{"title": "title", "description": "desc", "priority": "high|medium|low", "impact": "impact"}]
}"""
    
    def _create_single_file_analysis_prompt(self, content: str, repo_info: RepositoryInfo) -> str:
        """Create analysis prompt for single file."""
        return f"""
Analyze this {repo_info.primary_language} file:

File: {repo_info.name}
Lines: {repo_info.total_lines}

Code:
{content}

Provide detailed analysis of this file's architecture, structure, and functionality.
"""
    
    def _extract_structured_data_from_text(self, text: str) -> Dict:
        """Extract structured data from text response as fallback."""
        return {
            "overview": "Architectural analysis completed",
            "components": [],
            "patterns": [],
            "dependencies": [],
            "external_integrations": [],
            "recommendations": []
        }
    
    async def generate_diagrams(self, analysis: ArchitecturalAnalysis, code_content: Dict) -> List[DiagramData]:
        """Generate Mermaid diagrams based on architectural analysis."""
        diagrams = []
        
        try:
            # Generate component diagram
            component_diagram = await self._generate_component_diagram_fast(analysis)
            if component_diagram:
                diagrams.append(component_diagram)
            
            # Generate sequence diagram if we have components
            if analysis.components:
                sequence_diagram = await self._generate_sequence_diagram_fast(analysis)
                if sequence_diagram:
                    diagrams.append(sequence_diagram)
                    
        except Exception as e:
            logger.error(f"Error generating diagrams: {str(e)}")
        
        return diagrams
    
    async def _generate_component_diagram_fast(self, analysis: ArchitecturalAnalysis) -> Optional[DiagramData]:
        """Generate component diagram using Mermaid syntax."""
        if not analysis.components:
            return None
            
        prompt = f"""
Create a Mermaid component diagram for these architectural components:

Components: {[comp.component_name for comp in analysis.components]}
Dependencies: {analysis.dependencies}

Create a simple component diagram showing relationships.
Return ONLY JSON: {{"mermaid_code": "graph TD\\n...", "description": "Component relationships"}}
"""
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a diagram generator. Return only valid JSON with mermaid_code and description."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=800
            )
            
            result = json.loads(response.choices[0].message.content)
            
            return DiagramData(
                title="System Components",
                diagram_type="component",
                mermaid_code=result.get("mermaid_code", "graph TD\nA[Component A]"),
                description=result.get("description", "System component relationships")
            )
            
        except Exception as e:
            logger.error(f"Error generating component diagram: {str(e)}")
            return None
    
    async def _generate_sequence_diagram_fast(self, analysis: ArchitecturalAnalysis) -> Optional[DiagramData]:
        """Generate sequence diagram using Mermaid syntax."""
        prompt = f"""
Create a Mermaid sequence diagram for this system:

Components: {[comp.component_name for comp in analysis.components[:4]]}  # Limit to 4 components

Create a simple sequence diagram showing main interactions.
Return ONLY JSON: {{"mermaid_code": "sequenceDiagram\\n...", "description": "Main process flow"}}
"""
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a diagram generator. Return only valid JSON with mermaid_code and description."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=800
            )
            
            result = json.loads(response.choices[0].message.content)
            
            return DiagramData(
                title="Process Flow",
                diagram_type="sequence",
                mermaid_code=result.get("mermaid_code", "sequenceDiagram\nA->>B: Process"),
                description=result.get("description", "Main system process flow")
            )
            
        except Exception as e:
            logger.error(f"Error generating sequence diagram: {str(e)}")
            return None
    
    async def generate_recommendations(self, analysis: ArchitecturalAnalysis, repo_info: RepositoryInfo) -> List[Recommendation]:
        """Generate recommendations based on architectural analysis."""
        try:
            prompt = f"""
Based on this architectural analysis, provide 3-5 key recommendations:

Repository: {repo_info.name} ({repo_info.primary_language})
Components: {len(analysis.components)}
Patterns: {[p.pattern for p in analysis.patterns]}

Focus on:
1. Architecture improvements
2. Code quality enhancements
3. Performance optimizations
4. Maintainability improvements

Return JSON array: [{{"title": "...", "description": "...", "priority": "high|medium|low", "impact": "..."}}]
"""
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an architecture consultant. Return only valid JSON array of recommendations."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1000
            )
            
            recommendations_data = json.loads(response.choices[0].message.content)
            
            recommendations = []
            for rec_data in recommendations_data:
                recommendations.append(Recommendation(
                    title=rec_data.get('title', 'Recommendation'),
                    description=rec_data.get('description', ''),
                    priority=rec_data.get('priority', 'medium'),
                    impact=rec_data.get('impact', '')
                ))
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            return []
