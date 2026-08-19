"""Provider boundary for structured Microsoft Agent Framework execution."""

from typing import Protocol, TypeVar

from agent_framework import Agent
from pydantic import BaseModel, ValidationError

StructuredResultT = TypeVar("StructuredResultT", bound=BaseModel)


class MalformedAgentOutputError(ValueError):
    """Raised when an agent response is not valid for its required schema."""


class AgentProvider(Protocol):
    """Execute an agent and return structured output or raw response text."""

    async def complete(
        self,
        agent: Agent,
        prompt: str,
        response_type: type[StructuredResultT],
    ) -> StructuredResultT | str:
        """Run an agent with a required structured response type."""
        ...


class MAFAgentProvider:
    """Execute real Microsoft Agent Framework agents."""

    async def complete(
        self,
        agent: Agent,
        prompt: str,
        response_type: type[StructuredResultT],
    ) -> StructuredResultT | str:
        """Run a MAF agent using its installed Pydantic response-format support."""
        response = await agent.run(
            prompt,
            stream=False,
            options={"response_format": response_type},
        )
        try:
            value = response.value
        except (ValidationError, ValueError) as error:
            raise MalformedAgentOutputError(response.text) from error
        return value if isinstance(value, response_type) else response.text


def parse_json_output(
    output: str,
    response_type: type[StructuredResultT],
) -> StructuredResultT:
    """Parse strict JSON, tolerating one surrounding fence or text wrapper."""
    stripped = output.strip()
    candidates = [stripped]
    if stripped.startswith("```") and stripped.endswith("```"):
        fenced = stripped[3:-3].strip()
        if fenced.lower().startswith("json"):
            fenced = fenced[4:].strip()
        candidates.append(fenced)
    object_start = stripped.find("{")
    object_end = stripped.rfind("}")
    if object_start >= 0 and object_end > object_start:
        candidates.append(stripped[object_start : object_end + 1])

    validation_error: ValidationError | None = None
    for candidate in dict.fromkeys(candidates):
        try:
            return response_type.model_validate_json(candidate)
        except ValidationError as error:
            validation_error = error
    raise MalformedAgentOutputError(
        f"Response did not match {response_type.__name__}"
    ) from validation_error