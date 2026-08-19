"""Outcome verification rules."""

from .routing import verify_routing_outcome
from .rules import verify_outcome

__all__ = ["verify_outcome", "verify_routing_outcome"]