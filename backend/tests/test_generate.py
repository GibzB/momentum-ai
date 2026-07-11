"""Tests for task generation endpoint."""

import json
from unittest.mock import MagicMock, patch

import boto3
import pytest
from httpx import ASGITransport, AsyncClient
from moto import mock_aws

from app.core.config import settings

MOCK_GENERATE_RESPONSE = {
    "suggestions": [
        {
            "title": "Define project requirements",
            "description": "Document functional and non-functional requirements",
            "deadline": "2025-07-20",
            "reason": "Requirements are the foundation for all development work",
            "order": 1,
        },
        {
            "title": "Design system architecture",
            "description": "Create architecture diagrams and tech stack decisions",
            "deadline": "2025-07-25",
            "reason": "Architecture decisions must precede implementation",
            "order": 2,
        },
        {
            "title": "Build API endpoints",
            "description": "Implement the backend REST API",
            "deadline": "2025-08-10",
            "reason": "API is needed for frontend integration",
            "order": 3,
        },
    ],
    "strategy": (
        "Breaking the project into requirements, design, and implementation phases."
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
    body_content = json.dumps(
        {"output": {"message": {"content": [{"text": json.dumps(content)}]}}}
    ).encode()
    mock_body = MagicMock()
    mock_body.read.return_value = body_content
    return {"body": mock_body}


@pytest.mark.asyncio
async def test_generate_tasks_success(client):
    """Generate tasks for a project with objective."""
    r = await client.post(
        "/api/projects",
        json={
            "name": "Build App",
            "objective": "Create a web application for task management",
            "deadline": "2025-09-01",
        },
    )
    project_id = r.json()["projectId"]

    with patch("app.services.bedrock.get_bedrock_client") as mock_client:
        mock_bedrock = MagicMock()
        mock_bedrock.invoke_model.return_value = make_bedrock_response(
            MOCK_GENERATE_RESPONSE
        )
        mock_client.return_value = mock_bedrock

        from app.services.bedrock import get_bedrock_client

        get_bedrock_client.cache_clear()

        r = await client.post(f"/api/projects/{project_id}/generate-tasks")

    assert r.status_code == 200
    data = r.json()
    assert data["projectId"] == project_id
    assert len(data["suggestions"]) == 3
    assert data["suggestions"][0]["title"] == "Define project requirements"
    assert data["suggestions"][0]["reason"] is not None
    assert "strategy" in data


@pytest.mark.asyncio
async def test_generate_tasks_no_objective(client):
    """Returns 400 if project has no objective or description."""
    r = await client.post("/api/projects", json={"name": "Empty"})
    project_id = r.json()["projectId"]

    r = await client.post(f"/api/projects/{project_id}/generate-tasks")
    assert r.status_code == 400
    assert "objective" in r.json()["detail"].lower()


@pytest.mark.asyncio
async def test_accept_tasks(client):
    """Accept suggested tasks creates them in the project."""
    r = await client.post(
        "/api/projects",
        json={"name": "Accept Test", "objective": "Test"},
    )
    project_id = r.json()["projectId"]

    r = await client.post(
        f"/api/projects/{project_id}/accept-tasks",
        json={
            "tasks": [
                {
                    "title": "Task A",
                    "description": "Do A",
                    "deadline": "2025-08-01",
                    "reason": "Needed for B",
                    "order": 1,
                },
                {
                    "title": "Task B",
                    "description": "Do B",
                    "deadline": None,
                    "reason": "Final step",
                    "order": 2,
                },
            ]
        },
    )
    assert r.status_code == 201
    data = r.json()
    assert data["count"] == 2
    assert data["tasks"][0]["title"] == "Task A"
    assert "Reason: Needed for B" in data["tasks"][0]["description"]
