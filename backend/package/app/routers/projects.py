from fastapi import APIRouter

from app.models.project import (
    create_project,
    delete_project,
    get_project,
    list_projects,
    update_project,
)
from app.schemas.project import (
    ProjectCreate,
    ProjectListResponse,
    ProjectResponse,
    ProjectUpdate,
)

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.post("", response_model=ProjectResponse, status_code=201)
async def create(data: ProjectCreate):
    """Create a new project."""
    return create_project(data)


@router.get("", response_model=ProjectListResponse)
async def list_all():
    """List all projects."""
    projects = list_projects()
    return ProjectListResponse(projects=projects, count=len(projects))


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_one(project_id: str):
    """Get a project by ID."""
    return get_project(project_id)


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update(project_id: str, data: ProjectUpdate):
    """Update a project."""
    return update_project(project_id, data)


@router.delete("/{project_id}", status_code=204)
async def delete(project_id: str):
    """Delete a project."""
    delete_project(project_id)
