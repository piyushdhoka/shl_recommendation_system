"""
FastAPI Backend Server for SHL Assessment Recommendation System

This module provides a REST API endpoint for the recommendation engine.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from engine import get_recommendations

# Initialize FastAPI app
app = FastAPI(
    title="SHL Assessment Recommendation API",
    description="API for intelligent SHL assessment recommendations",
    version="1.0.0"
)

# Add CORS middleware to allow Streamlit frontend to access the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models for request/response
class RecommendationRequest(BaseModel):
    """Request model for recommendation endpoint."""
    query: str


class RecommendationItem(BaseModel):
    """Model for individual recommendation item."""
    assessment_name: str
    url: str  # API spec requires 'url' not 'assessment_url'
    description: str = ""
    why_great_fit: str = ""
    assessment_length: str = ""


class RecommendationResponse(BaseModel):
    """Response model for recommendation endpoint."""
    query: str
    recommendations: List[RecommendationItem]


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@app.post("/recommend", response_model=RecommendationResponse)
async def recommend(request: RecommendationRequest):
    """
    Get assessment recommendations based on user query.
    
    Args:
        request: RecommendationRequest containing the user's query
        
    Returns:
        RecommendationResponse with list of recommended assessments
    """
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    try:
        # Get recommendations from the engine
        recommendations = get_recommendations(request.query.strip())
        
        # Convert to response model - map assessment_url to url for API spec
        recommendation_items = []
        for rec in recommendations:
            # Map assessment_url to url to match API specification
            item_dict = {
                'assessment_name': rec.get('assessment_name', ''),
                'url': rec.get('assessment_url', rec.get('url', '')),
                'description': rec.get('description', ''),
                'why_great_fit': rec.get('why_great_fit', ''),
                'assessment_length': rec.get('assessment_length', '')
            }
            recommendation_items.append(RecommendationItem(**item_dict))
        
        return RecommendationResponse(
            query=request.query.strip(),
            recommendations=recommendation_items
        )
        
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

