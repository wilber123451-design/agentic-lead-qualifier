"""Command-line interface for qualification and evaluation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .evaluation import evaluate
from .workflow import LeadQualificationWorkflow


def _load(path: str) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write(value: Any, output: str | None) -> None:
    rendered = json.dumps(value, indent=2, ensure_ascii=False)
    if output:
        target = Path(output)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Observable lead qualification agents")
    subparsers = parser.add_subparsers(dest="command", required=True)

    qualify = subparsers.add_parser("qualify", help="Qualify one lead or a list of leads")
    qualify.add_argument("input", help="JSON input path")
    qualify.add_argument("--output", help="Optional JSON output path")

    evaluation = subparsers.add_parser("evaluate", help="Score a labelled case set")
    evaluation.add_argument("input", help="Labelled JSON case path")
    evaluation.add_argument("--output", help="Optional JSON output path")

    args = parser.parse_args(argv)
    payload = _load(args.input)

    if args.command == "qualify":
        workflow = LeadQualificationWorkflow()
        leads = payload if isinstance(payload, list) else [payload]
        _write([workflow.run(lead).to_dict() for lead in leads], args.output)
        return 0

    _write(evaluate(payload), args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

