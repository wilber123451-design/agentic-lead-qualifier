# Agentic Lead Qualifier

A small, key-free Python workflow that turns raw inbound leads into an auditable routing decision. It is designed to show how an agentic system can be useful before adding an LLM: focused agents, explicit hand-offs, observable traces, an offline quality gate, and reproducible evaluation.

## Why this exists

Lead qualification often starts as one large prompt. That is hard to debug: a wrong route could come from dirty input, weak evidence, inconsistent scoring, or a hallucinated conclusion. This project separates those responsibilities into five agents:

1. `normalizer_agent` cleans and bounds incoming fields.
2. `evidence_agent` distinguishes known signals from missing information.
3. `scoring_agent` produces a transparent score breakdown.
4. `quality_gate_agent` blocks unsafe automation and asks for clarification.
5. `routing_agent` chooses `qualified`, `human_review`, or `nurture`.

Every run returns a trace with agent name, status, duration, summary, and decision details. No external service, API key, or real customer data is required.

## Run it

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -e .
lead-agent qualify examples/leads.json --output out/decisions.json
lead-agent evaluate examples/eval_cases.json --output out/evaluation.json
```

Or without installing the command:

```bash
PYTHONPATH=src python -m lead_agent.cli qualify examples/leads.json
PYTHONPATH=src python -m lead_agent.cli evaluate examples/eval_cases.json
```

Run the standard-library test suite:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

## Observability and quality

The workflow does not treat a score as truth. It also measures evidence coverage and enforces a quality gate. A lead with a strong commercial score but an invalid email is routed to human review, not automatically accepted. The labelled evaluation set reports accuracy and a small confusion matrix, making routing changes measurable.

Example trace:

```json
{
  "agent": "quality_gate_agent",
  "status": "warning",
  "summary": "email is missing or invalid",
  "details": {"warnings": ["email is missing or invalid"]}
}
```

## Deliberate trade-offs

- Deterministic rules make the first version explainable and cheap to test.
- The agent boundaries are ready for selective LLM replacement later—for example, extracting a use case from free-form notes—without letting a model control every decision.
- Confidence means evidence coverage, not model probability. The name is intentionally honest.
- The sample `.example` domains and fictional leads prevent accidental outreach or exposure of customer data.

## Next experiments

- Add a redacted LLM extraction adapter behind the evidence agent.
- Compare its routes with the deterministic baseline rather than replacing the baseline blindly.
- Add drift monitoring for score distributions and human-review outcomes.
- Learn thresholds from accepted and rejected leads after enough labelled data exists.

Built by [Wilber Ramos](https://github.com/wilber123451-design). Related workflow: [n8n lead qualifier](https://github.com/wilber123451-design/flowsprint-lead-qualifier).

