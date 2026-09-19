"""
core/harness.py — PRE-BUILT. Runs everything deterministic end to end for a
given generated implementation and assembles the EvidenceFacts objects that
ai/evidence.py is allowed to draw from. Nothing in here calls a model.
"""
from __future__ import annotations
import time
from core.differential import run_differential, pass_rate
from core.traceability import build_matrix, find_untraceable_behavior, untested_rules
from core.models import EvidenceFacts


def run_harness(rules: list, vectors: list, generated_module, source_code: str) -> dict:
    t0 = time.time()
    divergences = run_differential(vectors, generated_module)
    rate = pass_rate(vectors, generated_module)
    matrix = build_matrix(rules, vectors, source_code)
    untraceable = find_untraceable_behavior(rules, vectors)
    untested = untested_rules(matrix)
    elapsed = time.time() - t0

    facts = {
        "change_summary": EvidenceFacts("change_summary", {
            "rule_count": len(rules),
            "vector_count": len(vectors),
            "pass_rate": rate,
        }),
        "test_evidence": EvidenceFacts("test_evidence", {
            "pass_rate": rate,
            "divergence_count": len(divergences),
        }),
        "impact_assessment": EvidenceFacts("impact_assessment", {
            "untested_rules": untested,
            "matrix_coverage": sum(1 for r in matrix.values() if r["covered"]) / len(matrix) if matrix else 0,
        }),
        "known_divergences": EvidenceFacts("known_divergences", {
            "divergences": divergences,
            "vector_count": rate["total"],
        }),
        "rollback_plan": EvidenceFacts("rollback_plan", {
            "untested_rules": untested,
            "untraceable_findings": untraceable,
        }),
    }
    return {
        "facts": facts,
        "divergences": divergences,
        "pass_rate": rate,
        "matrix": matrix,
        "untraceable": untraceable,
        "untested_rules": untested,
        "elapsed": elapsed,
    }
