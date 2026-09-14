"""Tests for M1 agent tools and the background watcher."""

import json
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import boto3
import pytest
from moto import mock_aws

from app.agent import watcher
from app.agent.m1 import M1Output, create_m1_agent
from app.agent.tools import days_until, eisenhower_quadrant
from app.core.config import settings
from app.schemas.project import ProjectCreate
from app.schemas.task import TaskCreate


def _call(tool_fn, **kwargs):
    """Invoke a Strands @tool-decorated function like plain Python."""
    return tool_fn(**kwargs)


def test_days_until_overdue():
    yesterday = (datetime.now(UTC) - timedelta(days=1)).strftime("%Y-%m-%d")
    out = json.loads(_call(days_until, deadline=yesterday))
    assert out["is_overdue"] is True
    assert out["pressure"] == "overdue"


def test_days_until_soon_and_none():
    in_five = (datetime.now(UTC) + timedelta(days=5)).strftime("%Y-%m-%d")
    assert json.loads(_call(days_until, deadline=in_five))["pressure"] == "soon"
    assert json.loads(_call(days_until, deadline="garbage"))["pressure"] == "none"


@pytest.mark.parametrize(
    ("days", "importance", "expected"),
    [
        (1, 9, "urgent-important"),
        (1, 2, "urgent-not-important"),
        (30, 9, "not-urgent-important"),
        (None, 2, "not-urgent-not-important"),
    ],
)
def test_eisenhower_quadrant(days, importance, expected):
    assert (
        _call(eisenhower_quadrant, days_remaining=days, importance=importance)
        == expected
    )


def test_agent_is_wired_with_tools():
    agent = create_m1_agent("p1")
    names = set(agent.tool_names)
    assert {"get_project_tasks", "days_until", "eisenhower_quadrant"} <= names
    assert agent.name == "M1"


@pytest.fixture
def tables(monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    with mock_aws():
        ddb = boto3.resource("dynamodb", region_name="us-east-1")
        ddb.create_table(
            TableName=settings.dynamodb_table_projects,
            KeySchema=[{"AttributeName": "projectId", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "projectId", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        ddb.create_table(
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
        from app.services.dynamodb import get_dynamodb_resource

        get_dynamodb_resource.cache_clear()
        yield


def _output(task_id: str, attention: bool) -> M1Output:
    return M1Output(
        recommendations=[
            {
                "taskId": task_id,
                "title": "Ship it",
                "priorityScore": 90,
                "quadrant": "urgent-important",
                "reason": "Deadline is tomorrow",
                "nextAction": "Finish the last section",
                "dependencies": [],
                "confidence": 0.9,
            }
        ],
        summary="One task left.",
        needsHumanAttention=attention,
        attentionReason="Deadline tomorrow, task not started" if attention else None,
    )


def test_watcher_skips_quiet_projects_and_alerts_risky_ones(tables):
    from app.models.project import create_project, get_project
    from app.models.task import create_task

    quiet = create_project(ProjectCreate(name="Quiet"))
    risky = create_project(ProjectCreate(name="Risky", deadline="2020-01-01"))
    empty = create_project(ProjectCreate(name="Empty"))
    qt = create_task(quiet["projectId"], TaskCreate(title="Later"))
    rt = create_task(risky["projectId"], TaskCreate(title="Ship it"))

    def fake_run(project, tasks):
        if project["projectId"] == risky["projectId"]:
            return _output(rt["taskId"], attention=True)
        return _output(qt["taskId"], attention=False)

    with (
        patch.object(watcher, "run_m1", side_effect=fake_run),
        patch.object(watcher, "notify") as mock_notify,
    ):
        summary = watcher.handler({}, None)

    assert summary == {"checked": 2, "alerted": 1, "failed": 0}
    mock_notify.assert_called_once()
    assert mock_notify.call_args.args[0]["projectId"] == risky["projectId"]

    # Both active projects got a persisted recommendation; the empty one did not
    assert get_project(quiet["projectId"])["lastRecommendation"]["summary"]
    assert get_project(risky["projectId"])["lastRecommendation"]["needsHumanAttention"]
    assert "lastRecommendation" not in get_project(empty["projectId"])


def test_watcher_alerts_only_on_new_risk(tables):
    from app.models.project import create_project, get_project
    from app.models.task import create_task

    risky = create_project(ProjectCreate(name="Risky"))
    rt = create_task(risky["projectId"], TaskCreate(title="Ship it"))

    with (
        patch.object(watcher, "run_m1", return_value=_output(rt["taskId"], True)),
        patch.object(watcher, "notify", return_value=True) as mock_notify,
    ):
        assert watcher.run_watch()["alerted"] == 1
        assert watcher.run_watch()["alerted"] == 0  # unchanged risk: stay quiet
    mock_notify.assert_called_once()
    assert get_project(risky["projectId"])["lastAlert"]["delivered"] is True

    changed = _output(rt["taskId"], True)
    changed.attentionReason = "Now two tasks are overdue"
    with (
        patch.object(watcher, "run_m1", return_value=changed),
        patch.object(watcher, "notify") as mock_notify,
    ):
        assert watcher.run_watch()["alerted"] == 1
    assert get_project(risky["projectId"])["lastRecommendation"]["attentionReason"] == (
        "Now two tasks are overdue"
    )


def test_watcher_retries_alert_until_delivered(tables):
    from app.models.project import create_project, get_project
    from app.models.task import create_task

    risky = create_project(ProjectCreate(name="Risky"))
    rt = create_task(risky["projectId"], TaskCreate(title="Ship it"))
    output = _output(rt["taskId"], True)

    with (
        patch.object(watcher, "run_m1", return_value=output),
        patch.object(watcher, "notify", side_effect=RuntimeError("sns down")),
    ):
        assert watcher.run_watch() == {"checked": 0, "alerted": 0, "failed": 1}
    assert get_project(risky["projectId"])["lastAlert"]["delivered"] is False

    with (
        patch.object(watcher, "run_m1", return_value=output),
        patch.object(watcher, "notify", return_value=True) as mock_notify,
    ):
        assert watcher.run_watch()["alerted"] == 1  # same reason, but never delivered
        assert watcher.run_watch()["alerted"] == 0
    mock_notify.assert_called_once()

    # Risk resolves -> alert state cleared -> same reason alerts again later
    with (
        patch.object(watcher, "run_m1", return_value=_output(rt["taskId"], False)),
        patch.object(watcher, "notify", return_value=True) as mock_notify,
    ):
        assert watcher.run_watch()["alerted"] == 0
    assert "lastAlert" not in get_project(risky["projectId"])


def test_claim_alert_is_exclusive(tables):
    from app.models.project import claim_alert, create_project, mark_alert_delivered

    p = create_project(ProjectCreate(name="P"))
    assert claim_alert(p["projectId"], "overdue") is True
    mark_alert_delivered(p["projectId"], "overdue")
    assert claim_alert(p["projectId"], "overdue") is False  # racing sweep loses
    assert claim_alert(p["projectId"], "two overdue") is True
    assert claim_alert("missing", "overdue") is False


def test_save_recommendation_never_resurrects_deleted_project(tables):
    from app.models.project import (
        create_project,
        delete_project,
        list_projects,
        save_recommendation,
    )

    p = create_project(ProjectCreate(name="Gone"))
    delete_project(p["projectId"])
    assert save_recommendation(p["projectId"], {"summary": "x"}) is False
    assert list_projects() == []


def test_watcher_isolates_failures(tables):
    from app.models.project import create_project
    from app.models.task import create_task

    p = create_project(ProjectCreate(name="Boom"))
    create_task(p["projectId"], TaskCreate(title="x"))

    with patch.object(watcher, "run_m1", side_effect=RuntimeError("bedrock down")):
        summary = watcher.run_watch()

    assert summary == {"checked": 0, "alerted": 0, "failed": 1}


def test_notify_publishes_to_sns(monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    with mock_aws():
        topic = boto3.client("sns", region_name="us-east-1").create_topic(
            Name="momentum-alerts"
        )
        monkeypatch.setattr(settings, "alerts_topic_arn", topic["TopicArn"])
        from app.schemas.prioritization import PrioritizationResponse

        resp = PrioritizationResponse(
            projectId="p1",
            generatedAt="now",
            **_output("t1", attention=True).model_dump(),
        )
        watcher.notify({"name": "Risky"}, resp)  # must not raise
