from pydantic import BaseModel, Field


class SuggestedTask(BaseModel):
    """A single AI-suggested task."""

    title: str = Field(..., description="Task title")
    description: str = Field(..., description="What this task involves")
    deadline: str | None = Field(None, description="Suggested deadline (YYYY-MM-DD)")
    reason: str = Field(..., description="Why this task is needed for the objective")
    order: int = Field(..., description="Suggested execution order")


class GenerateTasksResponse(BaseModel):
    """Response from task generation."""

    projectId: str
    suggestions: list[SuggestedTask]
    strategy: str = Field(
        ..., description="Brief explanation of the overall task breakdown strategy"
    )
    generatedAt: str


class AcceptTasksRequest(BaseModel):
    """Request to accept specific suggested tasks."""

    tasks: list[SuggestedTask]
