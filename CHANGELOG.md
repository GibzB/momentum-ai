# Changelog

All notable changes to Momentum AI are documented here.

---

## [Unreleased] — feature/generate-tasks

### AI Task Generation

M1 can now generate tasks from a project's objective. Instead of manually creating every task, describe what you want to achieve and let M1 break it down.

**How it works:**

1. Create a project with a name, objective, and deadline
2. Click "Generate Tasks" on the project page
3. M1 analyzes the objective, timeframe, and description
4. Returns 5–12 suggested tasks, each with:
   - Title and description
   - Suggested deadline (distributed across the timeline)
   - Reason explaining why this task is necessary
   - Execution order
5. Select which tasks to keep (all selected by default)
6. Click "Accept" — tasks are created in the project

**Why this matters:** Reduces blank-page paralysis. Users describe the *what*, M1 figures out the *how*. Every generated task comes with justification, so users understand the reasoning and can make informed decisions about what to keep or discard.

**Endpoints:**
- `POST /api/projects/{id}/generate-tasks` — returns suggestions
- `POST /api/projects/{id}/accept-tasks` — creates selected tasks

---

## [0.2.0] — 2026-07-12

### Eisenhower Matrix Dashboard

The dashboard now displays a four-quadrant Eisenhower Matrix showing prioritized tasks across all projects, colour-coded by project.

**Quadrants:**
- Do First (Urgent & Important) — red
- Schedule (Not Urgent & Important) — blue
- Quick Wins (Urgent & Not Important) — amber
- Consider Dropping (Not Urgent & Not Important) — muted

Only tasks that M1 has prioritized appear in the matrix. Unprioritized tasks remain in their project views until the user runs prioritization.

### Deadline Ticker Banner

A scrolling marquee banner appears at the top of the dashboard when tasks are due within 3 days. Shows task name, project name, and urgency (TODAY / TOMORROW / Xd left). Pauses on hover. Scrolls right-to-left continuously.

### Auto-Prioritization

The dashboard automatically runs M1 prioritization across all projects when tasks are loaded. No manual button needed — the matrix populates itself.

### Project Colour Coding

Each project is assigned a distinct colour from a palette of 8. Colours appear in:
- Eisenhower Matrix task labels
- Deadline banner dots
- Project legend at the bottom of the dashboard

---

## [0.1.0] — 2026-07-11

### Initial MVP Release

Complete full-stack application deployed to AWS.

**Frontend:**
- React 19 + TypeScript + Vite
- Tailwind CSS v4 with shadcn/ui components
- Dark mode by default
- Dashboard, Projects list, Project detail with tasks
- M1 prioritization interface (scores, quadrants, reasons)
- React Query for server state, React Hook Form + Zod for validation

**Backend:**
- FastAPI on AWS Lambda (Python 3.12, ARM64)
- CRUD APIs for Projects and Tasks
- DynamoDB (PAY_PER_REQUEST, two tables)
- M1 prioritization via Amazon Bedrock (Nova Lite)
- Structured JSON responses with Eisenhower quadrants, priority scores, confidence levels

**Infrastructure:**
- Terraform (modular: DynamoDB, Lambda, API Gateway, IAM, Monitoring, Amplify, GitHub OIDC)
- HTTP API Gateway v2 with catch-all route
- CloudWatch alarms (errors, duration, throttles)
- GitHub Actions CI/CD (lint, test, validate, deploy)
- AWS Amplify hosting for frontend

**Testing:**
- 24 backend tests (CRUD, validation, prioritization, prompt structure, task generation)
- Mocked DynamoDB via moto, mocked Bedrock for AI tests
- Ruff lint + format, ESLint, TypeScript strict mode
