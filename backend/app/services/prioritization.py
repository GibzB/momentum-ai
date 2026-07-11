import logging
from datetime import UTC, datetime

from fastapi import HTTPException

from app.models.project import get_project
from app.models.task import list_tasks
from app.schemas.prioritization import PrioritizationResponse, PrioritizedTask
from app.services.bedrock import invoke_model

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are M1 (Momentum Intelligence), an AI prioritization engine.

Your job is to analyze a project's tasks and determine the optimal work order based on:
1. Project objective and deadline
2. Individual task deadlines
3. Task descriptions and inferred dependencies
4. Eisenhower Matrix (Urgent vs Important)
5. Previously completed work
6. Logical task sequencing

RULES:
- Assign each task a priorityScore (1-100, higher = do first)
- Assign each task an Eisenhower quadrant:
  - "urgent-important": Do first
  - "not-urgent-important": Schedule
  - "urgent-not-important": Delegate or do quickly
  - "not-urgent-not-important": Consider dropping
- Explain WHY each task has its priority in plain language
- Suggest a concrete nextAction for each task
- Identify dependencies between tasks (by taskId)
- Provide a confidence score (0.0-1.0) for each ranking
- Only prioritize tasks with status "pending" or "in_progress"
- Skip tasks with status "completed"

RESPONSE FORMAT:
Return ONLY valid JSON matching this exact structure:
{
  "recommendations": [
    {
      "taskId": "uuid",
      "title": "task title",
      "priorityScore": 85,
      "quadrant": "urgent-important",
      "reason": "explanation of why this priority",
      "nextAction": "specific next step to take",
      "dependencies": ["other-task-id"],
      "confidence": 0.85
    }
  ],
  "summary": "Brief 1-2 sentence overview of the prioritization strategy"
}

Sort recommendations by priorityScore descending (highest priority first).
Do NOT include any text outside the JSON object.
"""


def build_context_prompt(project: dict, tasks: list[dict]) -> str:
    """Build the user prompt with full project context."""
    today = datetime.now(UTC).strftime("%Y-%m-%d")

    # Separate active vs completed tasks for context
    active_tasks = [t for t in tasks if t.get("status") != "completed"]
    completed_tasks = [t for t in tasks if t.get("status") == "completed"]

    prompt = f"""Today's date: {today}

PROJECT CONTEXT:
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

    prompt += "\nPlease analyze and prioritize the active tasks."
    return prompt


def prioritize_project(project_id: str) -> PrioritizationResponse:
    """Run M1 prioritization for a project.

    Fetches project + tasks, constructs prompt, calls Bedrock,
    validates response, returns structured result.
    """
    # 1. Fetch data
    project = get_project(project_id)
    tasks = list_tasks(project_id)

    active_tasks = [t for t in tasks if t.get("status") != "completed"]
    if not active_tasks:
        raise HTTPException(
            status_code=400,
            detail="No active tasks to prioritize. Add tasks or check task statuses.",
        )

    # 2. Build prompt
    context_prompt = build_context_prompt(project, tasks)

    # 3. Call Bedrock
    raw_response = invoke_model(prompt=context_prompt, system_prompt=SYSTEM_PROMPT)

    # 4. Validate response
    try:
        recommendations = [
            PrioritizedTask(**item) for item in raw_response["recommendations"]
        ]
        summary = raw_response.get("summary", "Prioritization complete.")
    except (KeyError, TypeError) as e:
        logger.error(f"M1 response validation failed: {e}")
        raise HTTPException(
            status_code=502,
            detail="AI returned an unexpected format. Please try again.",
        )

    # 5. Return structured result
    return PrioritizationResponse(
        projectId=project_id,
        recommendations=recommendations,
        summary=summary,
        generatedAt=datetime.now(UTC).isoformat(),
    )
