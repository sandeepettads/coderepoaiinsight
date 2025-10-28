from fastapi import APIRouter, File, UploadFile, HTTPException, BackgroundTasks, Form
from fastapi.responses import JSONResponse
from typing import List, Optional
import uuid
import logging
from datetime import datetime

from services.cobol_analysis_service import CobolAnalysisService
from services.repository_analysis_service import RepositoryAnalysisService
from services.enhanced_analysis_service import EnhancedAnalysisService
from utils.optimized_chunker import OptimizedChunker
from utils.code_chunker import CodeChunker
from utils.file_processor import FileProcessor
from models.schemas import (
    AnalysisResponse, AnalysisRequest, AnalysisStatus, 
    RepositoryInfo, AnalysisType
)

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory storage for analysis results (replace with database in production)
analysis_storage = {}

@router.post("/analyze/architectural", response_model=AnalysisResponse)
async def analyze_architectural(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    project_name: Optional[str] = Form(None),
    include_diagrams: bool = Form(True),
    include_recommendations: bool = Form(True)
):
    """
    Analyze repository architecture using OpenAI GPT.
    Handles large files by intelligent chunking.
    """
    try:
        # Generate unique analysis ID
        analysis_id = str(uuid.uuid4())
        
        # Validate files
        if not files:
            raise HTTPException(status_code=400, detail="No files uploaded")
        
        # Initialize file processor
        file_processor = FileProcessor()
        
        # Process uploaded files
        processed_files = await file_processor.process_uploaded_files(files)
        
        if not processed_files:
            raise HTTPException(status_code=400, detail="No valid code files found")
        
        # Create repository info
        repo_info = file_processor.create_repository_info(processed_files, project_name)
        
        # Create initial analysis response
        analysis_response = AnalysisResponse(
            analysis_id=analysis_id,
            status=AnalysisStatus.PROCESSING,
            repository_info=repo_info,
            created_at=datetime.utcnow()
        )
        
        # Store initial response
        analysis_storage[analysis_id] = analysis_response
        
        # Start background analysis
        background_tasks.add_task(
            perform_architectural_analysis,
            analysis_id,
            processed_files,
            include_diagrams,
            include_recommendations
        )
        
        logger.info(f"Started architectural analysis for {analysis_id}")
        
        return analysis_response
        
    except Exception as e:
        logger.error(f"Error starting analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.get("/analysis/{analysis_id}/status", response_model=AnalysisResponse)
async def get_analysis_status(analysis_id: str):
    """Get the current status of an analysis."""
    if analysis_id not in analysis_storage:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    return analysis_storage[analysis_id]

@router.get("/analysis/{analysis_id}/results", response_model=AnalysisResponse)
async def get_analysis_results(analysis_id: str):
    """Get the complete analysis results."""
    if analysis_id not in analysis_storage:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    analysis = analysis_storage[analysis_id]
    
    if analysis.status == AnalysisStatus.PROCESSING:
        raise HTTPException(status_code=202, detail="Analysis still in progress")
    
    return analysis

async def perform_architectural_analysis(
    analysis_id: str,
    processed_files: List[dict],
    include_diagrams: bool,
    include_recommendations: bool
):
    """Background task to perform the actual architectural analysis."""
    try:
        # Update status to processing
        analysis = analysis_storage[analysis_id]
        analysis.status = AnalysisStatus.PROCESSING
        
        # Initialize enhanced analysis service
        enhanced_service = EnhancedAnalysisService()
        cobol_service = CobolAnalysisService()
        repository_service = RepositoryAnalysisService()
        optimized_chunker = OptimizedChunker()
        
        # Prepare code for analysis with optimized chunking
        code_content = optimized_chunker.prepare_code_for_analysis(processed_files)
        
        # Perform enhanced architectural analysis with all rich features
        architectural_analysis = await enhanced_service.analyze_architecture_fast(
            code_content, 
            analysis.repository_info
        )
        
        # Generate diagrams if requested (includes PlantUML sequence diagrams)
        diagrams = []
        if include_diagrams:
            diagrams = await enhanced_service.generate_diagrams(
                architectural_analysis,
                code_content
            )
        
        # Generate recommendations if requested
        recommendations = []
        if include_recommendations:
            recommendations = await enhanced_service.generate_recommendations(
                architectural_analysis,
                analysis.repository_info
            )
        
        # Update analysis with results
        analysis.architectural_analysis = architectural_analysis
        analysis.diagrams = diagrams
        analysis.recommendations = recommendations
        analysis.status = AnalysisStatus.COMPLETED
        analysis.completed_at = datetime.utcnow()
        
        # Calculate analysis duration
        duration = analysis.completed_at - analysis.created_at
        analysis.repository_info.analysis_duration = f"{duration.total_seconds():.1f}s"
        
        logger.info(f"Completed architectural analysis for {analysis_id}")
        
    except Exception as e:
        logger.error(f"Analysis failed for {analysis_id}: {str(e)}")
        
        # Update analysis with error
        analysis = analysis_storage[analysis_id]
        analysis.status = AnalysisStatus.FAILED
        analysis.error_message = str(e)
        analysis.completed_at = datetime.utcnow()

@router.post("/repository-analysis")
async def analyze_repository_structure(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    repository_name: str = Form(...),
    analysis_type: str = Form(default="documentation")
):
    """Analyze entire repository structure and generate PlantUML sequence diagram."""
    try:
        # Generate unique analysis ID
        analysis_id = str(uuid.uuid4())
        
        # Process uploaded files
        file_processor = FileProcessor()
        processed_files = await file_processor.process_uploaded_files(files)
        
        if not processed_files:
            raise HTTPException(status_code=400, detail="No valid files found for analysis")
        
        # Create repository info
        repo_info = file_processor.create_repository_info(processed_files, repository_name)
        
        # Create analysis record
        analysis = AnalysisResponse(
            analysis_id=analysis_id,
            status=AnalysisStatus.PENDING,
            repository_info=repo_info,
            analysis_type=AnalysisType.ARCHITECTURAL,
            created_at=datetime.utcnow()
        )
        
        # Store analysis
        analysis_storage[analysis_id] = analysis
        
        # Start background analysis
        background_tasks.add_task(
            perform_repository_analysis,
            analysis_id,
            processed_files,
            repo_info
        )
        
        return JSONResponse(
            status_code=202,
            content={
                "message": "Repository analysis started",
                "analysis_id": analysis_id,
                "status": "pending",
                "repository_info": {
                    "name": repo_info.name,
                    "total_files": repo_info.total_files,
                    "total_lines": repo_info.total_lines
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Error starting repository analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start repository analysis: {str(e)}")

async def perform_repository_analysis(
    analysis_id: str,
    processed_files: List[dict],
    repo_info: RepositoryInfo
):
    """Background task to perform repository-wide analysis."""
    try:
        # Update status to processing
        analysis = analysis_storage[analysis_id]
        analysis.status = AnalysisStatus.PROCESSING
        
        # Initialize repository service
        repository_service = RepositoryAnalysisService()
        
        # Perform repository analysis
        repository_result = await repository_service.analyze_repository_structure(
            processed_files, 
            repo_info
        )
        
        # Update analysis with results
        analysis.repository_analysis = repository_result
        analysis.status = AnalysisStatus.COMPLETED
        analysis.completed_at = datetime.utcnow()
        
        # Calculate analysis duration
        duration = analysis.completed_at - analysis.created_at
        analysis.repository_info.analysis_duration = f"{duration.total_seconds():.1f}s"
        
        logger.info(f"Completed repository analysis for {analysis_id}")
        
    except Exception as e:
        logger.error(f"Repository analysis failed for {analysis_id}: {str(e)}")
        
        # Update analysis with error
        analysis = analysis_storage[analysis_id]
        analysis.status = AnalysisStatus.FAILED
        analysis.error_message = str(e)
        analysis.completed_at = datetime.utcnow()
