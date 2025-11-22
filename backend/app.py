"""FastAPI application for AtlasAI Multi-Agent Travel Planner.

Main API endpoint: POST /plan
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict

from agents.parent_agent import handle_query

# Initialize FastAPI app
app = FastAPI(
    title="AtlasAI – Multi-Agent Travel Planner",
    description="Multi-agent system for travel planning with weather and places information",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    """Request model for /plan endpoint."""
    query: str


class QueryResponse(BaseModel):
    """Response model for /plan endpoint."""
    reply: str
    debug: Dict


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "AtlasAI – Multi-Agent Travel Planner API",
        "version": "1.0.0",
        "endpoints": {
            "POST /plan": "Process travel planning queries"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/plan", response_model=QueryResponse)
async def plan_trip(request: QueryRequest):
    """
    Main endpoint for processing travel planning queries.
    
    Accepts a user query and returns a formatted response with weather
    and/or places information based on detected intent.
    
    Args:
        request: QueryRequest with user query text
        
    Returns:
        QueryResponse with reply text and debug information
        
    Example:
        Request:
        {
            "query": "I'm going to Bangalore. What's the weather like?"
        }
        
        Response:
        {
            "reply": "In Bangalore it's currently 28°C with a chance of 30% to rain.",
            "debug": {...}
        }
    """
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    try:
        result = handle_query(request.query)
        return QueryResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

