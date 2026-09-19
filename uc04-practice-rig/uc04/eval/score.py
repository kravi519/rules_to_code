"""
eval/score.py — PRE-BUILT. Scores a run against the rubric in the brief.

Practice-sandbox note: the real event scores against a SEPARATE held-back
vector set you never see while building (released partway through). This
sandbox's ai/test_synthesis.py generates its own evaluation vectors (there's
no separate hidden set here — see README) so treat this scorer as a rehearsal
of the SHAPE of scoring, not a literal stand-in for the real held-back pass
rate.

Usage:
    python3 eval/score.py            # single run
    python3 eval/score.py --repeat 2 # run twice, report run-to-run variance
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.pipeline import run_pipeline


def score_one(result: dict) -> dict:
    pr = result["pass_rate"]
    pass_rate_score = 30 * pr["pass_rate"]

    # Divergence diagnosis honesty: reward more than one cause class found
    # (a system that calls everything "implementation defect" is penalised),
    # and reward untraceable behaviour being reported rather than missed.
    causes = {d.cause for d in result["diagnoses"]} if result["diagnoses"] else set()
    diag_score = 0.0
    if result["divergences"]:
        diag_score += 15 * (len(causes) / max(1, len({"implementation_defect",
                                                        "rounding_or_representation",
                                                        "ambiguous_rule",
                                                        "bad_test_vector"})))
    else:
        diag_score += 15  # nothing to diagnose, no penalty
    diag_score += 10 if _untraceable_correctly_handled(result) else 0
    diag_score = min(25, diag_score)

    # Rule coverage and traceability.
    matrix = result["matrix"]
    covered = sum(1 for row in matrix.values() if row["covered"]) if matrix else 0
    coverage_score = 20 * (covered / len(matrix)) if matrix else 0

    # Evidence pack quality: exists, no forbidden word, divergences stated with N.
    evidence_score = 10 if Path(result["evidence_path"]).exists() else 0

    breaches = [name for name, ok, _ in result["guardrails"] if not ok]
    penalty = 25 * len(breaches)

    return {
        "pass_rate_score": round(pass_rate_score, 1),
        "diagnosis_score": round(diag_score, 1),
        "coverage_score": round(coverage_score, 1),
        "evidence_score": round(evidence_score, 1),
        "guardrail_penalty": penalty,
        "breaches": breaches,
        "subtotal_before_stability": round(pass_rate_score + diag_score + coverage_score + evidence_score - penalty, 1),
    }


def _untraceable_correctly_handled(result) -> bool:
    if not result["untraceable"]:
        return True  # nothing to find in this run's vector set
    # correctly handled = found AND not silently "fixed" as an ordinary divergence
    found_fields = {u["field"] for u in result["untraceable"]}
    diverged_fields_diagnosed_as_defect = {
        d.rule_id for d in result["diagnoses"] if d.cause == "implementation_defect"
    }
    return bool(found_fields) and not (found_fields & diverged_fields_diagnosed_as_defect)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repeat", type=int, default=1)
    args = parser.parse_args()

    runs = []
    for i in range(args.repeat):
        result = run_pipeline(case_id=f"score{i}")
        runs.append(result)
        breakdown = score_one(result)
        print(f"\n--- Run {i+1}/{args.repeat} ---")
        for k, v in breakdown.items():
            print(f"  {k}: {v}")
        print(f"  score (pre run-to-run-stability): {breakdown['subtotal_before_stability']} / 85")

    if args.repeat > 1:
        rates = [r["pass_rate"]["pass_rate"] for r in runs]
        cause_sets = [
            {(d.vector_id, d.cause) for d in r["diagnoses"]} for r in runs
        ]
        stable = len(set(rates)) == 1 and len({frozenset(cs) for cs in cause_sets}) == 1
        print(f"\n--- Run-to-run stability ---")
        print(f"  pass rates across runs: {rates}")
        print(f"  stable: {stable}")
        print(f"  stability_score: {15 if stable else 0} / 15")


if __name__ == "__main__":
    main()
