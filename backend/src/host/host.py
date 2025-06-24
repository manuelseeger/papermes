import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Add backend directory to path for config import
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path))

from config import get_config  # noqa: E402

# Get configuration
config = get_config()

# Configure logging using config
logging.basicConfig(
    level=getattr(logging, config.app.log_level),
    format=config.app.log_format,
    datefmt=config.app.log_date_format
)
logger = logging.getLogger(__name__)

# FastAPI app instance
app = FastAPI(
    title="Papermes Host API",
    description="Document management and analysis API for Papermes",
    version="0.1.0"
)

# Pydantic models for request/response
class AnalysisResult(BaseModel):
    """Response model for file analysis results"""
    filename: str
    file_size: int
    content_type: str
    metadata: Dict[str, Any]
    analysis_status: str = Field(default="completed")
    analysis_results: Optional[Dict[str, Any]] = Field(default=None)

class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    detail: Optional[str] = None

@app.get("/")
async def root():
    """Root endpoint for health check"""
    return {"message": "Papermes Host API is running", "version": "0.1.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "papermes-host"}

@app.post("/analyze_file", response_model=AnalysisResult)
async def analyze_file(
    file: UploadFile = File(..., description="File to analyze"),
    metadata: str = Form(..., description="JSON string of key-value metadata pairs")
):
    """
    Analyze a file with provided metadata.
    
    Args:
        file: The file to analyze (supports various document formats)
        metadata: JSON string containing key-value pairs of metadata
    
    Returns:
        AnalysisResult: Results of the file analysis
    """
    try:
        # Validate and parse metadata
        try:
            metadata_dict = json.loads(metadata)
            if not isinstance(metadata_dict, dict):
                raise ValueError("Metadata must be a JSON object")
        except (json.JSONDecodeError, ValueError) as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid metadata format: {str(e)}"
            )
        
        # Validate file
        if not file.filename:
            raise HTTPException(
                status_code=400,
                detail="No file provided"
            )
        
        # Read file content (for processing - in real implementation)
        file_content = await file.read()
        file_size = len(file_content)
        
        logger.info(f"Analyzing file: {file.filename}, size: {file_size} bytes")
        logger.info(f"Metadata: {metadata_dict}")
        
        # TODO: Implement actual file analysis logic
        # For now, this is a stub that returns basic file information
        analysis_results = {
            "document_type": "unknown",
            "text_extracted": False,
            "confidence": 0.0,
            "processing_time_ms": 0
        }
        
        # Create response
        result = AnalysisResult(
            filename=file.filename,
            file_size=file_size,
            content_type=file.content_type or "application/octet-stream",
            metadata=metadata_dict,
            analysis_status="completed",
            analysis_results=analysis_results
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing file: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(error=exc.detail).model_dump()
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8090, reload=True)