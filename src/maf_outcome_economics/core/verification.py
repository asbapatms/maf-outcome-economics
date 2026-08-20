"""Declarative, domain-independent verification of business outcomes."""

from collections.abc import Iterable
from decimal import Decimal
from enum import StrEnum
from numbers import Real

from pydantic import Field, JsonValue, model_validator

from .models import CoreModel, EvidenceRecord, WorkUnit


class EvidenceOperator(StrEnum):
    """Comparison operation applied to observed evidence."""

    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    GREATER_THAN_OR_EQUAL = "greater_than_or_equal"
    LESS_THAN = "less_than"
    LESS_THAN_OR_EQUAL = "less_than_or_equal"


class EvidenceRule(CoreModel):
    """Declarative requirement for one evidence metric."""

    metric: str = Field(min_length=1)
    operator: EvidenceOperator
    expected_value: JsonValue
    required: bool = True


class OutcomeContract(CoreModel):
    """Domain-independent definition of a verified business outcome."""

    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    success_rules: list[EvidenceRule] = Field(min_length=1)
    quality_gates: list[EvidenceRule]
    maximum_cost_per_verified_outcome: Decimal = Field(ge=0)
    minimum_sample_size: int = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3)


class RuleEvaluation(CoreModel):
    """Auditable result of applying one rule to one work unit."""

    metric: str = Field(min_length=1)
    operator: EvidenceOperator
    expected_value: JsonValue
    observed_value: JsonValue | None = None
    required: bool
    evidence_found: bool
    evidence_id: str | None = Field(default=None, min_length=1)
    passed: bool


class WorkUnitVerification(CoreModel):
    """Rule-level verification result for one business work unit."""

    work_unit_id: str = Field(min_length=1)
    passed: bool
    success_rules_passed: bool
    quality_gates_passed: bool
    evaluations: list[RuleEvaluation]

    @model_validator(mode="after")
    def validate_passed(self) -> "WorkUnitVerification":
        """Reject a result inconsistent with its rule-group decisions."""
        expected = self.success_rules_passed and self.quality_gates_passed
        if self.passed != expected:
            raise ValueError("passed must require success rules and quality gates")
        return self


class OutcomeVerificationSummary(CoreModel):
    """Batch verification results and evidence sufficiency for a contract."""

    contract_id: str = Field(min_length=1)
    total_work_units: int = Field(ge=0)
    verified_outcomes: int = Field(ge=0)
    minimum_sample_size: int = Field(gt=0)
    minimum_sample_size_met: bool
    results: list[WorkUnitVerification]

    @model_validator(mode="after")
    def validate_counts(self) -> "OutcomeVerificationSummary":
        """Reject counts inconsistent with the contained work-unit results."""
        if self.total_work_units != len(self.results):
            raise ValueError("total_work_units must equal the result count")
        if self.verified_outcomes != sum(result.passed for result in self.results):
            raise ValueError("verified_outcomes must equal the passing result count")
        if self.minimum_sample_size_met != (
            self.total_work_units >= self.minimum_sample_size
        ):
            raise ValueError("minimum_sample_size_met is inconsistent")
        return self


class OutcomeVerifier:
    """Evaluate evidence rules without knowledge of the source business domain."""

    def verify(
        self,
        contract: OutcomeContract,
        work_units: Iterable[WorkUnit],
        evidence: Iterable[EvidenceRecord],
    ) -> OutcomeVerificationSummary:
        """Verify each unique work unit against the contract's evidence rules."""
        unique_work_units = {work_unit.id: work_unit for work_unit in work_units}
        evidence_by_work_unit = self._latest_evidence(
            evidence,
            work_unit_ids=set(unique_work_units),
        )
        results = [
            self._verify_work_unit(
                work_unit_id,
                contract,
                evidence_by_work_unit.get(work_unit_id, {}),
            )
            for work_unit_id in unique_work_units
        ]
        total_work_units = len(results)
        return OutcomeVerificationSummary(
            contract_id=contract.id,
            total_work_units=total_work_units,
            verified_outcomes=sum(result.passed for result in results),
            minimum_sample_size=contract.minimum_sample_size,
            minimum_sample_size_met=total_work_units >= contract.minimum_sample_size,
            results=results,
        )

    def _verify_work_unit(
        self,
        work_unit_id: str,
        contract: OutcomeContract,
        evidence_by_metric: dict[str, EvidenceRecord],
    ) -> WorkUnitVerification:
        success_evaluations = [
            self._evaluate(rule, evidence_by_metric.get(rule.metric))
            for rule in contract.success_rules
        ]
        quality_evaluations = [
            self._evaluate(rule, evidence_by_metric.get(rule.metric))
            for rule in contract.quality_gates
        ]
        success_rules_passed = all(result.passed for result in success_evaluations)
        quality_gates_passed = all(result.passed for result in quality_evaluations)
        return WorkUnitVerification(
            work_unit_id=work_unit_id,
            passed=success_rules_passed and quality_gates_passed,
            success_rules_passed=success_rules_passed,
            quality_gates_passed=quality_gates_passed,
            evaluations=success_evaluations + quality_evaluations,
        )

    @staticmethod
    def _latest_evidence(
        evidence: Iterable[EvidenceRecord],
        *,
        work_unit_ids: set[str],
    ) -> dict[str, dict[str, EvidenceRecord]]:
        latest: dict[str, dict[str, EvidenceRecord]] = {}
        for record in evidence:
            if record.work_unit_id not in work_unit_ids:
                continue
            by_metric = latest.setdefault(record.work_unit_id, {})
            current = by_metric.get(record.metric)
            if current is None or (record.observed_at, record.id) > (
                current.observed_at,
                current.id,
            ):
                by_metric[record.metric] = record
        return latest

    def _evaluate(
        self,
        rule: EvidenceRule,
        evidence: EvidenceRecord | None,
    ) -> RuleEvaluation:
        if evidence is None:
            return RuleEvaluation(
                metric=rule.metric,
                operator=rule.operator,
                expected_value=rule.expected_value,
                required=rule.required,
                evidence_found=False,
                passed=not rule.required,
            )
        return RuleEvaluation(
            metric=rule.metric,
            operator=rule.operator,
            expected_value=rule.expected_value,
            observed_value=evidence.value,
            required=rule.required,
            evidence_found=True,
            evidence_id=evidence.id,
            passed=self._compare(evidence.value, rule.operator, rule.expected_value),
        )

    @classmethod
    def _compare(
        cls,
        observed: JsonValue,
        operator: EvidenceOperator,
        expected: JsonValue,
    ) -> bool:
        if operator is EvidenceOperator.EQUALS:
            return cls._equals(observed, expected)
        if operator is EvidenceOperator.NOT_EQUALS:
            return not cls._equals(observed, expected)

        comparable = cls._ordered_values(observed, expected)
        if comparable is None:
            return False
        left, right = comparable
        if isinstance(left, Decimal) and isinstance(right, Decimal):
            return cls._compare_ordered(left, right, operator)
        if isinstance(left, str) and isinstance(right, str):
            return cls._compare_ordered(left, right, operator)
        return False

    @staticmethod
    def _compare_ordered(
        observed: Decimal | str,
        expected: Decimal | str,
        operator: EvidenceOperator,
    ) -> bool:
        if type(observed) is not type(expected):
            return False
        if operator is EvidenceOperator.GREATER_THAN:
            return observed > expected  # type: ignore[operator]
        if operator is EvidenceOperator.GREATER_THAN_OR_EQUAL:
            return observed >= expected  # type: ignore[operator]
        if operator is EvidenceOperator.LESS_THAN:
            return observed < expected  # type: ignore[operator]
        return observed <= expected  # type: ignore[operator]

    @staticmethod
    def _equals(observed: JsonValue, expected: JsonValue) -> bool:
        if isinstance(observed, bool) or isinstance(expected, bool):
            return type(observed) is type(expected) and observed == expected
        if isinstance(observed, Real) and isinstance(expected, Real):
            return Decimal(str(observed)) == Decimal(str(expected))
        return observed == expected

    @staticmethod
    def _ordered_values(
        observed: JsonValue,
        expected: JsonValue,
    ) -> tuple[Decimal, Decimal] | tuple[str, str] | None:
        if (
            isinstance(observed, Real)
            and not isinstance(observed, bool)
            and isinstance(expected, Real)
            and not isinstance(expected, bool)
        ):
            return Decimal(str(observed)), Decimal(str(expected))
        if isinstance(observed, str) and isinstance(expected, str):
            return observed, expected
        return None
