"""Persistence adapters."""

from .seed import (
	FICTIONAL_TICKETS,
	contract_id_for_variant,
	seed_fictional_tickets,
	seeded_contract,
)
from .sqlite_repository import OutcomeRepository

__all__ = [
	"FICTIONAL_TICKETS",
	"OutcomeRepository",
	"contract_id_for_variant",
	"seed_fictional_tickets",
	"seeded_contract",
]