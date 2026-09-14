"""Background watcher — the "runs quietly, surfaces only when needed" half of M1.

Triggered on a schedule (EventBridge -> Lambda). For every project with active
tasks it re-runs the M1 agent, stores the fresh recommendation, and publishes an
SNS notification ONLY when the agent decides a human needs to weigh in.

Alert state lives in `project.lastAlert` and is claimed with a conditional
DynamoDB update before publishing, so concurrent sweeps cannot double-send and a
failed publish is retried on the next sweep (the claim is only marked delivered
after SNS accepts the message).
"""

import logging
from datetime import UTC, datetime

import boto3

from app.agent.m1 import run_m1
from app.core.config import settings
from app.models.project import (
    claim_alert,
    clear_alert,
    list_projects,
    mark_alert_delivered,
    save_recommendation,
)
from app.models.task import list_tasks
from app.schemas.prioritization import PrioritizationResponse

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def notify(project: dict, response: PrioritizationResponse) -> bool:
    """Send a human-facing alert. Returns True once SNS accepted the message."""
    if not settings.alerts_topic_arn:
        logger.warning("ALERTS_TOPIC_ARN not set; skipping notification")
        return False

    top = response.recommendations[:3]
    lines = [
        f"Project: {project.get('name')}",
        f"Why now: {response.attentionReason or response.summary}",
        "",
        "Top priorities:",
    ]
    lines += [f"  {i + 1}. {t.title} — {t.nextAction}" for i, t in enumerate(top)]

    boto3.client("sns", region_name=settings.aws_region).publish(
        TopicArn=settings.alerts_topic_arn,
        Subject=f"[Momentum] {project.get('name')} needs your attention",
        Message="\n".join(lines),
    )
    return True


def maybe_alert(project: dict, response: PrioritizationResponse) -> bool:
    """Alert once per distinct attention reason; retry until delivered."""
    project_id = project["projectId"]
    if not response.needsHumanAttention:
        clear_alert(project_id)
        return False
    reason = response.attentionReason or response.summary
    if not claim_alert(project_id, reason):
        return False
    if notify(project, response):
        mark_alert_delivered(project_id, reason)
        return True
    return False


def watch_project(project: dict) -> tuple[PrioritizationResponse, bool] | None:
    """Re-prioritize one project.

    Returns (response, alerted), or None when there is nothing to do.
    """
    project_id = project["projectId"]
    tasks = list_tasks(project_id)
    if not any(t.get("status") != "completed" for t in tasks):
        return None

    output = run_m1(project, tasks)
    response = PrioritizationResponse(
        projectId=project_id,
        recommendations=output.recommendations,
        summary=output.summary,
        needsHumanAttention=output.needsHumanAttention,
        attentionReason=output.attentionReason,
        generatedAt=datetime.now(UTC).isoformat(),
    )
    if not save_recommendation(project_id, response.model_dump()):
        logger.info("project=%s deleted during sweep; skipping", project_id)
        return None

    return response, maybe_alert(project, response)


def run_watch() -> dict:
    """Sweep every project. Safe to call repeatedly."""
    checked = alerted = failed = 0
    for project in list_projects():
        try:
            result = watch_project(project)
        except Exception:
            failed += 1
            logger.exception("watcher failed for project %s", project.get("projectId"))
            continue
        if result is None:
            continue
        checked += 1
        alerted += int(result[1])

    summary = {"checked": checked, "alerted": alerted, "failed": failed}
    logger.info("watcher sweep complete %s", summary)
    return summary


def handler(event, context):
    """AWS Lambda entrypoint for the scheduled sweep."""
    return run_watch()
