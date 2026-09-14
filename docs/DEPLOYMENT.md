# Deployment

## Prerequisites

- AWS account with Bedrock model access enabled for **Amazon Nova Lite** in `us-east-1`
  (Bedrock console → Model access → request `amazon.nova-lite-v1:0`).
- Terraform ≥ 1.7, AWS CLI v2, Python 3.12, Node 20.
- An AWS CLI profile with permissions to create Lambda, API Gateway, DynamoDB,
  EventBridge, SNS, IAM, CloudWatch and Amplify resources.

## One-command deploy

```bash
./scripts/deploy.sh dev <aws-profile>
```

This runs `terraform apply` with `infrastructure/terraform/environments/dev/terraform.tfvars`,
packages `backend/` once, and pushes the same zip to both Lambdas:

| Lambda | Handler | Trigger |
|--------|---------|---------|
| `momentum-api-dev` | `app.main.handler` | HTTP API Gateway |
| `momentum-watcher-dev` | `app.agent.watcher.handler` | EventBridge `rate(6 hours)` |

## Receiving alerts

Set `alert_email` in the tfvars file (or `-var alert_email=you@example.com`) and
confirm the SNS subscription email. The watcher publishes to
`momentum-alerts-<env>` **only** when M1 sets `needsHumanAttention=true`.

Trigger a sweep manually:

```bash
aws lambda invoke --function-name momentum-watcher-dev /dev/stdout
# {"checked": 3, "alerted": 1, "failed": 0}
```

## Environment variables (backend)

| Variable | Default | Purpose |
|----------|---------|---------|
| `AWS_REGION` | `us-east-1` | Bedrock / DynamoDB / SNS region |
| `DYNAMODB_TABLE_PROJECTS` | `momentum-projects` | |
| `DYNAMODB_TABLE_TASKS` | `momentum-tasks` | |
| `BEDROCK_MODEL_ID` | `amazon.nova-lite-v1:0` | Any Bedrock model supported by Strands `BedrockModel` |
| `ALERTS_TOPIC_ARN` | — | Set automatically on the watcher Lambda |
| `DEBUG` | `false` | Enables `/docs` |

## CI/CD

`.github/workflows/deploy.yml` (manual dispatch) does the same steps using a
GitHub OIDC role. Set repository variables `AWS_DEPLOY_ROLE_ARN` (from
`terraform output deploy_role_arn`) and `AMPLIFY_APP_ID`.

## Running M1 on Amazon Bedrock AgentCore Runtime (optional)

The agent is plain Strands code, so it can also be hosted on AgentCore Runtime:

```python
# agentcore_entry.py
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from app.agent.m1 import create_m1_agent

app = BedrockAgentCoreApp()
agent = create_m1_agent()

@app.entrypoint
def invoke(payload):
    return agent(payload["prompt"]).message

app.run()
```

```bash
pip install bedrock-agentcore bedrock-agentcore-starter-toolkit
agentcore configure -e agentcore_entry.py
agentcore launch
```

See <https://aws.github.io/bedrock-agentcore-starter-toolkit/user-guide/runtime/quickstart.html>.
