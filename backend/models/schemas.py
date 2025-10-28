from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class AnalysisType(str, Enum):
    ARCHITECTURAL = "architectural"
    CODE_QUALITY = "code_quality"
    DOCUMENTATION = "documentation"
    BUSINESS_LOGIC = "business_logic"
    SECURITY = "security"
    TESTING = "testing"

class AnalysisStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class FileInfo(BaseModel):
    name: str
    path: str
    size: int
    language: str
    lines: int

class RepositoryInfo(BaseModel):
    name: str
    total_files: int
    total_lines: int
    total_size: int
    primary_language: str
    languages: List[str]
    analysis_duration: Optional[str] = None

class ArchitecturalComponent(BaseModel):
    component_name: str
    type: str
    responsibilities: List[str]
    dependencies: List[str]
    file_paths: List[str]

class DiagramData(BaseModel):
    title: str
    mermaid_code: str
    description: str
    diagram_type: str

class ArchitecturalPattern(BaseModel):
    pattern: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: List[str]
    description: str

class Recommendation(BaseModel):
    category: str
    priority: str
    title: str
    description: str
    impact: str

class ArchitecturalAnalysis(BaseModel):
    overview: str
    components: List[ArchitecturalComponent]
    patterns: List[ArchitecturalPattern]
    dependencies: List[str]
    external_integrations: List[str]

class AnalysisResponse(BaseModel):
    analysis_id: str
    status: AnalysisStatus
    repository_info: RepositoryInfo
    architectural_analysis: Optional[ArchitecturalAnalysis] = None
    diagrams: List[DiagramData] = []
    recommendations: Optional[List[Recommendation]] = None
    repository_analysis: Optional[Dict] = None
    insights: List[str] = []
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

class AnalysisRequest(BaseModel):
    analysis_type: AnalysisType = AnalysisType.ARCHITECTURAL
    project_name: Optional[str] = None
    include_diagrams: bool = True
    include_recommendations: bool = True
