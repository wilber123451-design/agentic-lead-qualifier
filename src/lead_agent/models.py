"""Typed data exchanged by the workflow agents."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

Route = Literal["qualified", "human_review", "nurture"]


@dataclass(frozen=True)
class Lead:
    name: str = ""
    company: str = ""
    email: str = ""
    source: str = "unknown"
    company_size: int = 0
    use_case: str = ""
    monthly_volume: int = 0
    budget_usd: int = 0
    urgency_days: int = 0
    notes: str = ""

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "Lead":
        allowed = {field.name for field in cls.__dataclass_fields__.values()}
        return cls(**{key: value[key] for key in allowed if key in value})


@dataclass(frozen=True)
class Evidence:
    business_email: bool
    company_identified: bool
    use_case_present: bool
    budget_present: bool
    volume_present: bool
    urgency_present: bool

    @property
    def coverage(self) -> float:
        values = asdict(self).values()
        return round(sum(bool(value) for value in values) / len(asdict(self)), 2)


@dataclass(frozen=True)
class Decision:
    route: Route
    score: int
    confidence: float
    reasons: tuple[str, ...]
    warnings: tuple[str, ...]
    normalized_lead: Lead
    evidence: Evidence
    score_breakdown: dict[str, int]

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["reasons"] = list(self.reasons)
        value["warnings"] = list(self.warnings)
        return value


@dataclass(frozen=True)
class TraceEvent:
    agent: str
    status: Literal["ok", "warning"]
    duration_ms: float
    summary: str
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class WorkflowResult:
    decision: Decision
    trace: tuple[TraceEvent, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision.to_dict(),
            "trace": [event.to_dict() for event in self.trace],
        }
