from functools import lru_cache

import boto3

from app.core.config import settings


@lru_cache
def get_dynamodb_resource():
    """Get cached DynamoDB resource. Singleton per Lambda container."""
    return boto3.resource("dynamodb", region_name=settings.aws_region)


def get_projects_table():
    """Get DynamoDB projects table."""
    return get_dynamodb_resource().Table(settings.dynamodb_table_projects)


def get_tasks_table():
    """Get DynamoDB tasks table."""
    return get_dynamodb_resource().Table(settings.dynamodb_table_tasks)
