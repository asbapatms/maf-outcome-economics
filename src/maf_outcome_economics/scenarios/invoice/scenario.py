"""End-to-end invoice-processing scenario built only on generic core services."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from maf_outcome_economics.core import (
    EvidenceOperator,
    EvidenceRule,
    GenericGovernanceDecision,
    GenericGovernanceEngine,
    GovernanceAssurance,
    OutcomeContract,
    OutcomeVerificationSummary,
    OutcomeVerifier,
    ProcessDefinition,
    ProcessEconomicsComparison,
    ProcessVariant,
    ProcessVariantRole,
    ReportingPeriod,
    compare_processes,
)
from maf_outcome_economics.core.models import CoreModel

from .connector import InvoiceScenarioConnector
from .models import InvoiceCostProfile, InvoiceRecord

MANUAL_VARIANT_ID = "invoice-manual-v1"
AUTOMATED_VARIANT_ID = "invoice-automated-v1"
FIXTURE_START = datetime(2026, 8, 1, tzinfo=UTC)


class InvoiceScenarioResult(CoreModel):
    """Auditable output from the complete generic invoice economics pipeline."""

    process: ProcessDefinition
    variants: list[ProcessVariant]
    period: ReportingPeriod
    verification: OutcomeVerificationSummary
    comparison: ProcessEconomicsComparison
    decision: GenericGovernanceDecision


class InvoiceProcessingScenario:
    """Demonstrate generic outcome economics with invoice processing records."""

    id = "invoice-processing"
    name = "Invoice processing"

    def __init__(self, connector: InvoiceScenarioConnector | None = None) -> None:
        self.process = ProcessDefinition(
            id=self.id,
            name=self.name,
            process_type="accounts-payable",
        )
        self.control = ProcessVariant(
            id=MANUAL_VARIANT_ID,
            process_id=self.process.id,
            role=ProcessVariantRole.CONTROL,
            version="1",
        )
        self.treatment = ProcessVariant(
            id=AUTOMATED_VARIANT_ID,
            process_id=self.process.id,
            role=ProcessVariantRole.TREATMENT,
            version="1",
        )
        self.contract = OutcomeContract(
            id="invoice-posted-correctly",
            name="Invoice posted correctly",
            success_rules=[
                EvidenceRule(
                    metric="posted",
                    operator=EvidenceOperator.EQUALS,
                    expected_value=True,
                )
            ],
            quality_gates=[
                EvidenceRule(
                    metric="amount_matched",
                    operator=EvidenceOperator.EQUALS,
                    expected_value=True,
                ),
                EvidenceRule(
                    metric="duplicate_detected",
                    operator=EvidenceOperator.EQUALS,
                    expected_value=False,
                ),
            ],
            maximum_cost_per_verified_outcome=Decimal("5"),
            minimum_sample_size=2,
            currency="USD",
        )
        self.connector = connector or self.fixture_connector()

    async def run(
        self,
        period: ReportingPeriod | None = None,
    ) -> InvoiceScenarioResult:
        """Load, verify, compare, and govern invoice processing economics."""
        reporting_period = period or ReportingPeriod(
            start_at=FIXTURE_START,
            end_at=FIXTURE_START + timedelta(days=31),
        )
        work_units = await self.connector.load_work_units(reporting_period)
        evidence = await self.connector.load_evidence(reporting_period)
        costs = await self.connector.load_costs(reporting_period)
        verification = OutcomeVerifier().verify(self.contract, work_units, evidence)
        comparison = compare_processes(
            control_variant_id=self.control.id,
            treatment_variant_id=self.treatment.id,
            period=reporting_period,
            work_units=work_units,
            verification=verification,
            cost_entries=costs,
        )
        decision = GenericGovernanceEngine().evaluate(
            decision_id="invoice-processing-decision",
            contract=self.contract,
            comparison=comparison,
            assurance=GovernanceAssurance(
                quality_passed=True,
                safety_passed=True,
                compliance_passed=True,
                business_outcome_passed=True,
                reconciled_costs_available=True,
            ),
        )
        return InvoiceScenarioResult(
            process=self.process,
            variants=[self.control, self.treatment],
            period=reporting_period,
            verification=verification,
            comparison=comparison,
            decision=decision,
        )

    @staticmethod
    def fixture_connector() -> InvoiceScenarioConnector:
        """Build deterministic invoice records and reconciled cost profiles."""
        invoices = [
            InvoiceRecord(
                id=f"{variant_id}:invoice-{index}",
                supplier_id=f"SUP-{index:03d}",
                amount=Decimal(100 * index),
                currency="USD",
                process_variant_id=variant_id,
                received_at=FIXTURE_START + timedelta(days=index),
                completed_at=FIXTURE_START + timedelta(days=index, hours=2),
                posted=True,
                amount_matched=True,
                duplicate_detected=False,
            )
            for variant_id in (MANUAL_VARIANT_ID, AUTOMATED_VARIANT_ID)
            for index in (1, 2)
        ]
        return InvoiceScenarioConnector(
            invoices,
            [
                InvoiceCostProfile(
                    process_variant_id=MANUAL_VARIANT_ID,
                    human_processing=Decimal("12"),
                ),
                InvoiceCostProfile(
                    process_variant_id=AUTOMATED_VARIANT_ID,
                    platform=Decimal("2"),
                    model=Decimal("1"),
                ),
            ],
        )