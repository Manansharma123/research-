"""FastAPI server for Business Location Advisor."""

import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict, Any
import uvicorn

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from main import analyze_property

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Business Location Advisor API",
    description="AI-Powered Market Analysis for Opening a Business",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response models
class AnalysisRequest(BaseModel):
    query: str


class AnalysisResponse(BaseModel):
    success: bool
    data: Dict[str, Any] = {}
    error: str = ""


@app.get("/")
async def root():
    """Serve the index.html file."""
    return FileResponse("index.html")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "Business Location Advisor"}


@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze_business(request: AnalysisRequest):
    """
    Analyze business opportunity based on user query.
    
    Args:
        request: AnalysisRequest with query string
        
    Returns:
        AnalysisResponse with analysis results
    """
    try:
        logger.info(f"Received analysis request: {request.query}")
        
        if not request.query or not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        # Run analysis
        result = analyze_property(request.query)
        
        # Check for errors in result
        if "error" in result and result["error"]:
            logger.error(f"Analysis error: {result['error']}")
            return AnalysisResponse(
                success=False,
                error=result["error"]
            )
        
        # Format response
        response_data = {
            "area_name": result.get("area_name", "Unknown"),
            "city": result.get("city", "Unknown"),
            "latitude": result.get("latitude", 0.0),
            "longitude": result.get("longitude", 0.0),
            "business_type": result.get("business_type", "Unknown"),
            
            # Demographics
            "demographics": result.get("demographics", {}),
            
            # Market metrics
            "nearby_businesses": result.get("nearby_businesses", []),
            "competitors_count": len(result.get("nearby_businesses", [])),
            
            # Sentiment analysis
            "sentiment_analysis": result.get("sentiment_analysis", {}),
            
            # Scraped data
            "scraped_data": result.get("scraped_data", []),
            
            # LLM recommendations
            "llm_recommendation": result.get("llm_recommendation", {}),
            
            # Chain brands
            "chain_brands": result.get("chain_brands", []),
            
            # Amenities
            "nearby_amenities": result.get("nearby_amenities", {}),
            
            # Social validation
            "social_validation": result.get("social_validation", {}),
        }
        
        logger.info(f"Analysis completed successfully for: {request.query}")
        
        return AnalysisResponse(
            success=True,
            data=response_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during analysis: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.get("/api/status")
async def get_status():
    """Get API status and configuration."""
    return {
        "status": "running",
        "version": "1.0.0",
        "endpoints": {
            "analyze": "/api/analyze",
            "health": "/health",
            "status": "/api/status"
        }
    }


def start_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """
    Start the FastAPI server with Uvicorn.
    
    Args:
        host: Host to bind to
        port: Port to bind to
        reload: Enable auto-reload for development
    """
    logger.info(f"Starting Business Location Advisor API server on {host}:{port}")
    logger.info(f"Open http://localhost:{port} in your browser")
    
    uvicorn.run(
        "api_server:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )


if __name__ == "__main__":
    # Start server with auto-reload for development
    start_server(host="0.0.0.0", port=8000, reload=True)
