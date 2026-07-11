"""Validation and edge case tests."""

import boto3
import pytest
from httpx import ASGITransport, AsyncClient
from moto import mock_aws

from app.core.config import settings


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


# --- Project Validation ---


@pytest.mark.asyncio
async def test_create_project_empty_name(client):
    """Name is required and cannot be empty."""
    r = await client.post("/api/projects", json={"name": ""})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_create_project_name_too_long(client):
    """Name max 200 chars."""
    r = await client.post("/api/projects", json={"name": "x" * 201})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_create_project_missing_name(client):
    """Name field is required."""
    r = await client.post("/api/projects", json={"description": "no name"})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_update_project_no_fields(client):
    """Update with empty body returns 400."""
    r = await client.post("/api/projects", json={"name": "Test"})
    pid = r.json()["projectId"]
    r = await client.patch(f"/api/projects/{pid}", json={})
    assert r.status_code == 400


# --- Task Validation ---


@pytest.mark.asyncio
async def test_create_task_empty_title(client):
    """Title required."""
    r = await client.post("/api/projects", json={"name": "P"})
    pid = r.json()["projectId"]
    r = await client.post(f"/api/projects/{pid}/tasks", json={"title": ""})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_create_task_invalid_status(client):
    """Status must be pending|in_progress|completed."""
    r = await client.post("/api/projects", json={"name": "P"})
    pid = r.json()["projectId"]
    r = await client.post(
        f"/api/projects/{pid}/tasks",
        json={"title": "T", "status": "invalid"},
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_update_task_invalid_status(client):
    """Cannot set invalid status on update."""
    r = await client.post("/api/projects", json={"name": "P"})
    pid = r.json()["projectId"]
    r = await client.post(f"/api/projects/{pid}/tasks", json={"title": "T"})
    tid = r.json()["taskId"]
    r = await client.patch(
        f"/api/projects/{pid}/tasks/{tid}",
        json={"status": "done"},
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_complete_task_sets_completed_at(client):
    """Marking task completed should populate completedAt."""
    r = await client.post("/api/projects", json={"name": "P"})
    pid = r.json()["projectId"]
    r = await client.post(f"/api/projects/{pid}/tasks", json={"title": "T"})
    tid = r.json()["taskId"]
    assert r.json().get("completedAt") is None

    r = await client.patch(
        f"/api/projects/{pid}/tasks/{tid}",
        json={"status": "completed"},
    )
    assert r.status_code == 200
    assert r.json()["completedAt"] is not None
