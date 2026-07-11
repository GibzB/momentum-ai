from typing import Optional

from pydantic import BaseModel, Field


class TaskCreate(BaseModel):
    """Request schema for creating a task."""

    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    deadline: Optional[str] = Field(
        None, description="ISO 8601 date string (YYYY-MM-DD)"
    )
    status: str = Field(default="pending", pattern="^(pending|in_progress|completed)$")


class TaskUpdate(BaseModel):
    """Request schema for updating a task."""

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    deadline: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(pending|in_progress|completed)$")


class TaskResponse(BaseModel):
    """Response schema for a task."""

    taskId: str
    projectId: str
    title: str
    description: Optional[str] = None
    deadline: Optional[str] = None
    status: str
    completedAt: Optional[str] = None
    createdAt: str
    updatedAt: str


class TaskListResponse(BaseModel):
    """Response schema for listing tasks."""

    tasks: list[TaskResponse]
    count: int
