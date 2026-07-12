# Momentum AI — Product Update

## What Momentum Does

Momentum is an AI-powered project prioritization assistant. It doesn't just store tasks — it tells you what to work on next and why.

At its core sits M1 (Momentum Intelligence), an AI agent powered by Amazon Bedrock that analyzes your projects, deadlines, and task relationships to produce ranked recommendations with full explanations.

---

## The Problem

Most task management tools are glorified lists. They let you organize work but leave the hardest part to you: deciding what matters right now.

This creates decision fatigue. You stare at 30 tasks across 3 projects and waste time thinking about priorities instead of making progress.

---

## How Momentum Solves It

### 1. You describe the outcome, M1 figures out the work

Create a project with an objective and a deadline. That's it.

Click **Generate Tasks** and M1 breaks your objective into 5–12 concrete, actionable tasks. Each task comes with:

- A clear title and description
- A suggested deadline distributed across your timeline
- A **reason** explaining why this task is necessary to achieve the objective
- An execution order based on logical dependencies

You review the suggestions, deselect anything you don't want, and accept. Tasks are created instantly.

**Example:** You enter "Build and launch a SaaS product for freelance invoice management with Stripe integration" with a September deadline. M1 returns tasks spanning market research through launch day, each justified and time-boxed.

### 2. M1 prioritizes across all your projects

Once you have tasks, M1 ranks them using the Eisenhower Matrix:

| Quadrant | Meaning | Action |
|----------|---------|--------|
| Do First | Urgent & Important | Work on this now |
| Schedule | Not Urgent & Important | Plan time for this |
| Quick Wins | Urgent & Not Important | Do quickly or delegate |
| Consider Dropping | Not Urgent & Not Important | Remove or defer |

Each task gets:
- A priority score (1–100)
- A quadrant placement
- A plain-language explanation of why it has that priority
- A recommended next action
- A confidence score

### 3. The dashboard shows your world at a glance

The dashboard displays:

**Deadline Ticker** — A scrolling banner across the top showing tasks due within 3 days. Shows task name, project, and urgency (TODAY / TOMORROW / 2d left). Scrolls right-to-left, pauses when you hover.

**Eisenhower Matrix** — Four quadrants showing all prioritized tasks across every project. Tasks are colour-coded by project so you can see at a glance which projects dominate which quadrants.

**Stats** — Project count, active task count, due-soon count.

**Project Legend** — Colour-coded links to each project.

### 4. Project-level detail with AI reasoning

Inside each project you see:
- All active tasks sorted by priority score
- Eisenhower quadrant badges on each task
- M1's reasoning: *why* this priority, *what* to do next
- Completed tasks (with toggle to undo)
- Generate Tasks and Prioritize buttons

---

## Architecture

```
User → React (Amplify) → API Gateway → Lambda → FastAPI
                                                    ├── DynamoDB (projects + tasks)
                                                    └── Amazon Bedrock (Nova Lite)
```

All prioritization and task generation happens in Bedrock. Python never calculates priorities — it fetches data, constructs prompts, calls the model, validates the response, and returns structured JSON.

---

## What's New (Latest Changes)

### AI Task Generation (feature/generate-tasks)

Users no longer need to manually create every task. Describe your objective, set a deadline, and M1 produces a complete task breakdown with reasoning. Review, select, accept.

### Eisenhower Matrix Dashboard

The default dashboard view is a four-quadrant matrix. Only AI-prioritized tasks appear — no guessing, no heuristics. Tasks are tagged with project colours for cross-project visibility.

### Scrolling Deadline Banner

Tasks due within 3 days appear in a continuously scrolling ticker at the top of the dashboard. Visual urgency without clutter.

### Auto-Prioritization

The dashboard automatically runs M1 across all projects on load. The matrix populates without any manual action.

### Project Colour Coding

Eight distinct colours assigned to projects. Consistent across the matrix, banner, and legend. Makes it immediately clear which project owns which tasks.

---

## Key Design Decisions

- **AI does the thinking, not code** — Python orchestrates, Bedrock decides. This keeps logic adaptable without code changes.
- **Structured JSON responses** — Every AI response is validated against Pydantic schemas. If the model returns garbage, the user gets a clean error, not a crash.
- **Only show what AI has analyzed** — The matrix doesn't guess. If M1 hasn't prioritized a task, it doesn't appear in a quadrant. This maintains trust in the system.
- **Reasons on everything** — Generated tasks have reasons. Prioritized tasks have reasons. Users should always understand *why*.
- **Dark mode, minimal UI** — Inspired by Linear and Notion. Whitespace, rounded corners, no visual clutter.

---

## Live

| Service | URL |
|---------|-----|
| App | https://dev.d2kyovkps8f1nm.amplifyapp.com |
| API | https://3a9xfn5st8.execute-api.us-east-1.amazonaws.com |
