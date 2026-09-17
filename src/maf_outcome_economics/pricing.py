"""Helpers for resolving model pricing records against telemetry labels."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence

from maf_outcome_economics.domain import PricingRecord

_AZURE_OPENAI_PROVIDER = "azure.ai.openai"
_DATED_AZURE_MODEL = re.compile(r"^(?P<base>.+)-\d{4}-\d{2}-\d{2}$")


def build_pricing_index(
    pricing: Sequence[PricingRecord],
) -> dict[tuple[str, str], PricingRecord]:
    """Return pricing records keyed by provider and model."""
    return {(record.provider, record.model): record for record in pricing}


def resolve_pricing(
    pricing: Mapping[tuple[str, str], PricingRecord],
    *,
    provider: str,
    model: str,
) -> PricingRecord | None:
    """Resolve exact pricing, with Azure OpenAI dated response-model fallback."""
    exact = pricing.get((provider, model))
    if exact is not None:
        return exact
    if provider != _AZURE_OPENAI_PROVIDER:
        return None
    match = _DATED_AZURE_MODEL.match(model)
    if match is None:
        return None
    return pricing.get((provider, match.group("base")))
