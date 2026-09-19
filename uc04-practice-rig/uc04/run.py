#!/usr/bin/env python3
"""run.py — practice-sandbox CLI. Mirrors the shape of the real event's CLI."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.pipeline import run_pipeline

LAST_TRACE_FILE = Path(__file__).resolve().parent / "traces" / ".last_trace"


def _print_summary(result: dict):
    pr = result["pass_rate"]
    print(f"\n=== Pass rate: {pr['passed']}/{pr['total']} ({pr['pass_rate']*100:.1f}%) ===")
    if result["divergences"]:
        print(f"\nDivergences ({len(result['divergences'])}):")
        for d, diag in zip(result["divergences"], result["diagnoses"]):
            print(f"  [{diag.cause}] {d['vector_id']} ({d['rule_id']}.{d['field']}): "
                  f"expected {d['expected']} got {d['actual']}")
    else:
        print("No divergence found.")
    if result["untraceable"]:
        print(f"\nUntraceable behaviour found on: {[u['field'] for u in result['untraceable']]}")
    if result["untested_rules"]:
        print(f"\nUntested rules: {result['untested_rules']}")
    print(f"\nGuardrails:")
    for name, ok, reason in result["guardrails"]:
        status = "PASS" if ok else f"BREACH — {reason}"
        print(f"  {name}: {status}")
    print(f"\nTrace:    {result['trace_path']}")
    print(f"Evidence: {result['evidence_path']}\n")


def cmd_run(args):
    result = run_pipeline(case_id=args.case_id)
    LAST_TRACE_FILE.write_text(result["trace_path"])
    _print_summary(result)
    breaches = [r for r in result["guardrails"] if not r[1]]
    if breaches:
        sys.exit(1)


def cmd_baseline(args):
    print("Practice-sandbox note: there is no 'empty ai/' state here (the ai/ "
          "layer is pre-filled as a worked reference with intentional gaps to "
          "diagnose). Running the full pipeline as your starting number:\n")
    cmd_run(argparse.Namespace(case_id="baseline"))


def cmd_trace(args):
    if args.last:
        if not LAST_TRACE_FILE.exists():
            print("No run yet — run `python3 run.py run` first.")
            sys.exit(1)
        print(LAST_TRACE_FILE.read_text())
    else:
        print("Usage: python3 run.py trace --last")


def cmd_case(args):
    cmd_run(argparse.Namespace(case_id=args.case_id))


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="command", required=True)

    p_run = sub.add_parser("run")
    p_run.add_argument("case_id", nargs="?", default="local")
    p_run.set_defaults(func=cmd_run)

    p_baseline = sub.add_parser("baseline")
    p_baseline.set_defaults(func=cmd_baseline)

    p_trace = sub.add_parser("trace")
    p_trace.add_argument("--last", action="store_true")
    p_trace.set_defaults(func=cmd_trace)

    p_case = sub.add_parser("case")
    p_case.add_argument("case_id")
    p_case.set_defaults(func=cmd_case)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
