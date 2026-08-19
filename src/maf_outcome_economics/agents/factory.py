"""Azure OpenAI-backed Microsoft Agent Framework agent factory."""

from dataclasses import dataclass

from agent_framework import Agent
from agent_framework.openai import OpenAIChatClient
from azure.identity.aio import DefaultAzureCredential

from maf_outcome_economics.config import Settings

from .provider import MAFAgentProvider
from .support_agents import ReviewAgent, TriageAgent


@dataclass(slots=True)
class SupportAgentSuite:
    """Live triage and review agents sharing one Azure credential."""

    triage: TriageAgent
    review: ReviewAgent
    credential: DefaultAzureCredential

    async def close(self) -> None:
        """Close the shared Azure credential transport."""
        await self.credential.close()


def create_support_agent_suite(settings: Settings) -> SupportAgentSuite:
    """Create live MAF agents backed by the installed Azure OpenAI client."""
    if not settings.azure_openai_configured:
        raise ValueError("AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_CHAT_MODEL are required")

    credential = DefaultAzureCredential()
    client = OpenAIChatClient(
        azure_endpoint=settings.azure_openai_endpoint,
        model=settings.azure_openai_chat_model,
        api_version=settings.azure_openai_api_version,
        credential=credential,
    )
    provider = MAFAgentProvider()
    triage_agent = Agent(
        client=client,
        id=TriageAgent.ID,
        name=TriageAgent.NAME,
        instructions=(
            "Classify fictional support tickets and return only strict JSON "
            "matching the requested schema."
        ),
    )
    review_agent = Agent(
        client=client,
        id=ReviewAgent.ID,
        name=ReviewAgent.NAME,
        instructions=(
            "Review fictional support-ticket triage and return only strict JSON "
            "matching the requested schema."
        ),
    )
    return SupportAgentSuite(
        triage=TriageAgent(triage_agent, provider),
        review=ReviewAgent(review_agent, provider),
        credential=credential,
    )