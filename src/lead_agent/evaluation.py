"""Offline quality checks for a labelled lead set."""

from __future__ import annotations

from collections import Counter
from typing import Any

from .workflow import LeadQualificationWorkflow


def evaluate(cases: list[dict[str, Any]]) -> dict[str, Any]:
    workflow = LeadQualificationWorkflow()
    rows: list[dict[str, Any]] = []
    matrix: Counter[str] = Counter()

    for case in cases:
        predicted = workflow.run(case["lead"]).decision.route
        expected = case["expected_route"]
        matrix[f"{expected}->{predicted}"] += 1
        rows.append(
            {
                "id": case.get("id", "unknown"),
                "expected": expected,
                "predicted": predicted,
                "correct": predicted == expected,
            }
        )

    correct = sum(row["correct"] for row in rows)
    return {
        "accuracy": round(correct / len(rows), 3) if rows else 0.0,
        "correct": correct,
        "total": len(rows),
        "confusion_matrix": dict(sorted(matrix.items())),
        "cases": rows,
    }

