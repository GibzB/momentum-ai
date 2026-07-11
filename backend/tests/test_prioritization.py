"""Tests for M1 prioritization endpoint with mocked Bedrock."""

import json
from unittest.mock import MagicMock, patch

import boto3
import pytest
from httpx import ASGITransport, AsyncClient
from moto import mock_aws

from app.core.config import settings

MOCK_BEDROCK_RESPONSE = {
    "recommendations": [
        {
            "taskId": "TASK_ID_PLACEHOLDER",
            "title": "Design database schema",
            "priorityScore": 95,
            "quadrant": "urgent-important",
            "reason": (
                "This is a foundational task that blocks all other development work."
            ),
            "nextAction": ("Draft the DynamoDB table schemas in the architecture doc."),
            "dependencies": [],
            "confidence": 0.92,
        },
        {
            "taskId": "TASK_ID_PLACEHOLDER_2",
            "title": "Write API endpoints",
            "priorityScore": 78,
            "quadrant": "not-urgent-important",
            "reason": ("Needed for frontend integration but depends on schema design."),
            "nextAction": (
                "Start with the project CRUD endpoints once schema is finalized."
            ),
            "dependencies": ["TASK_ID_PLACEHOLDER"],
            "confidence": 0.85,
        },
    ],
    "summary": (
        "Database schema should be completed first as it unblocks API development."
    ),
}


@pytest.fixture
def aws_env(monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_SECURITY_TOKEN", "testing")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")


@pytest.fixture
def dynamodb_tables(aws_env):
    with mock_aws():
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")

        dynamodb.create_table(
            TableName=settings.dynamodb_table_projects,
            KeySchema=[{"AttributeName": "projectId", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "projectId", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )

        dynamodb.create_table(
            TableName=settings.dynamodb_table_tasks,
            KeySchema=[
                {"AttributeName": "projectId", "KeyType": "HASH"},
                {"AttributeName": "taskId", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "projectId", "AttributeType": "S"},
                {"AttributeName": "taskId", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )

        yield


@pytest.fixture
async def client(dynamodb_tables):
    from app.services.dynamodb import get_dynamodb_resource

    get_dynamodb_resource.cache_clear()

    from app.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


def make_bedrock_response(content: dict) -> MagicMock:
    """Create a mock Bedrock response object."""
    body_content = json.dumps(
        {"output": {"message": {"content": [{"text": json.dumps(content)}]}}}
    ).encode()

    mock_body = MagicMock()
    mock_body.read.return_value = body_content

    return {"body": mock_body}


@pytest.mark.asyncio
async def test_prioritize_success(client):
    """Test successful prioritization with mocked Bedrock."""
    # Create project
    r = await client.post(
        "/api/projects",
        json={
            "name": "Test Project",
            "objective": "Build MVP",
            "deadline": "2025-12-31",
        },
    )
    project_id = r.json()["projectId"]

    # Create tasks
    r1 = await client.post(
        f"/api/projects/{project_id}/tasks",
        json={
            "title": "Design database schema",
            "description": "Define DynamoDB table structures",
        },
    )
    task1_id = r1.json()["taskId"]

    r2 = await client.post(
        f"/api/projects/{project_id}/tasks",
        json={
            "title": "Write API endpoints",
            "description": "Implement CRUD operations",
        },
    )
    task2_id = r2.json()["taskId"]

    # Prepare mock response with real task IDs
    mock_response = MOCK_BEDROCK_RESPONSE.copy()
    mock_response["recommendations"] = [
        {**mock_response["recommendations"][0], "taskId": task1_id},
        {
            **mock_response["recommendations"][1],
            "taskId": task2_id,
            "dependencies": [task1_id],
        },
    ]

    # Mock Bedrock call
    with patch("app.services.bedrock.get_bedrock_client") as mock_client:
        mock_bedrock = MagicMock()
        mock_bedrock.invoke_model.return_value = make_bedrock_response(mock_response)
        mock_client.return_value = mock_bedrock

        # Clear cache so mock is used
        from app.services.bedrock import get_bedrock_client

        get_bedrock_client.cache_clear()

        r = await client.post(f"/api/projects/{project_id}/prioritize")

    assert r.status_code == 200
    data = r.json()
    assert data["projectId"] == project_id
    assert len(data["recommendations"]) == 2
    assert data["recommendations"][0]["priorityScore"] == 95
    assert data["recommendations"][0]["quadrant"] == "urgent-important"
    assert data["recommendations"][1]["dependencies"] == [task1_id]
    assert "summary" in data
    assert "generatedAt" in data


@pytest.mark.asyncio
async def test_prioritize_no_tasks(client):
    """Test prioritization with no active tasks returns 400."""
    r = await client.post("/api/projects", json={"name": "Empty Project"})
    project_id = r.json()["projectId"]

    r = await client.post(f"/api/projects/{project_id}/prioritize")
    assert r.status_code == 400
    assert "No active tasks" in r.json()["detail"]


@pytest.mark.asyncio
async def test_prioritize_project_not_found(client):
    """Test prioritization with invalid project ID returns 404."""
    r = await client.post("/api/projects/nonexistent/prioritize")
    assert r.status_code == 404
