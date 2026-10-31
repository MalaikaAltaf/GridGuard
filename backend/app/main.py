"""
Grid-Guard AI Backend - FastAPI Application Entry Point
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, consumers, users, cases, inspections, analytics, predictions
from app.database import SessionLocal


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: train Isolation Forest if DB has enough 34-month history."""
    db = SessionLocal()
    try:
        from app.ml.inference import model_service
        model_service.init_isolation_forest(db)
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"IF init failed at startup: {e}")
    finally:
        db.close()
    yield  # app runs here
    # (shutdown logic here if needed)


# Create FastAPI application
app = FastAPI(
    title="Grid-Guard AI API",
    description="Backend API for electricity theft detection system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS configuration - allow frontend to access API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js dev server
        "http://localhost:5173",  # Vite dev server (alternative)
        "http://localhost:5174",  # Vite dev server fallback
        "https://*.vercel.app",   # Vercel deployments
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers with their prefixes and tags
app.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"]
)

app.include_router(
    consumers.router,
    prefix="/consumers",
    tags=["Consumers"]
)

app.include_router(
    users.router,
    prefix="/users",
    tags=["Users"]
)

app.include_router(
    cases.router,
    prefix="/cases",
    tags=["Cases"]
)

app.include_router(
    inspections.router,
    prefix="/cases",
    tags=["Inspections"]
)

app.include_router(
    analytics.router,
    prefix="/analytics",
    tags=["Analytics"]
)

app.include_router(
    predictions.router,
    prefix="/predictions",
    tags=["Predictions"]
)


# Health check endpoint
@app.get("/health", tags=["Health"])
def health_check():
    """
    Health check endpoint for monitoring and deployment verification.
    
    Returns:
        dict: Status message
    """
    return {
        "status": "ok",
        "service": "grid-guard-ai-backend",
        "version": "1.0.0"
    }


# Root endpoint
@app.get("/", tags=["Root"])
def root():
    """
    Root endpoint - API information.
    
    Returns:
        dict: Welcome message with documentation links
    """
    return {
        "message": "Grid-Guard AI Backend API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
