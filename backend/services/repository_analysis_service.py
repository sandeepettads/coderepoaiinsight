import os
import json
import asyncio
import logging
from typing import List, Dict, Optional, Any
from pathlib import Path
from models.schemas import RepositoryInfo
from services.openai_service import OpenAIService
from utils.analysis_cache import AnalysisCache

logger = logging.getLogger(__name__)

class RepositoryAnalysisService:
    """Service for analyzing entire repositories and generating inter-file relationships."""
    
    def __init__(self):
        self.openai_service = OpenAIService()
        self.analysis_cache = AnalysisCache(cache_dir="temp_cache/repository_analysis")
        
    async def analyze_repository_structure(self, files_data: List[Dict], repo_info: RepositoryInfo) -> Dict[str, Any]:
        """Analyze entire repository structure and generate PlantUML sequence diagram."""
        try:
            # Create cache key for entire repository
            repo_content = self._create_repo_summary(files_data)
            cache_key_info = {
                'name': f"repo_{repo_info.name}",
                'language': 'REPOSITORY',
                'strategy': 'full_repository',
                'file_count': len(files_data)
            }
            
            # Check cache first
            cached_response = self.analysis_cache.get_cached_analysis(repo_content, cache_key_info)
            if cached_response:
                logger.info(f"Using cached repository analysis for {repo_info.name}")
                return json.loads(cached_response) if isinstance(cached_response, str) else cached_response
            
            # If not cached, perform fresh analysis
            logger.info(f"Performing fresh repository analysis for {repo_info.name}")
            
            # Analyze file relationships
            relationships = await self._analyze_file_relationships(files_data, repo_info)
            
            # Generate PlantUML sequence diagram
            plantuml_diagram = await self._generate_repository_plantuml(relationships, files_data, repo_info)
            
            # Create comprehensive repository documentation
            documentation = await self._generate_repository_documentation(relationships, files_data, repo_info)
            
            result = {
                'repository_name': repo_info.name,
                'total_files': len(files_data),
                'file_relationships': relationships,
                'plantuml_diagram': plantuml_diagram,
                'documentation': documentation,
                'analysis_timestamp': self._get_current_timestamp()
            }
            
            # Cache the result
            self.analysis_cache.save_analysis(repo_content, cache_key_info, json.dumps(result))
            
            return result
            
        except Exception as e:
            logger.error(f"Error in repository analysis: {str(e)}")
            raise
    
    def _create_repo_summary(self, files_data: List[Dict]) -> str:
        """Create a summary of repository content for caching."""
        summary_parts = []
        for file_data in files_data:
            file_summary = f"{file_data.get('name', 'unknown')}:{len(file_data.get('content', ''))}"
            summary_parts.append(file_summary)
        return "|".join(summary_parts)
    
    async def _analyze_file_relationships(self, files_data: List[Dict], repo_info: RepositoryInfo) -> Dict[str, Any]:
        """Analyze relationships between files in the repository."""
        
        # Create file summaries for analysis
        file_summaries = []
        for file_data in files_data:
            content = file_data.get('content', '')
            name = file_data.get('name', 'unknown')
            
            # Extract key information from each file
            summary = {
                'name': name,
                'size': len(content),
                'type': self._detect_file_type(name, content),
                'key_elements': self._extract_key_elements(content, name)
            }
            file_summaries.append(summary)
        
        system_prompt = self._get_relationship_analysis_prompt()
        user_prompt = f"""
Analyze the relationships between these files in a {repo_info.primary_language} repository:

Repository: {repo_info.name}
Total Files: {len(files_data)}

File Summaries:
{json.dumps(file_summaries, indent=2)}

Identify:
1. Main program entry points
2. Called programs/modules
3. Data flow between files
4. Shared data structures
5. File dependencies and call hierarchy
6. Business process flow across files

Return as JSON with this structure:
{{
  "entry_points": ["main_file1.cbl", "main_file2.cbl"],
  "call_relationships": [
    {{"caller": "file1.cbl", "called": "file2.cbl", "relationship_type": "CALL|COPY|INCLUDE", "description": "..."}}
  ],
  "data_flow": [
    {{"from": "file1.cbl", "to": "file2.cbl", "data_type": "record|file|parameter", "description": "..."}}
  ],
  "shared_resources": [
    {{"resource": "CUSTOMER-RECORD", "used_by": ["file1.cbl", "file2.cbl"], "type": "copybook|data_structure"}}
  ],
  "business_processes": [
    {{"process": "Customer Processing", "files": ["file1.cbl", "file2.cbl"], "flow": "sequential|parallel"}}
  ]
}}
"""
        
        response = await self.openai_service.client.chat.completions.create(
            model=self.openai_service.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            max_tokens=3000
        )
        
        try:
            return json.loads(response.choices[0].message.content)
        except json.JSONDecodeError:
            logger.error("Failed to parse relationship analysis response")
            return {"entry_points": [], "call_relationships": [], "data_flow": [], "shared_resources": [], "business_processes": []}
    
    async def _generate_repository_plantuml(self, relationships: Dict[str, Any], files_data: List[Dict], repo_info: RepositoryInfo) -> str:
        """Generate PlantUML sequence diagram for the entire repository."""
        
        system_prompt = """You are an expert at creating PlantUML sequence diagrams for software systems. 
Create a comprehensive sequence diagram showing the flow between all files in the repository."""
        
        user_prompt = f"""
Create a PlantUML sequence diagram for this {repo_info.primary_language} repository:

Repository: {repo_info.name}
Files: {[f.get('name', 'unknown') for f in files_data]}

Relationships:
{json.dumps(relationships, indent=2)}

Create a sequence diagram that shows:
1. Main entry points as actors or participants
2. File-to-file calls and interactions
3. Data flow between components
4. Business process flow
5. External system interactions (if any)

Use proper PlantUML syntax:
- Use participant declarations
- Show activation/deactivation
- Include notes for important business logic
- Group related interactions
- Use different arrow types for different relationship types

Return ONLY the PlantUML code starting with @startuml and ending with @enduml.
"""
        
        response = await self.openai_service.client.chat.completions.create(
            model=self.openai_service.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            max_tokens=2000
        )
        
        return response.choices[0].message.content.strip()
    
    async def _generate_repository_documentation(self, relationships: Dict[str, Any], files_data: List[Dict], repo_info: RepositoryInfo) -> str:
        """Generate comprehensive repository documentation."""
        
        system_prompt = """You are a technical documentation expert. Create comprehensive repository documentation 
that explains the system architecture, file relationships, and business processes."""
        
        user_prompt = f"""
Create comprehensive documentation for this {repo_info.primary_language} repository:

Repository: {repo_info.name}
Total Files: {len(files_data)}
Files: {[f.get('name', 'unknown') for f in files_data]}

Relationships Analysis:
{json.dumps(relationships, indent=2)}

Create documentation with these sections:
1. **System Overview** - High-level description of what this system does
2. **Architecture Summary** - How files are organized and interact
3. **File Relationships** - Detailed explanation of how files call each other
4. **Data Flow** - How data moves through the system
5. **Business Processes** - Key business workflows implemented
6. **Entry Points** - Main programs and how to execute them
7. **Dependencies** - External dependencies and shared resources

Use markdown formatting with clear headings and bullet points.
"""
        
        response = await self.openai_service.client.chat.completions.create(
            model=self.openai_service.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            max_tokens=3000
        )
        
        return response.choices[0].message.content.strip()
    
    def _detect_file_type(self, filename: str, content: str) -> str:
        """Detect the type/role of a file based on name and content."""
        filename_lower = filename.lower()
        content_upper = content.upper()
        
        if filename_lower.endswith('.cbl'):
            if 'IDENTIFICATION DIVISION' in content_upper:
                if 'PROGRAM-ID' in content_upper:
                    return 'COBOL_PROGRAM'
            elif 'COPY' in content_upper or 'INCLUDE' in content_upper:
                return 'COPYBOOK'
        elif filename_lower.endswith('.cpy'):
            return 'COPYBOOK'
        elif filename_lower.endswith('.jcl'):
            return 'JCL_JOB'
        elif filename_lower.endswith('.sql'):
            return 'SQL_SCRIPT'
        
        return 'UNKNOWN'
    
    def _extract_key_elements(self, content: str, filename: str) -> List[str]:
        """Extract key elements from file content."""
        elements = []
        content_upper = content.upper()
        
        # COBOL-specific extractions
        if filename.lower().endswith('.cbl'):
            # Extract PROGRAM-ID
            if 'PROGRAM-ID.' in content_upper:
                lines = content_upper.split('\n')
                for line in lines:
                    if 'PROGRAM-ID.' in line:
                        elements.append(f"PROGRAM-ID: {line.strip()}")
                        break
            
            # Extract CALL statements
            if 'CALL ' in content_upper:
                import re
                calls = re.findall(r'CALL\s+[\'"]([^\'"]+)[\'"]', content_upper)
                for call in calls[:5]:  # Limit to first 5
                    elements.append(f"CALLS: {call}")
            
            # Extract file operations
            if 'SELECT ' in content_upper:
                import re
                selects = re.findall(r'SELECT\s+([A-Z0-9-]+)', content_upper)
                for select in selects[:3]:  # Limit to first 3
                    elements.append(f"FILE: {select}")
        
        return elements
    
    def _get_relationship_analysis_prompt(self) -> str:
        """Get system prompt for relationship analysis."""
        return """You are an expert software architect analyzing code repositories. Your task is to identify 
relationships between files, understand the system architecture, and map out how different components interact.

Focus on:
1. Program entry points and main flows
2. File dependencies (CALL, COPY, INCLUDE relationships)
3. Data sharing and parameter passing
4. Business process workflows
5. System integration points

Be precise and identify actual relationships based on the code structure and content."""
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp for analysis."""
        from datetime import datetime
        return datetime.utcnow().isoformat()
