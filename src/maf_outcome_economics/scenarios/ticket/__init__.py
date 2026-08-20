"""Support-ticket triage reference scenario."""

from maf_outcome_economics.domain import (
	ReviewResult,
	RoutingVerificationResult,
	Ticket,
	TicketWorkflowInput,
	TicketWorkflowResult,
	TicketWorkflowState,
	TriageResult,
	WorkflowVariant,
)

from .analysis import TicketEconomicsAnalyzer, TicketGenericAnalysis
from .connector import TICKET_VARIANT_IDS, TicketScenarioConnector
from .scenario import TicketScenario
from .seed import (
	DEMO_SCENARIO_TICKETS,
	FICTIONAL_TICKETS,
	DemoScenario,
	contract_id_for_variant,
	seed_demo_scenario,
	seed_fictional_tickets,
	seeded_contract,
)
from .verification import verify_routing_outcome
from .workflow import create_ticket_workflow, stream_ticket_workflow

__all__ = [
	"DEMO_SCENARIO_TICKETS",
	"FICTIONAL_TICKETS",
	"DemoScenario",
	"ReviewResult",
	"RoutingVerificationResult",
	"Ticket",
	"TicketEconomicsAnalyzer",
	"TicketGenericAnalysis",
	"TicketScenario",
	"TicketScenarioConnector",
	"TicketWorkflowInput",
	"TicketWorkflowResult",
	"TicketWorkflowState",
	"TriageResult",
	"WorkflowVariant",
	"TICKET_VARIANT_IDS",
	"contract_id_for_variant",
	"create_ticket_workflow",
	"seed_demo_scenario",
	"seed_fictional_tickets",
	"seeded_contract",
	"stream_ticket_workflow",
	"verify_routing_outcome",
]