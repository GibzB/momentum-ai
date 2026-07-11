from typing import Optional

from pydantic import BaseModel, Field


class PrioritizedTask(BaseModel):
    """A single task with M1 prioritization data."""

    taskId: str
    title: str
    priorityScore: int = Field(..., ge=1, le=100, description="1-100 priority score")
    quadrant: str = Field(
        ...,
        pattern="^(urgent-important|urgent-not-important|not-urgent-important|not-urgent-not-important)$",
        description="Eisenhower matrix quadrant",
    )
    reason: str = Field(..., description="Why this task has this priority")
    nextAction: str = Field(..., description="Recommended immediate next step")
    dependencies: list[str] = Field(
        default_factory=list, description="Task IDs this depends on"
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Model confidence in this ranking"
    )


class PrioritizationResponse(BaseModel):
    """Full M1 prioritization response."""

    projectId: str
    recommendations: list[PrioritizedTask]
    summary: str = Field(..., description="Brief overview of prioritization reasoning")
    generatedAt: str


class PrioritizationError(BaseModel):
    """Error response when prioritization fails."""

    detail: str
    code: str
