"""Application configuration loaded from environment variables."""

from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel


class Settings(BaseModel):
    """Runtime settings that do not expose secret values."""

    azure_openai_endpoint: str | None = None
    azure_openai_chat_model: str | None = None
    azure_openai_api_version: str | None = None
    applicationinsights_connection_string: str | None = None
    database_path: Path = Path("data/outcomes.db")

    @classmethod
    def from_env(cls) -> "Settings":
        """Load local development settings from `.env` and the process environment."""
        import os

        load_dotenv()
        return cls(
            azure_openai_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            azure_openai_chat_model=os.getenv("AZURE_OPENAI_CHAT_MODEL"),
            azure_openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            applicationinsights_connection_string=os.getenv(
                "APPLICATIONINSIGHTS_CONNECTION_STRING"
            ),
            database_path=Path(os.getenv("MAF_DATABASE_PATH", "data/outcomes.db")),
        )

    @property
    def azure_openai_configured(self) -> bool:
        """Return whether the non-secret Azure OpenAI settings are present."""
        return bool(self.azure_openai_endpoint and self.azure_openai_chat_model)

    @property
    def applicationinsights_configured(self) -> bool:
        """Return whether an Application Insights connection string is present."""
        return bool(self.applicationinsights_connection_string)