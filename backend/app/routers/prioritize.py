from fastapi import APIRouter, HTTPException

from app.models.project import get_project
from app.schemas.prioritization import PrioritizationResponse
from app.services.prioritization import prioritize_project

router = APIRouter(prefix="/api/projects/{project_id}", tags=["prioritization"])


@router.post("/prioritize", response_model=PrioritizationResponse)
async def prioritize(project_id: str):
    """Ask M1 to prioritize tasks for a project right now.

    Runs the Strands agent and returns ranked recommendations with
    explanations, Eisenhower quadrants, and confidence scores.
    """
    return prioritize_project(project_id)


@router.get("/recommendations", response_model=PrioritizationResponse)
async def latest_recommendation(project_id: str):
    """Return the most recent M1 recommendation.

    Written either by an on-demand `/prioritize` call or by the background
    watcher agent on its schedule.
    """
    project = get_project(project_id)
    recommendation = project.get("lastRecommendation")
    if not recommendation:
        raise HTTPException(
            status_code=404,
            detail="No recommendation yet. Run /prioritize or wait for the watcher.",
        )
    return recommendation
