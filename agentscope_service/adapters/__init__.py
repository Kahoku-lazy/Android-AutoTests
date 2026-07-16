"""Adapters — thin wrappers around Django app APIs for AgentScope Tools.

Tools call these adapters instead of importing apps.*.models / apps.*.api directly.
This creates a clean seam: mock adapters for testing, REST adapters for remote deployment.

Each adapter function signature is stable — the implementation can change.
"""
from .device_adapter import DeviceAdapter
from .element_adapter import ElementAdapter
from .case_adapter import CaseAdapter
from .runner_adapter import RunnerAdapter

__all__ = ['DeviceAdapter', 'ElementAdapter', 'CaseAdapter', 'RunnerAdapter']
