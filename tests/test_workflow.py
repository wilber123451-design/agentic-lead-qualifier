from __future__ import annotations

import unittest

from lead_agent.evaluation import evaluate
from lead_agent.workflow import LeadQualificationWorkflow


class LeadQualificationWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.workflow = LeadQualificationWorkflow()

    def test_high_signal_business_lead_is_qualified(self) -> None:
        result = self.workflow.run(
            {
                "name": "  Ana   Torres ",
                "company": "Northstar Ops",
                "email": "ANA@NORTHSTAR.EXAMPLE",
                "company_size": 65,
                "use_case": "Route and qualify inbound demo requests",
                "monthly_volume": 320,
                "budget_usd": 800,
                "urgency_days": 10,
            }
        )

        self.assertEqual("qualified", result.decision.route)
        self.assertEqual(100, result.decision.score)
        self.assertEqual("ana@northstar.example", result.decision.normalized_lead.email)
        self.assertEqual(5, len(result.trace))
        self.assertEqual(
            [
                "normalizer_agent",
                "evidence_agent",
                "scoring_agent",
                "quality_gate_agent",
                "routing_agent",
            ],
            [event.agent for event in result.trace],
        )

    def test_invalid_email_forces_human_review(self) -> None:
        result = self.workflow.run(
            {
                "name": "No Email",
                "company": "Growing Team",
                "email": "invalid",
                "company_size": 20,
                "use_case": "Automate inbound request triage",
                "monthly_volume": 100,
                "budget_usd": 500,
                "urgency_days": 14,
            }
        )

        self.assertEqual("human_review", result.decision.route)
        self.assertIn("email is missing or invalid", result.decision.warnings)
        self.assertEqual("warning", result.trace[3].status)

    def test_low_signal_personal_lead_is_nurtured(self) -> None:
        result = self.workflow.run(
            {"name": "Sam", "company": "", "email": "sam@gmail.com", "use_case": "Need help"}
        )
        self.assertEqual("nurture", result.decision.route)
        self.assertLess(result.decision.score, 45)

    def test_same_input_produces_same_decision(self) -> None:
        lead = {
            "name": "Dana",
            "company": "Acme",
            "email": "dana@acme.example",
            "company_size": 12,
            "use_case": "Qualify support-to-sales handoffs",
            "monthly_volume": 60,
            "budget_usd": 350,
            "urgency_days": 21,
        }
        first = self.workflow.run(lead).decision.to_dict()
        second = self.workflow.run(lead).decision.to_dict()
        self.assertEqual(first, second)

    def test_labelled_evaluation_reports_accuracy(self) -> None:
        cases = [
            {
                "id": "low",
                "expected_route": "nurture",
                "lead": {"name": "Sam", "email": "sam@gmail.com", "use_case": "Need help"},
            }
        ]
        report = evaluate(cases)
        self.assertEqual(1.0, report["accuracy"])
        self.assertEqual({"nurture->nurture": 1}, report["confusion_matrix"])


if __name__ == "__main__":
    unittest.main()

