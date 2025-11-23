"""FastAPI application for AtlasAI Multi-Agent Travel Planner."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict

# Use relative import so Python resolves 'agents' inside 'backend' package
from .agents.parent_agent import handle_query

app = FastAPI(
    title="AtlasAI – Multi-Agent Travel Planner",
    description="Multi-agent system for travel planning with weather and places information",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    query: str


class QueryResponse(BaseModel):
    reply: str
    debug: Dict


@app.get("/")
async def root():
    return {
        "message": "AtlasAI – Multi-Agent Travel Planner API",
        "version": "1.0.0",
        "endpoints": {"POST /plan": "Process travel planning queries"}
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/plan", response_model=QueryResponse)
async def plan_trip(request: QueryRequest):
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    try:
        result = handle_query(request.query)
        return QueryResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


if __name__ == "__main__":
    import os
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("backend.app:app", host="0.0.0.0", port=port)


