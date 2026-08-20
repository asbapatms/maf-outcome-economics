"""Invoice-processing reference scenario."""

from .connector import InvoiceScenarioConnector
from .models import InvoiceCostProfile, InvoiceRecord
from .scenario import (
    AUTOMATED_VARIANT_ID,
    MANUAL_VARIANT_ID,
    InvoiceProcessingScenario,
    InvoiceScenarioResult,
)

__all__ = [
    "AUTOMATED_VARIANT_ID",
    "MANUAL_VARIANT_ID",
    "InvoiceCostProfile",
    "InvoiceProcessingScenario",
    "InvoiceRecord",
    "InvoiceScenarioConnector",
    "InvoiceScenarioResult",
]