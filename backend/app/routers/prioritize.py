from fastapi import APIRouter

from app.schemas.prioritization import PrioritizationResponse
from app.services.prioritization import prioritize_project

router = APIRouter(prefix="/api/projects/{project_id}", tags=["prioritization"])


@router.post("/prioritize", response_model=PrioritizationResponse)
async def prioritize(project_id: str):
    """Ask M1 to prioritize tasks for a project.

    Analyzes all active tasks using AI and returns ranked recommendations
    with explanations, Eisenhower quadrants, and confidence scores.
    """
    return prioritize_project(project_id)
