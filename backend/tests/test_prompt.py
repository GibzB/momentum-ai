"""Prompt structure validation tests."""

from app.services.prioritization import SYSTEM_PROMPT, build_context_prompt


def test_system_prompt_contains_required_fields():
    """System prompt must instruct model to return all required fields."""
    required_fields = [
        "priorityScore",
        "quadrant",
        "reason",
        "nextAction",
        "dependencies",
        "confidence",
    ]
    for field in required_fields:
        assert field in SYSTEM_PROMPT, f"Missing {field} in system prompt"


def test_system_prompt_contains_quadrants():
    """System prompt must define all 4 Eisenhower quadrants."""
    quadrants = [
        "urgent-important",
        "not-urgent-important",
        "urgent-not-important",
        "not-urgent-not-important",
    ]
    for q in quadrants:
        assert q in SYSTEM_PROMPT, f"Missing quadrant {q}"


def test_system_prompt_requires_json():
    """System prompt must instruct JSON-only response."""
    assert "JSON" in SYSTEM_PROMPT
    assert "Do NOT include any text outside the JSON" in SYSTEM_PROMPT


def test_build_context_prompt_includes_project_info():
    """Context prompt should include project metadata."""
    project = {
        "name": "Test Project",
        "objective": "Ship fast",
        "deadline": "2025-12-31",
        "description": "A test",
    }
    tasks = [
        {
            "taskId": "abc-123",
            "title": "Build feature",
            "status": "pending",
            "description": "Important work",
            "deadline": "2025-06-01",
        }
    ]

    prompt = build_context_prompt(project, tasks)

    assert "Test Project" in prompt
    assert "Ship fast" in prompt
    assert "2025-12-31" in prompt
    assert "Build feature" in prompt
    assert "abc-123" in prompt


def test_build_context_prompt_separates_completed():
    """Completed tasks should appear in separate section."""
    project = {"name": "P"}
    tasks = [
        {"taskId": "t1", "title": "Done", "status": "completed"},
        {"taskId": "t2", "title": "Todo", "status": "pending"},
    ]

    prompt = build_context_prompt(project, tasks)

    assert "COMPLETED TASKS (1)" in prompt
    assert "ACTIVE TASKS TO PRIORITIZE (1)" in prompt
