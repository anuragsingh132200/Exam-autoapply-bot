"""
Exam Automation Platform - FastAPI Main Entry Point
"""
import sys
import asyncio

# Fix Windows asyncio subprocess issue with Playwright
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.services.mongodb import Database
from app.api import exams, users, websocket, analytics, batch


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.
    Manages startup and shutdown events.
    """
    # Startup
    print("🚀 Starting Exam Automation Platform...")
    await Database.connect()
    
    yield
    
    # Shutdown
    await Database.disconnect()
    print("👋 Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Exam Automation Platform",
    description="AI-powered exam registration automation with LangGraph orchestration",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # Next.js dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(exams.router, prefix="/api/exams", tags=["Exams"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(batch.router, prefix="/api/batch", tags=["Batch"])
app.include_router(websocket.router, prefix="/ws", tags=["WebSocket"])


@app.get("/")
async def root():
    """Root endpoint - health check."""
    return {
        "status": "ok",
        "app": "Exam Automation Platform",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
