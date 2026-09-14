import uuid
from datetime import UTC, datetime
from decimal import Decimal

from botocore.exceptions import ClientError
from fastapi import HTTPException

from app.schemas.project import ProjectCreate, ProjectUpdate
from app.services.dynamodb import get_projects_table


def create_project(data: ProjectCreate) -> dict:
    """Create a new project in DynamoDB."""
    table = get_projects_table()
    now = datetime.now(UTC).isoformat()

    item = {
        "projectId": str(uuid.uuid4()),
        "name": data.name,
        "createdAt": now,
        "updatedAt": now,
    }

    if data.description is not None:
        item["description"] = data.description
    if data.deadline is not None:
        item["deadline"] = data.deadline
    if data.objective is not None:
        item["objective"] = data.objective

    table.put_item(Item=item)
    return item


def get_project(project_id: str) -> dict:
    """Get a single project by ID."""
    table = get_projects_table()

    response = table.get_item(Key={"projectId": project_id})
    item = response.get("Item")

    if not item:
        raise HTTPException(status_code=404, detail="Project not found")

    return item


def list_projects() -> list[dict]:
    """List all projects."""
    table = get_projects_table()
    items: list[dict] = []
    kwargs: dict = {}
    while True:
        response = table.scan(**kwargs)
        items.extend(response.get("Items", []))
        last_key = response.get("LastEvaluatedKey")
        if not last_key:
            return items
        kwargs["ExclusiveStartKey"] = last_key


def _conditional_update(project_id: str, **kwargs) -> bool:
    """Run an UpdateItem that must never create the item. False if condition failed."""
    try:
        get_projects_table().update_item(Key={"projectId": project_id}, **kwargs)
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return False
        raise
    return True


def save_recommendation(project_id: str, recommendation: dict) -> bool:
    """Persist the latest M1 recommendation on the project item.

    Returns False if the project no longer exists (never recreates it).
    """
    return _conditional_update(
        project_id,
        UpdateExpression="SET lastRecommendation = :r",
        ConditionExpression="attribute_exists(projectId)",
        ExpressionAttributeValues={":r": _to_dynamo(recommendation)},
    )


def claim_alert(project_id: str, reason: str) -> bool:
    """Atomically claim the right to send an alert for `reason`.

    Succeeds when no alert for this reason has been claimed yet, or when a
    previous claim was never marked delivered (so failed sends are retried).
    Concurrent sweeps race on this update and only one wins.
    """
    return _conditional_update(
        project_id,
        UpdateExpression="SET lastAlert = :a",
        ConditionExpression=(
            "attribute_exists(projectId) AND ("
            "attribute_not_exists(lastAlert) OR lastAlert.reason <> :r "
            "OR lastAlert.delivered = :f)"
        ),
        ExpressionAttributeValues={
            ":a": {
                "reason": reason,
                "delivered": False,
                "claimedAt": datetime.now(UTC).isoformat(),
            },
            ":r": reason,
            ":f": False,
        },
    )


def mark_alert_delivered(project_id: str, reason: str) -> bool:
    """Record that the alert for `reason` reached the notification channel."""
    return _conditional_update(
        project_id,
        UpdateExpression="SET lastAlert.delivered = :t, lastAlert.sentAt = :now",
        ConditionExpression="attribute_exists(projectId) AND lastAlert.reason = :r",
        ExpressionAttributeValues={
            ":t": True,
            ":now": datetime.now(UTC).isoformat(),
            ":r": reason,
        },
    )


def clear_alert(project_id: str) -> None:
    """Forget the alert state once the project is healthy again."""
    _conditional_update(
        project_id,
        UpdateExpression="REMOVE lastAlert",
        ConditionExpression=(
            "attribute_exists(projectId) AND attribute_exists(lastAlert)"
        ),
    )


def _to_dynamo(value):
    """DynamoDB rejects floats; store them as Decimal."""
    if isinstance(value, float):
        return Decimal(str(value))
    if isinstance(value, dict):
        return {k: _to_dynamo(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_to_dynamo(v) for v in value]
    return value


def update_project(project_id: str, data: ProjectUpdate) -> dict:
    """Update an existing project."""
    # Verify exists
    get_project(project_id)

    table = get_projects_table()
    now = datetime.now(UTC).isoformat()

    update_fields = data.model_dump(exclude_unset=True)
    if not update_fields:
        raise HTTPException(status_code=400, detail="No fields to update")

    update_fields["updatedAt"] = now

    # Build update expression
    expressions = []
    attr_names = {}
    attr_values = {}

    for i, (key, value) in enumerate(update_fields.items()):
        expressions.append(f"#k{i} = :v{i}")
        attr_names[f"#k{i}"] = key
        attr_values[f":v{i}"] = value

    response = table.update_item(
        Key={"projectId": project_id},
        UpdateExpression="SET " + ", ".join(expressions),
        ExpressionAttributeNames=attr_names,
        ExpressionAttributeValues=attr_values,
        ReturnValues="ALL_NEW",
    )

    return response["Attributes"]


def delete_project(project_id: str) -> None:
    """Delete a project by ID."""
    # Verify exists
    get_project(project_id)

    table = get_projects_table()
    table.delete_item(Key={"projectId": project_id})
