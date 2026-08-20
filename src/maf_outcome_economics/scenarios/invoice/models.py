"""Invoice-domain records used by the invoice-processing reference scenario."""

from decimal import Decimal

from pydantic import AwareDatetime, Field

from maf_outcome_economics.core.models import CoreModel


class InvoiceRecord(CoreModel):
    """One source invoice and its independently observed processing outcome."""

    id: str = Field(min_length=1)
    supplier_id: str = Field(min_length=1)
    amount: Decimal = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3)
    process_variant_id: str = Field(min_length=1)
    received_at: AwareDatetime
    completed_at: AwareDatetime
    posted: bool
    amount_matched: bool
    duplicate_detected: bool


class InvoiceCostProfile(CoreModel):
    """Reconciled per-invoice operating costs for one process variant."""

    process_variant_id: str = Field(min_length=1)
    human_processing: Decimal = Field(default=Decimal(0), ge=0)
    platform: Decimal = Field(default=Decimal(0), ge=0)
    model: Decimal = Field(default=Decimal(0), ge=0)