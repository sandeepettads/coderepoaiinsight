import os
import json
import asyncio
from typing import List, Dict, Optional
from openai import AsyncOpenAI
import logging

from models.schemas import (
    ArchitecturalAnalysis, ArchitecturalComponent, ArchitecturalPattern,
    DiagramData, Recommendation, RepositoryInfo
)

logger = logging.getLogger(__name__)

class OpenAIService:
    """Service for interacting with OpenAI GPT API for code analysis."""
    
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self.model = "gpt-4-turbo-preview"
        
    async def analyze_architecture(self, code_content: Dict, repo_info: RepositoryInfo) -> ArchitecturalAnalysis:
        """Perform architectural analysis using OpenAI GPT."""
        try:
            if code_content['strategy'] == 'single_chunk':
                return await self._analyze_single_chunk(code_content, repo_info)
            else:
                return await self._analyze_multi_chunk(code_content, repo_info)
                
        except Exception as e:
            logger.error(f"Error in architectural analysis: {str(e)}")
            raise
    
    async def _analyze_single_chunk(self, code_content: Dict, repo_info: RepositoryInfo) -> ArchitecturalAnalysis:
        """Analyze code in a single chunk."""
        system_prompt = self._get_architectural_system_prompt()
        user_prompt = self._create_analysis_prompt(code_content['content'], repo_info)
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            max_tokens=4000
        )
        
        return self._parse_architectural_response(response.choices[0].message.content)
    
    async def _analyze_multi_chunk(self, code_content: Dict, repo_info: RepositoryInfo) -> ArchitecturalAnalysis:
        """Analyze code in multiple chunks and synthesize results."""
        chunk_analyses = []
        
        # Analyze each chunk
        for i, chunk in enumerate(code_content['chunks']):
            logger.info(f"Analyzing chunk {i+1}/{len(code_content['chunks'])}")
            
            system_prompt = self._get_chunk_analysis_prompt()
            user_prompt = self._create_chunk_prompt(chunk['content'], i+1, len(code_content['chunks']))
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=2000
            )
            
            chunk_analyses.append(response.choices[0].message.content)
        
        # Synthesize all chunk analyses
        return await self._synthesize_chunk_analyses(chunk_analyses, repo_info)
    
    async def _synthesize_chunk_analyses(self, chunk_analyses: List[str], repo_info: RepositoryInfo) -> ArchitecturalAnalysis:
        """Synthesize multiple chunk analyses into a unified architectural view."""
        synthesis_prompt = self._get_synthesis_prompt()
        
        combined_analyses = "\n\n--- CHUNK ANALYSIS SEPARATOR ---\n\n".join(chunk_analyses)
        user_prompt = f"""
Repository: {repo_info.name}
Primary Language: {repo_info.primary_language}
Total Files: {repo_info.total_files}
Total Lines: {repo_info.total_lines}

Chunk Analyses to Synthesize:
{combined_analyses}

Please synthesize these chunk analyses into a unified architectural analysis.
"""
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": synthesis_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            max_tokens=4000
        )
        
        return self._parse_architectural_response(response.choices[0].message.content)
    
    async def generate_diagrams(self, analysis: ArchitecturalAnalysis, code_content: Dict) -> List[DiagramData]:
        """Generate Mermaid diagrams based on architectural analysis."""
        diagrams = []
        
        try:
            # Generate sequence diagram
            sequence_diagram = await self._generate_sequence_diagram(analysis, code_content)
            if sequence_diagram:
                diagrams.append(sequence_diagram)
            
            # Generate component diagram
            component_diagram = await self._generate_component_diagram(analysis)
            if component_diagram:
                diagrams.append(component_diagram)
            
            # Generate integration diagram if external systems detected
            if analysis.external_integrations:
                integration_diagram = await self._generate_integration_diagram(analysis)
                if integration_diagram:
                    diagrams.append(integration_diagram)
                    
        except Exception as e:
            logger.error(f"Error generating diagrams: {str(e)}")
        
        return diagrams
    
    async def _generate_sequence_diagram(self, analysis: ArchitecturalAnalysis, code_content: Dict) -> Optional[DiagramData]:
        """Generate sequence diagram using Mermaid syntax."""
        prompt = f"""
Based on this architectural analysis, create a Mermaid sequence diagram showing the main process flow:

Components: {[comp.component_name for comp in analysis.components]}
Dependencies: {analysis.dependencies}

Create a sequence diagram that shows:
1. Main user interactions
2. Component interactions
3. External system calls
4. Data flow between components

Return ONLY the Mermaid syntax starting with 'sequenceDiagram' and a brief description.
Format as JSON: {{"mermaid_code": "sequenceDiagram...", "description": "..."}}
"""
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are an expert at creating Mermaid diagrams for software architecture."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=1000
        )
        
        try:
            result = json.loads(response.choices[0].message.content)
            return DiagramData(
                title="Main Process Flow",
                mermaid_code=result["mermaid_code"],
                description=result["description"],
                diagram_type="sequence"
            )
        except:
            return None
    
    async def _generate_component_diagram(self, analysis: ArchitecturalAnalysis) -> Optional[DiagramData]:
        """Generate component diagram using Mermaid syntax."""
        prompt = f"""
Create a Mermaid component diagram showing the system architecture:

Components:
{json.dumps([{
    'name': comp.component_name,
    'type': comp.type,
    'dependencies': comp.dependencies
} for comp in analysis.components], indent=2)}

Create a graph diagram showing:
1. All components and their relationships
2. Dependencies between components
3. Component types (use different shapes/colors)

Return ONLY the Mermaid syntax starting with 'graph TD' and a brief description.
Format as JSON: {{"mermaid_code": "graph TD...", "description": "..."}}
"""
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are an expert at creating Mermaid diagrams for software architecture."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=1000
        )
        
        try:
            result = json.loads(response.choices[0].message.content)
            return DiagramData(
                title="System Components",
                mermaid_code=result["mermaid_code"],
                description=result["description"],
                diagram_type="component"
            )
        except:
            return None
    
    async def _generate_integration_diagram(self, analysis: ArchitecturalAnalysis) -> Optional[DiagramData]:
        """Generate integration diagram for external systems."""
        prompt = f"""
Create a Mermaid diagram showing external system integrations:

External Systems: {analysis.external_integrations}
Components: {[comp.component_name for comp in analysis.components]}

Create a diagram showing:
1. Internal components
2. External systems
3. Integration points
4. Data flow directions

Return ONLY the Mermaid syntax and a brief description.
Format as JSON: {{"mermaid_code": "graph LR...", "description": "..."}}
"""
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are an expert at creating Mermaid diagrams for software architecture."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=1000
        )
        
        try:
            result = json.loads(response.choices[0].message.content)
            return DiagramData(
                title="System Integrations",
                mermaid_code=result["mermaid_code"],
                description=result["description"],
                diagram_type="integration"
            )
        except:
            return None
    
    async def generate_recommendations(self, analysis: ArchitecturalAnalysis, repo_info: RepositoryInfo) -> List[Recommendation]:
        """Generate architectural recommendations."""
        prompt = f"""
Based on this architectural analysis, provide specific recommendations:

Repository: {repo_info.name} ({repo_info.primary_language})
Components: {len(analysis.components)}
Patterns: {[p.pattern for p in analysis.patterns]}

Provide 3-5 specific recommendations for:
1. Architecture improvements
2. Code organization
3. Performance optimizations
4. Maintainability enhancements
5. Security considerations

Format as JSON array: [{{"category": "...", "priority": "high/medium/low", "title": "...", "description": "...", "impact": "..."}}]
"""
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a senior software architect providing actionable recommendations."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=1500
        )
        
        try:
            recommendations_data = json.loads(response.choices[0].message.content)
            return [Recommendation(**rec) for rec in recommendations_data]
        except:
            return []
    
    def _get_architectural_system_prompt(self) -> str:
        """Get system prompt for architectural analysis."""
        return """You are an expert software architect analyzing code repositories. Your task is to provide comprehensive architectural analysis including:

1. System overview and architecture description
2. Identification of architectural components and their responsibilities
3. Detection of architectural patterns (MVC, microservices, layered, etc.)
4. Analysis of dependencies and relationships
5. Identification of external integrations

Respond with a structured JSON format:
{
  "overview": "High-level architecture description",
  "components": [
    {
      "component_name": "Name",
      "type": "business_logic|data_access|presentation|service|utility",
      "responsibilities": ["responsibility1", "responsibility2"],
      "dependencies": ["component1", "component2"],
      "file_paths": ["path1", "path2"]
    }
  ],
  "patterns": [
    {
      "pattern": "Pattern Name",
      "confidence": 0.85,
      "evidence": ["evidence1", "evidence2"],
      "description": "How this pattern is implemented"
    }
  ],
  "dependencies": ["internal dependency list"],
  "external_integrations": ["external system list"]
}

Be specific and accurate. Focus on architectural significance rather than implementation details."""
    
    def _get_chunk_analysis_prompt(self) -> str:
        """Get system prompt for chunk analysis."""
        return """You are analyzing a portion of a larger codebase. Focus on:

1. Components and modules in this chunk
2. Architectural patterns visible in this section
3. Dependencies and relationships
4. External integrations mentioned
5. Key architectural decisions

Provide a concise analysis that can be combined with other chunks. Focus on architectural elements rather than detailed code review."""
    
    def _get_synthesis_prompt(self) -> str:
        """Get system prompt for synthesizing chunk analyses."""
        return """You are synthesizing multiple architectural analyses of different parts of a codebase into a unified view.

Combine the analyses to create:
1. Complete system overview
2. Unified component list (merge similar components)
3. Overall architectural patterns
4. Complete dependency map
5. All external integrations

Ensure consistency and avoid duplication. Focus on the big picture architecture."""
    
    def _create_analysis_prompt(self, code_content: str, repo_info: RepositoryInfo) -> str:
        """Create user prompt for analysis."""
        return f"""
Analyze this {repo_info.primary_language} repository:

Repository: {repo_info.name}
Files: {repo_info.total_files}
Lines: {repo_info.total_lines}
Languages: {', '.join(repo_info.languages)}

Code Content:
{code_content}

Provide comprehensive architectural analysis focusing on system design, components, patterns, and integrations.
"""
    
    def _create_chunk_prompt(self, chunk_content: str, chunk_num: int, total_chunks: int) -> str:
        """Create prompt for chunk analysis."""
        return f"""
Analyzing chunk {chunk_num} of {total_chunks} from a larger codebase:

{chunk_content}

Focus on architectural elements in this section that contribute to the overall system design.
"""
    
    def _parse_architectural_response(self, response: str) -> ArchitecturalAnalysis:
        """Parse GPT response into ArchitecturalAnalysis object."""
        try:
            data = json.loads(response)
            
            components = [
                ArchitecturalComponent(**comp) for comp in data.get('components', [])
            ]
            
            patterns = [
                ArchitecturalPattern(**pattern) for pattern in data.get('patterns', [])
            ]
            
            return ArchitecturalAnalysis(
                overview=data.get('overview', ''),
                components=components,
                patterns=patterns,
                dependencies=data.get('dependencies', []),
                external_integrations=data.get('external_integrations', [])
            )
            
        except json.JSONDecodeError:
            # Fallback for non-JSON responses
            return ArchitecturalAnalysis(
                overview=response[:500] + "..." if len(response) > 500 else response,
                components=[],
                patterns=[],
                dependencies=[],
                external_integrations=[]
            )
