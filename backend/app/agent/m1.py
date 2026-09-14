"""M1 (Momentum Intelligence) agent definition.

One Strands `Agent` backed by Amazon Bedrock. It reasons over a project's
context with a small toolbox and returns a validated `M1Output`.
"""

import logging
from datetime import UTC, datetime

from pydantic import BaseModel, Field
from strands import Agent
from strands.models import BedrockModel

from app.agent.tools import days_until, eisenhower_quadrant, get_project_tasks
from app.core.config import settings
from app.schemas.prioritization import PrioritizedTask

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are M1 (Momentum Intelligence), an autonomous prioritization
agent.

Your job is to decide the optimal work order for a project's active tasks based on:
1. Project objective and deadline
2. Individual task deadlines (use the days_until tool — never guess dates)
3. Task descriptions and inferred dependencies
4. Eisenhower Matrix (use the eisenhower_quadrant tool for consistency)
5. Previously completed work
6. Logical task sequencing

RULES:
- Call get_project_tasks first if you were not given the task list.
- Assign each active task a priorityScore (1-100, higher = do first).
- Assign each task an Eisenhower quadrant:
  - "urgent-important": Do first
  - "not-urgent-important": Schedule
  - "urgent-not-important": Delegate or do quickly
  - "not-urgent-not-important": Consider dropping
- Explain WHY each task has its priority in plain language (the reason field).
- Suggest one concrete nextAction per task.
- Identify dependencies between tasks by taskId.
- Provide a confidence score (0.0-1.0) per ranking.
- Only prioritize tasks with status "pending" or "in_progress"; skip "completed".
- Set needsHumanAttention=true ONLY when a deadline is overdue or at real risk
  (critical pressure with the task not yet started). Otherwise keep it false so
  the human is not interrupted.
- Sort recommendations by priorityScore descending.
"""


class M1Output(BaseModel):
    """Structured result the agent must produce."""

    recommendations: list[PrioritizedTask]
    summary: str = Field(..., description="1-2 sentence prioritization strategy")
    needsHumanAttention: bool = Field(
        default=False,
        description="True only if a deadline is overdue or at real risk",
    )
    attentionReason: str | None = Field(
        default=None, description="Why a human should look at this project now"
    )


def build_context_prompt(project: dict, tasks: list[dict]) -> str:
    """Build the user prompt with full project context."""
    today = datetime.now(UTC).strftime("%Y-%m-%d")

    active_tasks = [t for t in tasks if t.get("status") != "completed"]
    completed_tasks = [t for t in tasks if t.get("status") == "completed"]

    prompt = f"""Today's date: {today}

PROJECT CONTEXT:
- projectId: {project.get("projectId")}
- Name: {project.get("name")}
- Objective: {project.get("objective", "Not specified")}
- Deadline: {project.get("deadline", "No deadline set")}
- Description: {project.get("description", "No description")}

COMPLETED TASKS ({len(completed_tasks)}):
"""

    for t in completed_tasks:
        completed_at = t.get("completedAt", "unknown")
        prompt += f'- [{t["taskId"][:8]}] "{t["title"]}" (completed {completed_at})\n'

    prompt += f"\nACTIVE TASKS TO PRIORITIZE ({len(active_tasks)}):\n"

    for t in active_tasks:
        prompt += f'- taskId: "{t["taskId"]}"\n'
        prompt += f'  title: "{t["title"]}"\n'
        prompt += f"  status: {t.get('status', 'pending')}\n"
        prompt += f"  description: {t.get('description', 'None')}\n"
        prompt += f"  deadline: {t.get('deadline', 'No deadline')}\n\n"

    if not active_tasks:
        prompt += "(No active tasks to prioritize)\n"

    prompt += "\nAnalyze and prioritize the active tasks."
    return prompt


def create_m1_agent() -> Agent:
    """Instantiate the M1 Strands agent."""
    model = BedrockModel(
        model_id=settings.bedrock_model_id,
        region_name=settings.aws_region,
        temperature=0.2,
        top_p=0.9,
        max_tokens=4096,
    )
    return Agent(
        name="M1",
        description="Momentum Intelligence — project prioritization agent",
        model=model,
        system_prompt=SYSTEM_PROMPT,
        tools=[get_project_tasks, days_until, eisenhower_quadrant],
        callback_handler=None,
    )


def run_m1(project: dict, tasks: list[dict]) -> M1Output:
    """Run the agent for one project and return validated structured output."""
    agent = create_m1_agent()
    prompt = build_context_prompt(project, tasks)
    result = agent(prompt, structured_output_model=M1Output)

    output = result.structured_output
    if not isinstance(output, M1Output):
        raise ValueError("M1 did not return structured output")

    logger.info(
        "M1 finished project=%s stop=%s tokens=%s",
        project.get("projectId"),
        result.stop_reason,
        result.metrics.accumulated_usage,
    )
    return output
