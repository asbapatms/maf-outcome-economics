"""Persistence adapters."""

from .seed import FICTIONAL_TICKETS, seed_fictional_tickets
from .sqlite_repository import OutcomeRepository

__all__ = ["FICTIONAL_TICKETS", "OutcomeRepository", "seed_fictional_tickets"]