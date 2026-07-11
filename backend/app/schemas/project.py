from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    """Request schema for creating a project."""

    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    deadline: Optional[str] = Field(
        None, description="ISO 8601 date string (YYYY-MM-DD)"
    )
    objective: Optional[str] = Field(None, max_length=2000)


class ProjectUpdate(BaseModel):
    """Request schema for updating a project."""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    deadline: Optional[str] = None
    objective: Optional[str] = Field(None, max_length=2000)


class ProjectResponse(BaseModel):
    """Response schema for a project."""

    projectId: str
    name: str
    description: Optional[str] = None
    deadline: Optional[str] = None
    objective: Optional[str] = None
    createdAt: str
    updatedAt: str


class ProjectListResponse(BaseModel):
    """Response schema for listing projects."""

    projects: list[ProjectResponse]
    count: int
