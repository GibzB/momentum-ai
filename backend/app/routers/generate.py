from fastapi import APIRouter

from app.models.task import create_task
from app.schemas.generate import AcceptTasksRequest, GenerateTasksResponse
from app.schemas.task import TaskCreate, TaskListResponse
from app.services.task_generation import generate_tasks_for_project

router = APIRouter(prefix="/api/projects/{project_id}", tags=["generate"])


@router.post("/generate-tasks", response_model=GenerateTasksResponse)
async def generate(project_id: str):
    """Ask M1 to generate tasks for a project based on its objective.

    Analyzes the project objective, deadline, and description to produce
    a set of suggested tasks with reasoning.
    """
    return generate_tasks_for_project(project_id)


@router.post("/accept-tasks", response_model=TaskListResponse, status_code=201)
async def accept(project_id: str, data: AcceptTasksRequest):
    """Accept suggested tasks and create them in the project."""
    created = []
    for suggestion in data.tasks:
        task_data = TaskCreate(
            title=suggestion.title,
            description=f"{suggestion.description}\n\nReason: {suggestion.reason}",
            deadline=suggestion.deadline,
        )
        item = create_task(project_id, task_data)
        created.append(item)

    return TaskListResponse(tasks=created, count=len(created))
