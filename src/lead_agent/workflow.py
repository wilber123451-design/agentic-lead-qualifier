"""Small agents with explicit hand-offs, quality gates, and audit traces."""

from __future__ import annotations

import re
from dataclasses import replace
from time import perf_counter
from typing import Any, Callable, TypeVar

from .models import Decision, Evidence, Lead, TraceEvent, WorkflowResult

T = TypeVar("T")

FREE_EMAIL_DOMAINS = {
    "gmail.com",
    "hotmail.com",
    "outlook.com",
    "proton.me",
    "yahoo.com",
}
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class LeadQualificationWorkflow:
    """Coordinate five focused agents without an external API or secret key.

    Each agent owns one decision boundary. The orchestrator records the input
    evidence, duration, and outcome of every hand-off, making the workflow easy
    to inspect and evaluate before replacing any deterministic step with an LLM.
    """

    def run(self, raw_lead: dict[str, Any] | Lead) -> WorkflowResult:
        trace: list[TraceEvent] = []
        lead = raw_lead if isinstance(raw_lead, Lead) else Lead.from_dict(raw_lead)

        normalized = self._observe(
            trace,
            "normalizer_agent",
            lambda: self._normalize(lead),
            lambda value: f"Normalized {value.email or 'missing email'}",
        )
        evidence = self._observe(
            trace,
            "evidence_agent",
            lambda: self._collect_evidence(normalized),
            lambda value: f"Evidence coverage {value.coverage:.0%}",
            details=lambda value: {"coverage": value.coverage},
        )
        breakdown = self._observe(
            trace,
            "scoring_agent",
            lambda: self._score(normalized, evidence),
            lambda value: f"Calculated score {sum(value.values())}/100",
            details=lambda value: {"breakdown": value},
        )
        warnings = self._observe(
            trace,
            "quality_gate_agent",
            lambda: self._quality_gate(normalized, evidence, breakdown),
            lambda value: "Quality gate passed" if not value else "; ".join(value),
            status=lambda value: "warning" if value else "ok",
            details=lambda value: {"warnings": list(value)},
        )
        decision = self._observe(
            trace,
            "routing_agent",
            lambda: self._route(normalized, evidence, breakdown, warnings),
            lambda value: f"Routed to {value.route}",
            details=lambda value: {
                "route": value.route,
                "score": value.score,
                "confidence": value.confidence,
            },
        )
        return WorkflowResult(decision=decision, trace=tuple(trace))

    @staticmethod
    def _observe(
        trace: list[TraceEvent],
        agent: str,
        action: Callable[[], T],
        summary: Callable[[T], str],
        *,
        status: Callable[[T], str] | None = None,
        details: Callable[[T], dict[str, Any]] | None = None,
    ) -> T:
        started = perf_counter()
        value = action()
        trace.append(
            TraceEvent(
                agent=agent,
                status=(status(value) if status else "ok"),  # type: ignore[arg-type]
                duration_ms=round((perf_counter() - started) * 1000, 3),
                summary=summary(value),
                details=details(value) if details else {},
            )
        )
        return value

    @staticmethod
    def _normalize(lead: Lead) -> Lead:
        def clean(value: str) -> str:
            return " ".join(value.strip().split())

        return replace(
            lead,
            name=clean(lead.name),
            company=clean(lead.company),
            email=lead.email.strip().lower(),
            source=clean(lead.source).lower() or "unknown",
            use_case=clean(lead.use_case),
            notes=clean(lead.notes),
            company_size=max(0, lead.company_size),
            monthly_volume=max(0, lead.monthly_volume),
            budget_usd=max(0, lead.budget_usd),
            urgency_days=max(0, lead.urgency_days),
        )

    @staticmethod
    def _collect_evidence(lead: Lead) -> Evidence:
        domain = lead.email.rsplit("@", 1)[-1] if "@" in lead.email else ""
        return Evidence(
            business_email=bool(EMAIL_PATTERN.match(lead.email))
            and domain not in FREE_EMAIL_DOMAINS,
            company_identified=bool(lead.company),
            use_case_present=len(lead.use_case) >= 12,
            budget_present=lead.budget_usd > 0,
            volume_present=lead.monthly_volume > 0,
            urgency_present=lead.urgency_days > 0,
        )

    @staticmethod
    def _score(lead: Lead, evidence: Evidence) -> dict[str, int]:
        company_fit = 20 if lead.company_size >= 50 else 15 if lead.company_size >= 10 else 5
        budget_fit = 25 if lead.budget_usd >= 500 else 15 if lead.budget_usd >= 300 else 5 if lead.budget_usd else 0
        volume_fit = 15 if lead.monthly_volume >= 200 else 10 if lead.monthly_volume >= 50 else 5 if lead.monthly_volume else 0
        urgency_fit = 15 if 0 < lead.urgency_days <= 14 else 8 if lead.urgency_days <= 30 and lead.urgency_days else 0
        return {
            "business_email": 15 if evidence.business_email else 0,
            "company_fit": company_fit if evidence.company_identified else 0,
            "use_case": 10 if evidence.use_case_present else 0,
            "budget_fit": budget_fit,
            "volume_fit": volume_fit,
            "urgency_fit": urgency_fit,
        }

    @staticmethod
    def _quality_gate(
        lead: Lead, evidence: Evidence, breakdown: dict[str, int]
    ) -> tuple[str, ...]:
        warnings: list[str] = []
        if not EMAIL_PATTERN.match(lead.email):
            warnings.append("email is missing or invalid")
        if not evidence.use_case_present:
            warnings.append("use case needs clarification")
        if not evidence.budget_present:
            warnings.append("budget is unconfirmed")
        if sum(breakdown.values()) > 100:
            warnings.append("score exceeds configured maximum")
        return tuple(warnings)

    @staticmethod
    def _route(
        lead: Lead,
        evidence: Evidence,
        breakdown: dict[str, int],
        warnings: tuple[str, ...],
    ) -> Decision:
        score = sum(breakdown.values())
        confidence = evidence.coverage
        blocking_warning = any("email" in warning for warning in warnings)
        if score >= 70 and confidence >= 0.67 and not blocking_warning:
            route = "qualified"
        elif score >= 45 or blocking_warning:
            route = "human_review"
        else:
            route = "nurture"

        reasons = tuple(
            key.replace("_", " ")
            for key, value in breakdown.items()
            if value >= 10
        )
        return Decision(
            route=route,  # type: ignore[arg-type]
            score=score,
            confidence=confidence,
            reasons=reasons,
            warnings=warnings,
            normalized_lead=lead,
            evidence=evidence,
            score_breakdown=breakdown,
        )

