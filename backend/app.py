"""FastAPI application for AtlasAI Multi-Agent Travel Planner.

Main API endpoint: POST /plan
"""
import importlib
import os
import sys
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict

# Robust import sequence for agents.parent_agent:
# 1) Prefer relative import (works when backend is loaded as a package: "uvicorn backend.app:app")
# 2) Try absolute import as "backend.agents.parent_agent"
# 3) Add project root to sys.path and try "agents.parent_agent" (last resort)
handle_query = None
_import_errors = []

try:
    # preferred when backend is a package (uvicorn backend.app:app)
    from .agents.parent_agent import handle_query  # type: ignore
except Exception as e:
    _import_errors.append(("relative", repr(e)))
    try:
        # absolute (explicit) import
        from backend.agents.parent_agent import handle_query  # type: ignore
    except Exception as e2:
        _import_errors.append(("absolute_backend", repr(e2)))
        try:
            # last-resort: add project root to sys.path and import top-level package
            # assume this file is at <repo_root>/backend/app.py
            repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            if repo_root not in sys.path:
                sys.path.insert(0, repo_root)
            from agents.parent_agent import handle_query  # type: ignore
        except Exception as e3:
            _import_errors.append(("top_level", repr(e3)))
            # If import still fails, raise a clear error showing attempts
            details = "; ".join(f"{k}: {v}" for k, v in _import_errors)
            raise ImportError(
                "Failed to import 'agents.parent_agent'. Tried relative, backend absolute, "
                "and top-level imports. Details: " + details
            )

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
    # Useful for local debugging: run uvicorn with module path so relative imports behave.
    import uvicorn
    uvicorn.run("backend.app:app", host="0.0.0.0", port=8000, reload=True)
