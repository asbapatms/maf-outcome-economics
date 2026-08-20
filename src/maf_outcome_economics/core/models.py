"""Framework-neutral records for measuring process outcome economics."""

from decimal import Decimal
from enum import StrEnum

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, JsonValue, model_validator


class CoreModel(BaseModel):
    """Base model for strict generic economics records."""

    model_config = ConfigDict(extra="forbid")


class ProcessVariantRole(StrEnum):
    """Role a process variant plays in a comparison."""

    CONTROL = "control"
    TREATMENT = "treatment"


class ReportingPeriod(CoreModel):
    """Half-open time window used to load comparable process records."""

    start_at: AwareDatetime
    end_at: AwareDatetime

    @model_validator(mode="after")
    def validate_time_order(self) -> "ReportingPeriod":
        """Reject reporting windows without a positive duration."""
        if self.end_at <= self.start_at:
            raise ValueError("end_at must be later than start_at")
        return self


class CostCategory(StrEnum):
    """Framework-neutral classification for a process cost."""

    MODEL = "model"
    PLATFORM = "platform"
    HUMAN_PROCESSING = "human_processing"
    HUMAN_REVIEW = "human_review"
    RETRY = "retry"
    REWORK = "rework"
    FAILURE = "failure"
    IMPLEMENTATION = "implementation"
    LICENSE = "license"
    OTHER = "other"


class CostEvidenceStatus(StrEnum):
    """Strength and accounting treatment of cost evidence."""

    ESTIMATED = "estimated"
    MEASURED = "measured"
    RECONCILED = "reconciled"
    ALLOCATED = "allocated"


class TokenPurpose(StrEnum):
    """Business purpose assigned to one unit of model token consumption."""

    PRIMARY_WORK = "primary_work"
    REVIEW = "review"
    COORDINATION = "coordination"
    RETRY = "retry"
    REWORK = "rework"
    FAILED_WORK = "failed_work"
    UNKNOWN = "unknown"


class ProcessDefinition(CoreModel):
    """Business process whose outcomes and costs are measured."""

    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    process_type: str = Field(min_length=1)


class ProcessVariant(CoreModel):
    """Versioned control or treatment design for a business process."""

    id: str = Field(min_length=1)
    process_id: str = Field(min_length=1)
    role: ProcessVariantRole
    version: str = Field(min_length=1)


class WorkUnit(CoreModel):
    """One domain-independent item of work handled by a process variant."""

    id: str = Field(min_length=1)
    process_variant_id: str = Field(min_length=1)
    started_at: AwareDatetime
    completed_at: AwareDatetime | None = None
    attributes: dict[str, JsonValue] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_completion_time(self) -> "WorkUnit":
        """Reject completion timestamps earlier than the work start."""
        if self.completed_at is not None and self.completed_at < self.started_at:
            raise ValueError("completed_at must not be earlier than started_at")
        return self


class EvidenceRecord(CoreModel):
    """One observed fact used to verify the outcome of a work unit."""

    id: str = Field(min_length=1)
    work_unit_id: str = Field(min_length=1)
    metric: str = Field(min_length=1)
    value: JsonValue
    source: str = Field(min_length=1)
    observed_at: AwareDatetime
    provenance: dict[str, str] = Field(default_factory=dict)


class CostEntry(CoreModel):
    """One normalized process cost with evidence strength and provenance."""

    id: str = Field(min_length=1)
    process_variant_id: str = Field(min_length=1)
    work_unit_id: str | None = Field(default=None, min_length=1)
    category: CostCategory
    amount: Decimal = Field(ge=0)
    currency: str = Field(min_length=3, max_length=3)
    source: str = Field(min_length=1)
    status: CostEvidenceStatus
    reconciliation_key: str | None = Field(default=None, min_length=1)
    incurred_at: AwareDatetime


class TokenEntry(CoreModel):
    """One normalized model-token observation with work attribution."""

    id: str = Field(min_length=1)
    process_variant_id: str = Field(min_length=1)
    work_unit_id: str = Field(min_length=1)
    agent_id: str | None = Field(default=None, min_length=1)
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    purpose: TokenPurpose
    source: str = Field(min_length=1)
    trace_id: str = Field(min_length=1)
    span_id: str = Field(min_length=1)
    observed_at: AwareDatetime

    @property
    def total_tokens(self) -> int:
        """Return combined input and output token consumption."""
        return self.input_tokens + self.output_tokens
