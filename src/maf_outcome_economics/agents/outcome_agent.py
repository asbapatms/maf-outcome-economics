"""Azure OpenAI outcome analyst agent."""

from agent_framework import Agent
from agent_framework.openai import OpenAIChatClient
from azure.identity.aio import DefaultAzureCredential

from maf_outcome_economics.config import Settings


def create_outcome_agent(settings: Settings) -> Agent:
    """Create an outcome analyst backed by Azure OpenAI and passwordless auth."""
    if not settings.azure_openai_configured:
        raise ValueError("AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_CHAT_MODEL are required")
    client = OpenAIChatClient(
        azure_endpoint=settings.azure_openai_endpoint,
        model=settings.azure_openai_chat_model,
        api_version=settings.azure_openai_api_version,
        credential=DefaultAzureCredential(),
    )
    return Agent(
        client=client,
        name="OutcomeEconomicsAnalyst",
        instructions="Analyze outcome evidence and explain economic assumptions concisely.",
    )