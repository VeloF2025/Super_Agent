"""
Jarvis Super Agent API
Main entry point for the FastAPI application.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, Any, List
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Import ML optimization components if available
try:
    from memory.context.jarvis.ml_optimization_integration import create_ml_optimized_app
    ML_ENABLED = True
except ImportError:
    ML_ENABLED = False

# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting Jarvis Super Agent API...")
    
    # Initialize directories
    for directory in ['data', 'logs', 'memory/context/jarvis', 'projects']:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    yield
    
    # Shutdown
    print("👋 Shutting down Jarvis Super Agent API...")

# Create FastAPI app
if ML_ENABLED:
    app, ml_orchestrator = create_ml_optimized_app()
else:
    app = FastAPI(
        title="Jarvis Super Agent API",
        description="AI-powered multi-agent orchestration system",
        version="2.0.0",
        lifespan=lifespan
    )

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "ml_enabled": ML_ENABLED,
        "version": "2.0.0"
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with system information."""
    return {
        "name": "Jarvis Super Agent System",
        "version": "2.0.0",
        "status": "running",
        "features": {
            "ml_optimization": ML_ENABLED,
            "context_persistence": True,
            "collaborative_learning": ML_ENABLED,
            "crash_recovery": True
        },
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "dashboard": "http://localhost:3000"
        }
    }

# Agent endpoints
@app.get("/api/agents/status")
async def get_agents_status():
    """Get status of all agents."""
    # Mock data for now
    agents = [
        {
            "id": "agent-orchestrator-001",
            "name": "Orchestrator Prime",
            "type": "orchestrator",
            "status": "online",
            "health": 100,
            "current_task": None
        },
        {
            "id": "agent-architect-001",
            "name": "System Architect",
            "type": "architect",
            "status": "online",
            "health": 100,
            "current_task": None
        },
        {
            "id": "agent-researcher-001",
            "name": "Research Specialist",
            "type": "researcher",
            "status": "online",
            "health": 100,
            "current_task": None
        },
        {
            "id": "agent-quality-001",
            "name": "Quality Guardian",
            "type": "quality",
            "status": "online",
            "health": 100,
            "current_task": None
        },
        {
            "id": "agent-communicator-001",
            "name": "Communication Hub",
            "type": "communicator",
            "status": "online",
            "health": 100,
            "current_task": None
        }
    ]
    
    return {"agents": agents, "total": len(agents), "online": len(agents)}

# Task endpoints
@app.post("/api/tasks")
async def create_task(task: Dict[str, Any]):
    """Create a new task."""
    task_id = f"task-{int(datetime.now().timestamp())}"
    
    new_task = {
        "id": task_id,
        "description": task.get("description", ""),
        "project_id": task.get("project_id", "default"),
        "status": "pending",
        "created": datetime.now().isoformat(),
        "assigned_to": None
    }
    
    # If ML is enabled, use ML optimization for assignment
    if ML_ENABLED and ml_orchestrator:
        try:
            assignment = await ml_orchestrator.assign_task_optimized(new_task)
            new_task["assigned_to"] = assignment.get("assigned_to", [])
            new_task["ml_optimized"] = True
        except:
            pass
    
    return {"status": "success", "task": new_task}

@app.get("/api/tasks")
async def get_tasks():
    """Get all tasks."""
    # Mock data for now
    return {
        "tasks": [],
        "total": 0,
        "pending": 0,
        "in_progress": 0,
        "completed": 0
    }

# Dashboard data endpoint
@app.get("/api/dashboard")
async def get_dashboard_data():
    """Get dashboard data."""
    agents_status = await get_agents_status()
    
    return {
        "metrics": {
            "totalAgents": len(agents_status["agents"]),
            "activeAgents": agents_status["online"],
            "completedTasks": 0,
            "avgResponseTime": 0.0,
            "systemUptime": 0,
            "messagesProcessed": 0
        },
        "agents": agents_status["agents"],
        "activities": [],
        "performance": []
    }

# Project endpoints
@app.get("/api/projects")
async def get_projects():
    """Get all projects."""
    projects = []
    
    # Check projects directory
    projects_dir = Path("projects")
    if projects_dir.exists():
        for project_path in projects_dir.iterdir():
            if project_path.is_dir():
                project_json = project_path / "project.json"
                if project_json.exists():
                    try:
                        import json
                        with open(project_json) as f:
                            project_data = json.load(f)
                            projects.append(project_data)
                    except:
                        pass
    
    return {"projects": projects, "total": len(projects)}

# Activities endpoint
@app.get("/api/activities")
async def get_activities():
    """Get recent activities."""
    return {"activities": [], "total": 0}

# Error handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "status_code": exc.status_code}
    )

# General exception handler
@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("API_PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port, reload=True)