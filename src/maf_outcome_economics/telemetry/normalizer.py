"""Normalize OpenTelemetry spans and Microsoft Agent Framework attributes."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from math import isfinite
from typing import Any

from opentelemetry.sdk.trace import ReadableSpan

SENSITIVE_ATTRIBUTE_KEYS = frozenset(
    {
        "gen_ai.input.messages",
        "gen_ai.output.messages",
        "gen_ai.system_instructions",
        "gen_ai.system.message",
        "gen_ai.user.message",
        "gen_ai.assistant.message",
        "gen_ai.tool.message",
        "gen_ai.tool.call.arguments",
        "gen_ai.tool.call.result",
    }
)


@dataclass(frozen=True, slots=True)
class NormalizedSpan:
    """Storage-ready OpenTelemetry span with normalized MAF metadata."""

    trace_id: str
    span_id: str
    parent_span_id: str | None
    name: str
    started_at: datetime
    ended_at: datetime | None
    status_code: str
    status_description: str | None
    attributes: dict[str, Any]
    input_tokens: int
    output_tokens: int
    has_token_usage: bool
    agent_id: str | None
    agent_name: str | None
    provider_name: str | None
    request_model: str | None
    response_model: str | None
    operation_name: str | None
    workflow_id: str | None
    session_id: str | None
    executor_id: str | None
    message_source: str | None
    message_target: str | None
    error_type: str | None

    @property
    def is_billable_model_call(self) -> bool:
        """Return whether this is a semantic chat model-call span."""
        return (
            self.operation_name == "chat"
            and bool(self.request_model or self.response_model)
            and self.has_token_usage
        )


class MAFSpanNormalizer:
    """Extract billing and workflow metadata from MAF OpenTelemetry spans."""

    def normalize(self, span: ReadableSpan) -> NormalizedSpan:
        """Convert a readable span into a safe storage representation."""
        if span.context is None or span.start_time is None:
            raise ValueError("Exported spans require a context and start timestamp")

        attributes = {
            key: self._json_value(value)
            for key, value in (span.attributes or {}).items()
            if key not in SENSITIVE_ATTRIBUTE_KEYS
        }
        parent_span_id = None
        if span.parent is not None and span.parent.span_id:
            parent_span_id = f"{span.parent.span_id:016x}"
        input_tokens = self._token_count(attributes, "gen_ai.usage.input_tokens")
        output_tokens = self._token_count(attributes, "gen_ai.usage.output_tokens")

        return NormalizedSpan(
            trace_id=f"{span.context.trace_id:032x}",
            span_id=f"{span.context.span_id:016x}",
            parent_span_id=parent_span_id,
            name=span.name,
            started_at=self._timestamp(span.start_time),
            ended_at=self._timestamp(span.end_time) if span.end_time is not None else None,
            status_code=span.status.status_code.name,
            status_description=span.status.description,
            attributes=attributes,
            input_tokens=input_tokens or 0,
            output_tokens=output_tokens or 0,
            has_token_usage=input_tokens is not None and output_tokens is not None,
            agent_id=self._text(attributes, "gen_ai.agent.id"),
            agent_name=self._text(attributes, "gen_ai.agent.name"),
            provider_name=self._text(attributes, "gen_ai.provider.name"),
            request_model=self._text(attributes, "gen_ai.request.model"),
            response_model=self._text(attributes, "gen_ai.response.model"),
            operation_name=self._text(attributes, "gen_ai.operation.name"),
            workflow_id=self._text(attributes, "workflow.id"),
            session_id=self._first_text(attributes, "session.id", "gen_ai.conversation.id"),
            executor_id=self._text(attributes, "executor.id"),
            message_source=self._first_text(
                attributes, "message.source_id", "message.source"
            ),
            message_target=self._first_text(
                attributes, "message.target_id", "message.target"
            ),
            error_type=self._text(attributes, "error.type"),
        )

    @staticmethod
    def _timestamp(nanoseconds: int) -> datetime:
        return datetime.fromtimestamp(nanoseconds / 1_000_000_000, UTC)

    @classmethod
    def _json_value(cls, value: Any) -> Any:
        if isinstance(value, Mapping):
            return {str(key): cls._json_value(item) for key, item in value.items()}
        if isinstance(value, Sequence) and not isinstance(value, str):
            return [cls._json_value(item) for item in value]
        return value

    @staticmethod
    def _token_count(attributes: Mapping[str, Any], key: str) -> int | None:
        value = attributes.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return None
        if isinstance(value, float) and not isfinite(value):
            return None
        integer = int(value)
        return integer if integer >= 0 and integer == value else None

    @staticmethod
    def _text(attributes: Mapping[str, Any], key: str) -> str | None:
        value = attributes.get(key)
        return str(value) if value is not None else None

    @classmethod
    def _first_text(cls, attributes: Mapping[str, Any], *keys: str) -> str | None:
        return next((value for key in keys if (value := cls._text(attributes, key))), None)