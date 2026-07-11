from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    app_name: str = "Momentum API"
    debug: bool = False
    aws_region: str = "us-east-1"
    dynamodb_table_projects: str = "momentum-projects"
    dynamodb_table_tasks: str = "momentum-tasks"
    bedrock_model_id: str = "amazon.nova-lite-v1:0"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
