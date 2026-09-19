"""
core/differential.py — PRE-BUILT. Runs the oracle and the generated
implementation over a vector set and reports every divergence with the exact
input that triggered it. Pure Python, no model calls.
"""
from __future__ import annotations
from decimal import Decimal, InvalidOperation
from core.cobol_runner import run_cobol


def _values_differ(expected, actual) -> bool:
    """Numeric-aware comparison: '75.00' and '75.0' are the same value.
    Falls back to string comparison for non-numeric fields (e.g. windowed_year)."""
    try:
        return Decimal(str(expected)) != Decimal(str(actual))
    except (InvalidOperation, ValueError, TypeError):
        return str(expected) != str(actual)


# capped_interest is deliberately excluded from bug-hunting divergence: it is
# the practice sandbox's untraceable-behaviour pathology (see
# core/traceability.find_untraceable_behavior). Diffing it here would flag it
# as a "bug" on every tier-3 vector over the cap, which is the wrong frame —
# the correct response to undocumented behaviour is to report it, not chase it
# as a defect (guardrail G4).
IGNORED_FOR_BUG_HUNTING = {"capped_interest"}


def run_differential(vectors: list, generated_module) -> list[dict]:
    """Returns one entry per FIELD-level divergence: {vector, field, expected, actual}."""
    divergences = []
    for v in vectors:
        expected = v.expected or run_cobol(v.inputs)
        try:
            actual = generated_module.calculate(v.inputs)
        except Exception as exc:  # noqa: BLE001 - surfaced as a divergence, not a crash
            actual = {"__error__": repr(exc)}
        for field_name, exp_val in expected.items():
            if field_name in IGNORED_FOR_BUG_HUNTING:
                continue
            act_val = actual.get(field_name, "__missing__")
            if _values_differ(exp_val, act_val):
                divergences.append({
                    "vector_id": v.id,
                    "rule_id": v.rule_id,
                    "field": field_name,
                    "inputs": v.inputs,
                    "expected": exp_val,
                    "actual": act_val,
                })
    return divergences


def pass_rate(vectors: list, generated_module) -> dict:
    total = len(vectors)
    divergent_vector_ids = {d["vector_id"] for d in run_differential(vectors, generated_module)}
    failed = len(divergent_vector_ids)
    passed = total - failed
    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "pass_rate": round(passed / total, 4) if total else 0.0,
    }
