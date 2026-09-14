import logging
from datetime import UTC, datetime

from botocore.exceptions import ClientError
from fastapi import HTTPException
from pydantic import ValidationError

from app.agent.m1 import M1Output, run_m1
from app.models.project import get_project, save_recommendation
from app.models.task import list_tasks
from app.schemas.prioritization import PrioritizationResponse

logger = logging.getLogger(__name__)


def run_agent_for_project(project: dict, tasks: list[dict]) -> M1Output:
    """Invoke M1 and translate agent/Bedrock failures into HTTP errors."""
    try:
        return run_m1(project, tasks)
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        logger.error(f"Bedrock API error: {error_code} - {e}")
        if error_code == "ThrottlingException":
            raise HTTPException(
                status_code=429,
                detail="AI service is temporarily busy. Please try again.",
            )
        if error_code == "ValidationException":
            raise HTTPException(
                status_code=400, detail="Invalid request to AI service."
            )
        raise HTTPException(status_code=502, detail="AI service unavailable.")
    except (ValidationError, ValueError) as e:
        logger.error(f"M1 response validation failed: {e}")
        raise HTTPException(
            status_code=502,
            detail="AI returned an unexpected format. Please try again.",
        )


def prioritize_project(project_id: str) -> PrioritizationResponse:
    """Run M1 prioritization for a project on demand.

    Fetches project + tasks, runs the Strands agent, persists the result on the
    project so the background watcher and UI can read it later.
    """
    project = get_project(project_id)
    tasks = list_tasks(project_id)

    active_tasks = [t for t in tasks if t.get("status") != "completed"]
    if not active_tasks:
        raise HTTPException(
            status_code=400,
            detail="No active tasks to prioritize. Add tasks or check task statuses.",
        )

    output = run_agent_for_project(project, tasks)

    response = PrioritizationResponse(
        projectId=project_id,
        recommendations=output.recommendations,
        summary=output.summary,
        needsHumanAttention=output.needsHumanAttention,
        attentionReason=output.attentionReason,
        generatedAt=datetime.now(UTC).isoformat(),
    )
    if not save_recommendation(project_id, response.model_dump()):
        raise HTTPException(status_code=404, detail="Project not found")
    return response
