import uuid
from datetime import datetime, timezone
from typing import Optional

from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from fastapi import HTTPException

from app.schemas.project import ProjectCreate, ProjectUpdate
from app.services.dynamodb import get_projects_table


def create_project(data: ProjectCreate) -> dict:
    """Create a new project in DynamoDB."""
    table = get_projects_table()
    now = datetime.now(timezone.utc).isoformat()

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
    response = table.scan()
    return response.get("Items", [])


def update_project(project_id: str, data: ProjectUpdate) -> dict:
    """Update an existing project."""
    # Verify exists
    get_project(project_id)

    table = get_projects_table()
    now = datetime.now(timezone.utc).isoformat()

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
