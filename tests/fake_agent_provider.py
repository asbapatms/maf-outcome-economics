"""Deterministic agent provider available only to tests."""

from collections import deque
from typing import TypeVar

from agent_framework import Agent
from pydantic import BaseModel

from maf_outcome_economics.domain import ReviewResult, TriageResult

StructuredResultT = TypeVar("StructuredResultT", bound=BaseModel)


class DeterministicFakeProvider:
    """Return queued outputs, then deterministic schema-valid test results."""

    def __init__(self, outputs: list[str | BaseModel] | None = None) -> None:
        self.outputs = deque(outputs or [])
        self.prompts: list[str] = []

    async def complete(
        self,
        agent: Agent,
        prompt: str,
        response_type: type[StructuredResultT],
    ) -> StructuredResultT | str:
        """Return the next queued output or a deterministic default."""
        del agent
        self.prompts.append(prompt)
        if self.outputs:
            return self.outputs.popleft()  # type: ignore[return-value]
        if response_type is TriageResult:
            return response_type.model_validate(
                {
                    "run_id": "run-test",
                    "ticket_id": "TKT-001",
                    "category": "Identity and access",
                    "priority": "P2",
                    "resolver_group": "Identity Operations",
                    "confidence": 0.95,
                    "rationale": "The fictional account is locked after a password reset.",
                }
            )
        if response_type is ReviewResult:
            return response_type.model_validate(
                {
                    "run_id": "run-test",
                    "ticket_id": "TKT-001",
                    "approved": True,
                    "notes": "The proposed routing is consistent with the ticket.",
                }
            )
        raise TypeError(f"Unsupported response type: {response_type.__name__}")