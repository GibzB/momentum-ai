import uuid
from datetime import datetime, timezone
from typing import Optional

from boto3.dynamodb.conditions import Key
from fastapi import HTTPException

from app.schemas.task import TaskCreate, TaskUpdate
from app.services.dynamodb import get_tasks_table


def create_task(project_id: str, data: TaskCreate) -> dict:
    """Create a new task within a project."""
    table = get_tasks_table()
    now = datetime.now(timezone.utc).isoformat()

    item = {
        "taskId": str(uuid.uuid4()),
        "projectId": project_id,
        "title": data.title,
        "status": data.status,
        "createdAt": now,
        "updatedAt": now,
    }

    if data.description is not None:
        item["description"] = data.description
    if data.deadline is not None:
        item["deadline"] = data.deadline

    table.put_item(Item=item)
    return item


def get_task(project_id: str, task_id: str) -> dict:
    """Get a single task by project ID and task ID."""
    table = get_tasks_table()

    response = table.get_item(
        Key={"projectId": project_id, "taskId": task_id}
    )
    item = response.get("Item")

    if not item:
        raise HTTPException(status_code=404, detail="Task not found")

    return item


def list_tasks(project_id: str) -> list[dict]:
    """List all tasks for a project."""
    table = get_tasks_table()

    response = table.query(
        KeyConditionExpression=Key("projectId").eq(project_id)
    )
    return response.get("Items", [])


def update_task(project_id: str, task_id: str, data: TaskUpdate) -> dict:
    """Update an existing task."""
    # Verify exists
    get_task(project_id, task_id)

    table = get_tasks_table()
    now = datetime.now(timezone.utc).isoformat()

    update_fields = data.model_dump(exclude_unset=True)
    if not update_fields:
        raise HTTPException(status_code=400, detail="No fields to update")

    update_fields["updatedAt"] = now

    # Mark completedAt when status changes to completed
    if update_fields.get("status") == "completed":
        update_fields["completedAt"] = now

    # Build update expression
    expressions = []
    attr_names = {}
    attr_values = {}

    for i, (key, value) in enumerate(update_fields.items()):
        expressions.append(f"#k{i} = :v{i}")
        attr_names[f"#k{i}"] = key
        attr_values[f":v{i}"] = value

    response = table.update_item(
        Key={"projectId": project_id, "taskId": task_id},
        UpdateExpression="SET " + ", ".join(expressions),
        ExpressionAttributeNames=attr_names,
        ExpressionAttributeValues=attr_values,
        ReturnValues="ALL_NEW",
    )

    return response["Attributes"]


def delete_task(project_id: str, task_id: str) -> None:
    """Delete a task."""
    # Verify exists
    get_task(project_id, task_id)

    table = get_tasks_table()
    table.delete_item(Key={"projectId": project_id, "taskId": task_id})
