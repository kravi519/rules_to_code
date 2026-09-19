#!/usr/bin/env python3
"""
demo.py — PRE-BUILT. The one-command demo script: happy flow, then the two
negative scenarios, mirroring section 12 of the brief. Run `make demo`.
"""
from __future__ import annotations
import sys
import webbrowser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.pipeline import run_pipeline


def _rule_line(rid, all_results, label):
    print(f"\n--- {label} ({rid}) ---")


def main():
    print("=" * 70)
    print("UC-04 DEMO — From Validated Rules to Tested Code (practice sandbox)")
    print("=" * 70)

    result = run_pipeline(case_id="demo")
    pr = result["pass_rate"]

    print("\nBEAT 1 OF 3 — Happy flow: R-001..R-003, R-005, R-007, R-009..R-012")
    print("  These rules have zero divergence in this run. Vectors were written")
    print("  before this implementation existed — the pass rate means something")
    print("  because of that ordering, not despite it.")
    clean_rules = {"R-001", "R-002", "R-003", "R-005", "R-007", "R-009", "R-010", "R-011", "R-012"}
    clean_diverged = {d["rule_id"] for d in result["divergences"]} & clean_rules
    print(f"  Divergences among the happy-path rules: {clean_diverged or 'none'}")

    print("\nBEAT 2 OF 3 — Negative scenario: R-006, rounding")
    r006 = [d for d in result["divergences"] if d["rule_id"] == "R-006"]
    r004 = [d for d in result["divergences"] if d["rule_id"] == "R-004"]
    r008 = [d for d in result["divergences"] if d["rule_id"] == "R-008"]
    for d in r006 + r004 + r008:
        diag = next((x for x in result["diagnoses"] if x.vector_id == d["vector_id"]), None)
        cause = diag.cause if diag else "?"
        print(f"  [{cause}] {d['vector_id']} ({d['rule_id']}.{d['field']}): "
              f"expected {d['expected']}, got {d['actual']}")
    print("  The test vectors were NOT changed to make these pass. The evidence")
    print("  pack reports each as a known divergence, with its diagnosis.")

    print("\nBEAT 3 OF 3 — Negative scenario: undocumented behaviour")
    if result["untraceable"]:
        for u in result["untraceable"]:
            print(f"  Untraceable behaviour on '{u['field']}' (example: {u['example_vector_id']})")
            print(f"    {u['note']}")
        print("  This was NOT quietly implemented. See the Rollback Plan section")
        print(f"  of {result['evidence_path']}.")
    else:
        print("  No untraceable behaviour surfaced by this run's vector set.")

    print("\n--- Close: pass rate & guardrails ---")
    print(f"  Pass rate: {pr['passed']}/{pr['total']} ({pr['pass_rate']*100:.1f}%)")
    breaches = [name for name, ok, _ in result["guardrails"] if not ok]
    print(f"  Guardrail breaches: {breaches or 'none'}")
    print(f"\n  Trace:    {result['trace_path']}")
    print(f"  Evidence: {result['evidence_path']}")

    if "--open" in sys.argv:
        webbrowser.open(f"file://{result['trace_path']}")
        webbrowser.open(f"file://{result['evidence_path']}")


if __name__ == "__main__":
    main()
