---
name: testing-momentum-locally
description: Exercise Momentum project prioritization and watcher flows locally without AWS credentials.
---

# Local Momentum testing

## Services and dependencies
- Backend: use `backend/.venv/bin/python`; install editable `.[dev]` from backend if unavailable.
- Frontend: run `npm ci` then `npm run dev` from frontend. Open `http://localhost:5173`.
- API base is `VITE_API_URL`, default `http://localhost:8000`; prefer localhost rather than 127.0.0.1 for frontend CORS.
- No application login is currently required. Keep test services on loopback.
- DynamoDB fixtures are in `backend/tests/test_api.py`, not conftest.py. Projects use projectId HASH; tasks use projectId HASH and taskId RANGE.

## No-AWS runtime strategy
- Start `moto.mock_aws()` before importing the application or creating boto3 resources. Set dummy AWS credentials and clear cached `get_dynamodb_resource` if already imported.
- Run moto and uvicorn in the same Python process so UI requests share the in-memory database.
- Patch both `app.services.prioritization.run_m1` and `app.agent.watcher.run_m1` with a deterministic `M1Output`; patching the original definition alone does not replace these imported references.
- Keep real schemas, routers, persistence, and watcher code. Explicitly disclose that agent reasoning/Bedrock are not tested.
- For watcher verification, create a moto SNS topic, set `settings.alerts_topic_arn`, spy on publish while forwarding to moto, and call real `run_watch()` in the same process.
- Include active risk, active safe, and empty controls; confirm both cache writes and actual SNS publish call counts, not only watcher counters.
- Keep temporary harness routes/files out of production commits.

## Browser flow
- Projects > New Project > Create opens detail; Add Task creates tasks; the action button is `Prioritize`.
- A stub keyed to incomplete overdue tasks allows a natural true-to-false attention transition by completing overdue work and clicking Prioritize again.
- Native Chromium date fields auto-advance segments. Click month/day/year separately when typing to avoid skipping the day.
- GET recommendations returns 404 before the first run; compare subsequent GET with persisted output, including confidence floats.
- Capture separate screenshots for attention present/absent and label the evidence as stub-backed.

## Devin Secrets Needed
- None for moto + deterministic output testing.
- Real Bedrock coverage needs AWS credentials (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, optionally `AWS_SESSION_TOKEN`) or an approved AWS profile with model invocation access. Deployed integration additionally requires DynamoDB/SNS permissions.
