"""FastAPI server for Business Location Advisor."""

import os
import logging
from typing import Dict, Any
import sys

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Import FastAPI components after ensuring dependencies are available
try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import FileResponse
    from pydantic import BaseModel
    import uvicorn
except ImportError as e:
    print(f"Required dependencies not installed: {e}")
    print("Please install them with: pip install fastapi uvicorn python-dotenv pydantic")
    sys.exit(1)

# Import the analyze_property function
try:
    from main import analyze_property
except ImportError as e:
    print(f"Warning: Could not import analyze_property: {e}")
    def analyze_property(business_query: str) -> Dict[str, Any]:
        # Mock implementation for testing
        return {
            "area_name": "Test Area",
            "city": "Test City",
            "latitude": 12.9716,
            "longitude": 77.5946,
            "business_type": "coffee shop",
            "nearby_businesses": [
                {"name": "Starbucks", "rating": 4.5, "reviews_count": 120},
                {"name": "Local Cafe", "rating": 4.2, "reviews_count": 85}
            ],
            "competitors_count": 2,
            "sentiment_analysis": {"average_sentiment": 78.5},
            "chain_brands": [
                {
                    "name": "Starbucks",
                    "brand": "Starbucks",
                    "is_chain": True,
                    "area_name": "MG Road",
                    "distance": 0.5,
                    "rating": 4.5,
                    "reviews_count": 128,
                    "types": "Coffee Shop",
                    "positive_percentage": 85,
                    "reviews_analyzed": 50
                }
            ],
            "nearby_amenities": {
                "schools": [
                    {"name": "Test School", "rating": 4.5, "distance": 1.2, "address": "123 Education Lane"}
                ],
                "hospitals": [
                    {"name": "Test Hospital", "rating": 4.7, "distance": 2.1, "address": "789 Health Avenue"}
                ],
                "parks": [
                    {"name": "Test Park", "rating": 4.8, "distance": 0.5, "address": "Central Area"}
                ],
                "shopping": [
                    {"name": "Test Mall", "rating": 4.5, "distance": 4.5, "address": "Shopping District"}
                ]
            },
            "llm_recommendation": {
                "pros": ["High foot traffic area", "Growing coffee culture"],
                "cons": ["High rental costs", "Established competition"],
                "suggestions": ["Focus on unique brewing methods", "Implement loyalty program"],
                "recommendation": "This location shows strong potential for a specialty coffee shop."
            }
        }

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
    """Serve the business_advisor.html file."""
    return FileResponse("business_advisor.html")


@app.get("/test")
async def test_page():
    """Serve the test API page."""
    return FileResponse("test_api.html")


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
        
        # Run analysis - adapt parameter name
        result = analyze_property(business_query=request.query)
        
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
            
            # Market metrics
            "nearby_businesses": result.get("nearby_businesses", []),
            "competitors_count": len(result.get("nearby_businesses", [])),
            
            # Sentiment analysis
            "sentiment_analysis": result.get("sentiment_analysis", {}),
            
            # Chain brands
            "chain_brands": result.get("chain_brands", []),
            
            # Amenities
            "nearby_amenities": result.get("nearby_amenities", {}),
            
            # LLM recommendations
            "llm_recommendation": result.get("llm_recommendation", {}),
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


def start_server(host: str = "0.0.0.0", port: int = 8001, reload: bool = False):
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
    start_server(host="0.0.0.0", port=8001, reload=True)