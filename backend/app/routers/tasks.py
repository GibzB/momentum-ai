from fastapi import APIRouter

from app.models.task import (
    create_task,
    delete_task,
    get_task,
    list_tasks,
    update_task,
)
from app.schemas.task import (
    TaskCreate,
    TaskListResponse,
    TaskResponse,
    TaskUpdate,
)

router = APIRouter(prefix="/api/projects/{project_id}/tasks", tags=["tasks"])


@router.post("", response_model=TaskResponse, status_code=201)
async def create(project_id: str, data: TaskCreate):
    """Create a new task within a project."""
    return create_task(project_id, data)


@router.get("", response_model=TaskListResponse)
async def list_all(project_id: str):
    """List all tasks for a project."""
    tasks = list_tasks(project_id)
    return TaskListResponse(tasks=tasks, count=len(tasks))


@router.get("/{task_id}", response_model=TaskResponse)
async def get_one(project_id: str, task_id: str):
    """Get a task by ID."""
    return get_task(project_id, task_id)


@router.patch("/{task_id}", response_model=TaskResponse)
async def update(project_id: str, task_id: str, data: TaskUpdate):
    """Update a task."""
    return update_task(project_id, task_id, data)


@router.delete("/{task_id}", status_code=204)
async def delete(project_id: str, task_id: str):
    """Delete a task."""
    delete_task(project_id, task_id)
