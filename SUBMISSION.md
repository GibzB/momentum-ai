# Hackathon Submission — AWS "Agents for Humans"

**Track:** Everyday Agents
**Project:** Momentum — an autonomous prioritization agent (M1) built with the Strands Agents SDK

## Text description (paste into Devpost)

**What it does.** Momentum is an agent that decides *what you should work on
next* and keeps that decision current without being asked. You give it
projects, objectives, deadlines and tasks; M1 — a Strands Agents SDK agent on
Amazon Bedrock — ranks every open task on an Eisenhower Matrix, explains why,
and names the concrete next action. A background watcher re-runs M1 for every
project on a schedule and stays silent unless a deadline is genuinely at risk
— then, and only then, it emails you.

**Who it's for.** Anyone juggling several projects with real deadlines: solo
builders, students, freelancers, small teams. People who already have a task
list and still spend the first 20 minutes of every day deciding where to start.

**How it works.** The agent is a single Strands `Agent` with a
`BedrockModel` (Nova Lite) and three tools: `get_project_tasks` (DynamoDB),
`days_until` (deterministic date math so the model never guesses urgency) and
`eisenhower_quadrant`. Output is enforced with
`structured_output_model=M1Output`, a Pydantic schema that includes a
`needsHumanAttention` flag. The same agent is invoked two ways: on demand via
FastAPI on Lambda behind API Gateway, and autonomously via an EventBridge rule
that triggers a watcher Lambda. Results are cached on the project in DynamoDB;
alerts go through SNS. Infrastructure is Terraform; frontend is React on
Amplify.

**Why it matters.** Prioritization is the invisible chore under every other
chore. Momentum turns it into something that happens in the background, makes
the safe calls itself, and only surfaces when a human actually needs to weigh in.

## Judging checklist

| Requirement | Status | Where |
|-------------|--------|-------|
| Built with Strands Agents SDK | Done | `backend/app/agent/m1.py`, `tools.py` |
| Runs autonomously, surfaces only when needed | Done | `backend/app/agent/watcher.py`, EventBridge + SNS in Terraform |
| Public repo with source, assets, setup | Done | this repo, `README.md`, `docs/DEPLOYMENT.md` |
| MIT / Apache license visible in About | Done | `LICENSE` (MIT) — GitHub auto-detects it |
| README | Done | `README.md` |
| Architecture diagram | Done | `docs/architecture.png` (Mermaid source in `docs/ARCHITECTURE.md`) |
| Live demo link (optional, scores higher) | Live | Frontend + API URLs in `README.md` — **redeploy after merging so the Strands version is live** |
| AgentCore deployment (optional) | Documented | `docs/DEPLOYMENT.md` |
| Demo video ≤ 5 min | **You** | see script below |
| AWS Builder ID | **You** | https://profile.aws.amazon.com |
| Bonus: builder.aws.com post titled "Agents for Humans …" | **You** | outline below |

## Things only you can do before submitting

1. **Redeploy** so the live URLs run this code: `./scripts/deploy.sh dev <profile>`
   (also set `alert_email` in `infrastructure/terraform/environments/dev/terraform.tfvars`
   and confirm the SNS email so the alert path is demoable).
2. **Enable Bedrock model access** for Nova Lite in `us-east-1` if not already.
3. **Record the demo video** (script below) and upload to YouTube/Vimeo.
4. **Create / find your AWS Builder ID** and enter it on Devpost.
5. Fill in the Devpost form using the text above and upload `docs/architecture.png`.
6. Optional bonus: publish the builder.aws.com post.

## Demo video script (≤ 5 min)

| Time | Beat |
|------|------|
| 0:00–0:40 | **Problem.** Task lists store work; they don't decide it. Every morning you re-triage. Deadlines slip quietly. |
| 0:40–1:00 | **Who.** Students, freelancers, solo builders, small teams with 3+ concurrent projects. |
| 1:00–2:30 | **Demo, on demand.** Open a project with mixed deadlines → click *Ask M1* → show the Eisenhower matrix, reasons, next actions, confidence. Point out the `days_until` tool making urgency deterministic. |
| 2:30–3:30 | **Demo, autonomous.** Show the EventBridge rule and watcher Lambda in the console → invoke it manually → CloudWatch log `{"checked": n, "alerted": 1}` → show the SNS email for the at-risk project, and *no* email for healthy ones. |
| 3:30–4:20 | **How.** Architecture diagram: one Strands `Agent`, two triggers, structured output, DynamoDB cache. 30-second code tour of `m1.py`. |
| 4:20–5:00 | **Why it matters.** Background, safe calls, surfaces only for real decisions. Close with the repo URL. |

## builder.aws.com post outline (bonus)

Title: *Agents for Humans: Building Momentum, a background prioritization agent with Strands*

1. The problem and why a "prioritization button" was not enough.
2. Porting a raw `bedrock-runtime.invoke_model` prompt to a Strands `Agent`
   with tools — what got simpler (structured output, no JSON scraping).
3. Designing the "surface only when needed" contract: `needsHumanAttention`
   in the schema, EventBridge + SNS around it.
4. Lessons: keep date math in tools, keep the agent stateless, one artifact
   for two Lambdas.
5. What's next: AgentCore Runtime, memory across sweeps, calendar tool.
