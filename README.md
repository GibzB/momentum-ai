# Momentum

**Turn priorities into progress.**

Momentum is an AI-powered project prioritization assistant. Unlike traditional task managers, Momentum helps you decide *what to work on next* — not just where to store tasks.

M1 (Momentum Intelligence) analyzes your projects, deadlines, task descriptions, and completed work to deliver ranked recommendations with explanations.

## Live

| Service | URL |
|---------|-----|
| Frontend | https://dev.d2kyovkps8f1nm.amplifyapp.com |
| API | https://3a9xfn5st8.execute-api.us-east-1.amazonaws.com |

## Architecture

```
React (Vite + TypeScript + Tailwind)
  → AWS Amplify Hosting
  → HTTP API Gateway
  → AWS Lambda (Python 3.12, ARM64)
  → FastAPI + Mangum
  → Amazon Bedrock (Nova Lite) + DynamoDB
```

## Tech Stack

**Frontend:** React 19, TypeScript, Vite, Tailwind CSS v4, shadcn/ui, React Query, React Hook Form, Zod

**Backend:** Python 3.12, FastAPI, Pydantic, boto3, Mangum

**AI:** Amazon Bedrock (Nova Lite), structured JSON prompts

**Infrastructure:** Terraform, DynamoDB (PAY_PER_REQUEST), Lambda ARM64, API Gateway v2, CloudWatch, Amplify

**CI/CD:** GitHub Actions (lint → test → validate → deploy)

## Local Development

### Frontend

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173
```

### Backend

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

### Run Tests

```bash
# Backend (21 tests)
cd backend && source .venv/bin/activate
pytest tests/ -v

# Frontend
cd frontend
npm run lint
npm run build
```

## API Endpoints

```
GET    /health
POST   /api/projects
GET    /api/projects
GET    /api/projects/{id}
PATCH  /api/projects/{id}
DELETE /api/projects/{id}
POST   /api/projects/{id}/tasks
GET    /api/projects/{id}/tasks
GET    /api/projects/{id}/tasks/{taskId}
PATCH  /api/projects/{id}/tasks/{taskId}
DELETE /api/projects/{id}/tasks/{taskId}
POST   /api/projects/{id}/prioritize
```

## Deploy

```bash
# One-command deploy (requires AWS credentials)
./scripts/deploy.sh dev K1-Kitstek-Billy
```

## M1 Prioritization

POST `/api/projects/{id}/prioritize` returns:

```json
{
  "projectId": "...",
  "recommendations": [
    {
      "taskId": "...",
      "title": "...",
      "priorityScore": 95,
      "quadrant": "urgent-important",
      "reason": "Why this task matters now",
      "nextAction": "Concrete next step",
      "dependencies": ["other-task-id"],
      "confidence": 0.92
    }
  ],
  "summary": "Brief prioritization overview",
  "generatedAt": "2026-07-11T..."
}
```

## Project Structure

```
momentum-ai/
├── frontend/          # React + Vite + Tailwind
├── backend/           # FastAPI + DynamoDB + Bedrock
├── infrastructure/    # Terraform (modular)
├── scripts/           # Deploy/destroy helpers
├── docs/              # PRD, architecture, prompts
└── .github/           # CI/CD workflows
```

## License

MIT
