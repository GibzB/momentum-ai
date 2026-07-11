import json
import logging
from functools import lru_cache

import boto3
from botocore.exceptions import ClientError
from fastapi import HTTPException

from app.core.config import settings

logger = logging.getLogger(__name__)


@lru_cache()
def get_bedrock_client():
    """Get cached Bedrock runtime client."""
    return boto3.client("bedrock-runtime", region_name=settings.aws_region)


def invoke_model(prompt: str, system_prompt: str) -> dict:
    """Invoke Amazon Bedrock with structured prompt.

    Args:
        prompt: User message with task/project context.
        system_prompt: System instructions for M1 behavior.

    Returns:
        Parsed JSON response from the model.

    Raises:
        HTTPException: If Bedrock call fails or response is invalid.
    """
    client = get_bedrock_client()

    body = {
        "messages": [
            {"role": "user", "content": [{"text": prompt}]},
        ],
        "system": [{"text": system_prompt}],
        "inferenceConfig": {
            "maxTokens": 4096,
            "temperature": 0.2,
            "topP": 0.9,
        },
    }

    try:
        response = client.invoke_model(
            modelId=settings.bedrock_model_id,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(body),
        )

        response_body = json.loads(response["body"].read())
        output_text = response_body["output"]["message"]["content"][0]["text"]

        # Parse JSON from response — handle markdown code blocks
        cleaned = output_text.strip()
        if cleaned.startswith("```"):
            # Strip ```json and trailing ```
            lines = cleaned.split("\n")
            cleaned = "\n".join(lines[1:-1])

        return json.loads(cleaned)

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        logger.error(f"Bedrock API error: {error_code} - {e}")

        if error_code == "ThrottlingException":
            raise HTTPException(
                status_code=429,
                detail="AI service is temporarily busy. Please try again.",
            )
        elif error_code == "ValidationException":
            raise HTTPException(
                status_code=400, detail="Invalid request to AI service."
            )
        else:
            raise HTTPException(
                status_code=502, detail="AI service unavailable."
            )

    except (json.JSONDecodeError, KeyError, IndexError) as e:
        logger.error(f"Failed to parse Bedrock response: {e}")
        raise HTTPException(
            status_code=502,
            detail="AI returned an invalid response. Please try again.",
        )
