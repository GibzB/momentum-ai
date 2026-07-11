# M1 System Prompt

This document tracks the M1 (Momentum Intelligence) system prompt used for prioritization.

The canonical version lives in `backend/app/services/prioritization.py` as `SYSTEM_PROMPT`.

## Overview

M1 analyzes project context and returns structured JSON prioritization:

- **Input:** Project metadata + all tasks (active and completed for context)
- **Output:** Ranked recommendations with scores, quadrants, explanations
- **Model:** Amazon Nova Lite (via Bedrock)
- **Temperature:** 0.2 (low variance, consistent rankings)

## Response Structure

```json
{
  "recommendations": [
    {
      "taskId": "uuid",
      "title": "task title",
      "priorityScore": 85,
      "quadrant": "urgent-important",
      "reason": "explanation",
      "nextAction": "concrete next step",
      "dependencies": ["other-task-id"],
      "confidence": 0.85
    }
  ],
  "summary": "Brief prioritization overview"
}
```

## Eisenhower Quadrants

| Quadrant | Meaning |
|----------|---------|
| urgent-important | Do first |
| not-urgent-important | Schedule |
| urgent-not-important | Do quickly / delegate |
| not-urgent-not-important | Consider dropping |

## Evolution Notes

- v0.1: Initial prompt with Eisenhower matrix, dependencies, confidence scoring
- Temperature 0.2 chosen for consistency across re-runs
- Max 4096 tokens to accommodate large task lists
