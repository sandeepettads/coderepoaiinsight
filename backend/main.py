from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional
import os
import uuid
import logging
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from api.routes import analysis, cache, chat
from services.openai_service import OpenAIService
from utils.file_processor import FileProcessor
from models.schemas import AnalysisResponse, AnalysisStatus

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="RepoInsight AI Backend",
    description="Backend API for repository architectural analysis",
    version="1.0.0"
)

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(analysis.router, prefix="/api", tags=["analysis"])
app.include_router(cache.router, prefix="/api", tags=["cache"])
app.include_router(chat.router, prefix="/api", tags=["chat"])

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "RepoInsight AI Backend"
    }

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "RepoInsight AI Backend API",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
