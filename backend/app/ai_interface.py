"""Optional AI provider interface (DISABLED by default).

OpsRadar performs root-cause analysis using the deterministic rule engine in
detectors.py. This module defines the interface that could be wired to an
external LLM provider in the future. It is intentionally NOT connected to any
API key or network call in the default build.
"""

from typing import List, Optional, Protocol, runtime_checkable


@runtime_checkable
class AIRootCauseProvider(Protocol):
    def suggest_root_cause(
        self,
        incident_title: str,
        evidence: List[str],
        context: dict,
    ) -> Optional[str]:
        """Return a speculative root-cause string or None if unavailable."""
        ...


class DisabledAIProvider:
    """Placeholder provider that always declines. Safety default."""

    def suggest_root_cause(
        self,
        incident_title: str,
        evidence: List[str],
        context: dict,
    ) -> Optional[str]:
        return None


# Instantiate the disabled provider. To enable an AI provider in the future,
# replace this with a real implementation that calls an LLM API and clearly
# labels output as speculative.
AI_PROVIDER: AIRootCauseProvider = DisabledAIProvider()
