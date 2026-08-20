"""Generic outcome-economics analysis for persisted ticket scenario runs."""

from datetime import datetime, timedelta
from decimal import Decimal

from maf_outcome_economics.connectors import (
    MAFTelemetryCostConnector,
    MAFTelemetryTokenConnector,
)
from maf_outcome_economics.core import (
    EvidenceOperator,
    EvidenceRule,
    GenericGovernanceDecision,
    GenericGovernanceEngine,
    GovernanceAssurance,
    OutcomeContract,
    OutcomeVerificationSummary,
    OutcomeVerifier,
    ProcessEconomicsComparison,
    ReportingPeriod,
    ReviewTokenAttribution,
    TokenEfficiencyComparison,
    TokenGovernancePolicy,
    attribute_review_tokens,
    compare_processes,
    compare_token_efficiency,
)
from maf_outcome_economics.core.models import CoreModel
from maf_outcome_economics.domain import OutcomeContract as TicketOutcomeContract
from maf_outcome_economics.domain import WorkflowVariant
from maf_outcome_economics.persistence.sqlite_repository import OutcomeRepository

from .connector import TICKET_VARIANT_IDS, TicketScenarioConnector
from .seed import contract_id_for_variant


class TicketGenericAnalysis(CoreModel):
    """Generic verification, comparison, and governance for ticket runs."""

    period: ReportingPeriod
    verification: OutcomeVerificationSummary
    comparison: ProcessEconomicsComparison
    token_comparison: TokenEfficiencyComparison
    control_review_attribution: ReviewTokenAttribution
    treatment_review_attribution: ReviewTokenAttribution
    decision: GenericGovernanceDecision


class TicketEconomicsAnalyzer:
    """Analyze persisted ticket evidence entirely through generic core DTOs."""

    def __init__(self, repository: OutcomeRepository) -> None:
        self._repository = repository

    async def analyze(self) -> TicketGenericAnalysis:
        """Normalize persisted records and evaluate generic ticket economics."""
        period = self._reporting_period()
        ticket_connector = TicketScenarioConnector(self._repository)
        work_units = await ticket_connector.load_work_units(period)
        evidence = await ticket_connector.load_evidence(period)
        review_outcomes = await ticket_connector.load_review_outcomes(period)
        pricing = self._repository.list_pricing()
        cost_connector = MAFTelemetryCostConnector(
            self._repository,
            pricing,
            {
                variant.value: generic_id
                for variant, generic_id in TICKET_VARIANT_IDS.items()
            },
        )
        costs = await cost_connector.load_costs(period)
        token_connector = MAFTelemetryTokenConnector(
            self._repository,
            {
                variant.value: generic_id
                for variant, generic_id in TICKET_VARIANT_IDS.items()
            },
        )
        tokens = await token_connector.load_tokens(period)
        ticket_contract = self._ticket_contract(WorkflowVariant.OPTIMIZED)
        contract = self._generic_contract(ticket_contract)
        verification = OutcomeVerifier().verify(contract, work_units, evidence)
        comparison = compare_processes(
            control_variant_id=TICKET_VARIANT_IDS[WorkflowVariant.BASELINE],
            treatment_variant_id=TICKET_VARIANT_IDS[WorkflowVariant.OPTIMIZED],
            period=period,
            work_units=work_units,
            verification=verification,
            cost_entries=costs,
        )
        token_comparison = compare_token_efficiency(
            control_variant_id=TICKET_VARIANT_IDS[WorkflowVariant.BASELINE],
            treatment_variant_id=TICKET_VARIANT_IDS[WorkflowVariant.OPTIMIZED],
            period=period,
            work_units=work_units,
            verification=verification,
            token_entries=tokens,
        )
        control_work_unit_ids = {
            work_unit.id
            for work_unit in work_units
            if work_unit.process_variant_id
            == TICKET_VARIANT_IDS[WorkflowVariant.BASELINE]
        }
        treatment_work_unit_ids = {
            work_unit.id
            for work_unit in work_units
            if work_unit.process_variant_id
            == TICKET_VARIANT_IDS[WorkflowVariant.OPTIMIZED]
        }
        control_review_attribution = attribute_review_tokens(
            (
                entry
                for entry in tokens
                if entry.process_variant_id
                == TICKET_VARIANT_IDS[WorkflowVariant.BASELINE]
            ),
            {
                work_unit_id: outcome
                for work_unit_id, outcome in review_outcomes.items()
                if work_unit_id in control_work_unit_ids
            },
        )
        treatment_review_attribution = attribute_review_tokens(
            (
                entry
                for entry in tokens
                if entry.process_variant_id
                == TICKET_VARIANT_IDS[WorkflowVariant.OPTIMIZED]
            ),
            {
                work_unit_id: outcome
                for work_unit_id, outcome in review_outcomes.items()
                if work_unit_id in treatment_work_unit_ids
            },
        )
        decision = GenericGovernanceEngine().evaluate(
            decision_id="ticket-generic-governance",
            contract=contract,
            comparison=comparison,
            assurance=self._assurance(ticket_contract),
            token_policy=TokenGovernancePolicy(
                maximum_tokens_per_verified_outcome=Decimal(300),
                minimum_efficiency_improvement=Decimal("0.1"),
                maximum_review_token_ratio=Decimal("0.4"),
                maximum_retry_token_ratio=Decimal("0.1"),
            ),
            token_comparison=token_comparison,
            review_attribution=treatment_review_attribution,
        )
        return TicketGenericAnalysis(
            period=period,
            verification=verification,
            comparison=comparison,
            token_comparison=token_comparison,
            control_review_attribution=control_review_attribution,
            treatment_review_attribution=treatment_review_attribution,
            decision=decision,
        )

    def _reporting_period(self) -> ReportingPeriod:
        completed_runs = [
            row
            for row in self._repository.list_runs()
            if row.get("status") == "completed" and row.get("completed_at")
        ]
        if not completed_runs:
            raise ValueError("Generic ticket analysis requires completed runs")
        start_at = min(
            datetime.fromisoformat(str(row["started_at"])) for row in completed_runs
        )
        latest_timestamps = [
            datetime.fromisoformat(str(row["completed_at"]))
            for row in completed_runs
        ]
        completed_run_ids = {str(row["id"]) for row in completed_runs}
        latest_timestamps.extend(
            datetime.fromisoformat(str(row["recorded_at"]))
            for row in self._repository.list_billable_model_usage()
            if str(row.get("run_id") or "") in completed_run_ids
        )
        end_at = max(latest_timestamps) + timedelta(microseconds=1)
        return ReportingPeriod(start_at=start_at, end_at=end_at)

    def _ticket_contract(self, variant: WorkflowVariant) -> TicketOutcomeContract:
        contract = self._repository.get_outcome_contract(contract_id_for_variant(variant))
        if contract is None:
            raise ValueError(f"Missing ticket contract for {variant.value}")
        return contract

    @staticmethod
    def _generic_contract(contract: TicketOutcomeContract) -> OutcomeContract:
        return OutcomeContract(
            id="ticket-routing-accepted",
            name="Ticket routed correctly",
            success_rules=[
                EvidenceRule(
                    metric="routing_accepted",
                    operator=EvidenceOperator.EQUALS,
                    expected_value=True,
                )
            ],
            quality_gates=[],
            maximum_cost_per_verified_outcome=(
                contract.maximum_cost_per_accepted_outcome
            ),
            minimum_sample_size=1,
            currency=contract.budget_currency,
        )

    def _assurance(self, contract: TicketOutcomeContract) -> GovernanceAssurance:
        verifications = self._repository.list_routing_verifications(
            WorkflowVariant.OPTIMIZED
        )
        if not verifications:
            return GovernanceAssurance(
                quality_passed=None,
                safety_passed=None,
                compliance_passed=None,
                business_outcome_passed=None,
                reconciled_costs_available=False,
            )
        total = Decimal(len(verifications))
        acceptance_rate = Decimal(sum(item.accepted for item in verifications)) / total
        average_quality = (
            sum(
                (item.quality_score for item in verifications),
                start=Decimal(0),
            )
            / total
        )
        critical = [
            item for item in verifications if item.critical_priority_expected
        ]
        critical_recall = (
            Decimal(
                sum(item.critical_priority_recalled is True for item in critical)
            )
            / Decimal(len(critical))
            if critical
            else Decimal(1)
        )
        return GovernanceAssurance(
            quality_passed=average_quality >= contract.minimum_quality_score,
            safety_passed=(
                critical_recall >= contract.minimum_critical_priority_recall
            ),
            compliance_passed=True,
            business_outcome_passed=(
                acceptance_rate >= contract.minimum_acceptance_rate
            ),
            reconciled_costs_available=False,
        )