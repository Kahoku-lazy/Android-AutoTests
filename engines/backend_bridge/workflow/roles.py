from __future__ import annotations

from dataclasses import dataclass

from engines.ae_harness.agents.creator import AgentBundle
from engines.ae_harness.middleware import ObservationMiddleware

__all__ = ["SopRoles"]


@dataclass(frozen=True)
class SopRoles:
    executor: AgentBundle
    verifier: AgentBundle
    observer: ObservationMiddleware
