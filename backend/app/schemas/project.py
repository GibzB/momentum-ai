from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    """Request schema for creating a project."""

    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None, max_length=2000)
    deadline: str | None = Field(None, description="ISO 8601 date string (YYYY-MM-DD)")
    objective: str | None = Field(None, max_length=2000)


class ProjectUpdate(BaseModel):
    """Request schema for updating a project."""

    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=2000)
    deadline: str | None = None
    objective: str | None = Field(None, max_length=2000)


class ProjectResponse(BaseModel):
    """Response schema for a project."""

    projectId: str
    name: str
    description: str | None = None
    deadline: str | None = None
    objective: str | None = None
    createdAt: str
    updatedAt: str


class ProjectListResponse(BaseModel):
    """Response schema for listing projects."""

    projects: list[ProjectResponse]
    count: int
