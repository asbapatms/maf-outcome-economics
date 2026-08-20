"""Framework-neutral contracts for normalizing external process data."""

from typing import Protocol

from maf_outcome_economics.core import (
    CostEntry,
    EvidenceRecord,
    ReportingPeriod,
    TokenEntry,
    WorkUnit,
)


class WorkUnitSource(Protocol):
    """Load normalized work units for a reporting period."""

    async def load_work_units(self, period: ReportingPeriod) -> list[WorkUnit]:
        """Return work units whose source timestamps fall within the period."""
        ...


class EvidenceSource(Protocol):
    """Load normalized outcome evidence for a reporting period."""

    async def load_evidence(self, period: ReportingPeriod) -> list[EvidenceRecord]:
        """Return evidence whose observation timestamps fall within the period."""
        ...


class CostSource(Protocol):
    """Load normalized costs for a reporting period."""

    async def load_costs(self, period: ReportingPeriod) -> list[CostEntry]:
        """Return costs whose incurred timestamps fall within the period."""
        ...


class TokenSource(Protocol):
    """Load normalized model-token observations for a reporting period."""

    async def load_tokens(self, period: ReportingPeriod) -> list[TokenEntry]:
        """Return token observations whose timestamps fall within the period."""
        ...
