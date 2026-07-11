from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from app.core.config import settings
from app.routers import projects, tasks, prioritize

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# CORS — permissive for local dev, lock down in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint for load balancers and monitoring."""
    return {"status": "healthy", "service": settings.app_name, "version": "0.1.0"}


# Register routers
app.include_router(projects.router)
app.include_router(tasks.router)
app.include_router(prioritize.router)


# Lambda handler via Mangum
handler = Mangum(app, lifespan="off")
