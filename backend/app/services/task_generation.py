import logging
from datetime import UTC, datetime

from fastapi import HTTPException

from app.models.project import get_project
from app.models.task import list_tasks
from app.schemas.generate import GenerateTasksResponse, SuggestedTask
from app.services.bedrock import invoke_model

logger = logging.getLogger(__name__)

GENERATE_SYSTEM_PROMPT = """\
You are M1 (Momentum Intelligence), an AI task generation engine.

Given a project's objective, description, deadline, and any existing tasks, you generate
a comprehensive set of tasks needed to achieve the objective within the timeframe.

RULES:
- Break the objective into concrete, actionable tasks
- Order tasks logically (dependencies first)
- Distribute deadlines realistically across the available time
- Each task must have a clear reason explaining why it's essential
- Don't duplicate existing tasks
- Keep tasks specific and measurable (not vague)
- Aim for 5-12 tasks depending on project complexity
- If no deadline is set, suggest reasonable relative timelines

RESPONSE FORMAT:
Return ONLY valid JSON matching this structure:
{
  "suggestions": [
    {
      "title": "Clear task title",
      "description": "What this involves in 1-2 sentences",
      "deadline": "YYYY-MM-DD or null",
      "reason": "Why this task is needed to achieve the objective",
      "order": 1
    }
  ],
  "strategy": "Brief 1-2 sentence explanation of how you broke down this project"
}

Sort by order (execution sequence).
Do NOT include any text outside the JSON object.
"""


def build_generation_prompt(project: dict, existing_tasks: list[dict]) -> str:
    """Build prompt for task generation."""
    today = datetime.now(UTC).strftime("%Y-%m-%d")

    prompt = f"""Today's date: {today}

PROJECT:
- Name: {project.get("name")}
- Objective: {project.get("objective", "Not specified")}
- Deadline: {project.get("deadline", "No deadline set")}
- Description: {project.get("description", "No description")}

"""

    if existing_tasks:
        prompt += f"EXISTING TASKS ({len(existing_tasks)}) — do not duplicate:\n"
        for t in existing_tasks:
            prompt += f'- "{t["title"]}" ({t.get("status", "pending")})\n'
        prompt += "\n"

    prompt += (
        "Generate tasks needed to achieve this project's objective "
        "within the given timeframe."
    )
    return prompt


def generate_tasks_for_project(project_id: str) -> GenerateTasksResponse:
    """Generate task suggestions for a project using M1."""
    project = get_project(project_id)
    existing = list_tasks(project_id)

    if not project.get("objective") and not project.get("description"):
        raise HTTPException(
            status_code=400,
            detail=(
                "Project needs an objective or description for M1 to generate tasks."
            ),
        )

    prompt = build_generation_prompt(project, existing)
    raw = invoke_model(prompt=prompt, system_prompt=GENERATE_SYSTEM_PROMPT)

    try:
        suggestions = [SuggestedTask(**item) for item in raw["suggestions"]]
        strategy = raw.get("strategy", "Tasks generated based on project objective.")
    except (KeyError, TypeError) as e:
        logger.error(f"Task generation response invalid: {e}")
        raise HTTPException(
            status_code=502,
            detail="AI returned an unexpected format. Please try again.",
        )

    return GenerateTasksResponse(
        projectId=project_id,
        suggestions=suggestions,
        strategy=strategy,
        generatedAt=datetime.now(UTC).isoformat(),
    )
