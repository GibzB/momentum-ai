"""Integration tests for Projects and Tasks CRUD API using mocked DynamoDB."""

import boto3
import pytest
from httpx import ASGITransport, AsyncClient
from moto import mock_aws

from app.core.config import settings


@pytest.fixture
def aws_env(monkeypatch):
    """Mock AWS credentials."""
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_SECURITY_TOKEN", "testing")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")


@pytest.fixture
def dynamodb_tables(aws_env):
    """Create mocked DynamoDB tables."""
    with mock_aws():
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")

        # Projects table
        dynamodb.create_table(
            TableName=settings.dynamodb_table_projects,
            KeySchema=[{"AttributeName": "projectId", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "projectId", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )

        # Tasks table
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
    """Async HTTP client for testing."""
    # Clear LRU cache so moto table is used
    from app.services.dynamodb import get_dynamodb_resource

    get_dynamodb_resource.cache_clear()

    from app.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


@pytest.mark.asyncio
async def test_health(client):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_project_crud(client):
    # Create
    r = await client.post(
        "/api/projects",
        json={
            "name": "Test Project",
            "description": "A test project",
            "deadline": "2025-12-31",
            "objective": "Ship MVP",
        },
    )
    assert r.status_code == 201
    project = r.json()
    project_id = project["projectId"]
    assert project["name"] == "Test Project"
    assert project["objective"] == "Ship MVP"

    # Get
    r = await client.get(f"/api/projects/{project_id}")
    assert r.status_code == 200
    assert r.json()["name"] == "Test Project"

    # List
    r = await client.get("/api/projects")
    assert r.status_code == 200
    assert r.json()["count"] == 1

    # Update
    r = await client.patch(f"/api/projects/{project_id}", json={"name": "Updated"})
    assert r.status_code == 200
    assert r.json()["name"] == "Updated"

    # Delete
    r = await client.delete(f"/api/projects/{project_id}")
    assert r.status_code == 204

    # Verify gone
    r = await client.get(f"/api/projects/{project_id}")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_task_crud(client):
    # Create project first
    r = await client.post("/api/projects", json={"name": "Task Project"})
    project_id = r.json()["projectId"]

    # Create task
    r = await client.post(
        f"/api/projects/{project_id}/tasks",
        json={
            "title": "Build feature",
            "description": "Implement the thing",
            "deadline": "2025-06-15",
        },
    )
    assert r.status_code == 201
    task = r.json()
    task_id = task["taskId"]
    assert task["title"] == "Build feature"
    assert task["status"] == "pending"

    # List tasks
    r = await client.get(f"/api/projects/{project_id}/tasks")
    assert r.status_code == 200
    assert r.json()["count"] == 1

    # Update — mark completed
    r = await client.patch(
        f"/api/projects/{project_id}/tasks/{task_id}",
        json={"status": "completed"},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "completed"
    assert r.json()["completedAt"] is not None

    # Delete
    r = await client.delete(f"/api/projects/{project_id}/tasks/{task_id}")
    assert r.status_code == 204


@pytest.mark.asyncio
async def test_project_not_found(client):
    r = await client.get("/api/projects/nonexistent-id")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_task_not_found(client):
    r = await client.get("/api/projects/some-project/tasks/nonexistent-id")
    assert r.status_code == 404
