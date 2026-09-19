"""
infra/guardrails.py — PRE-BUILT. Enforced in code, after every relevant
step, independent of anything a prompt says. A breach here costs points
uncapped, regardless of how accurate the run otherwise is.
"""
from __future__ import annotations
import hashlib
from pathlib import Path

FORBIDDEN_EQUIVALENCE_WORDS = ["equivalent", "equivalence"]


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else ""


def check_no_equivalence_claim(text: str) -> tuple[bool, str]:
    """G3 — never claim equivalence; state 'no divergence found over N vectors'."""
    lowered = text.lower()
    for word in FORBIDDEN_EQUIVALENCE_WORDS:
        if word in lowered:
            return False, f"forbidden word '{word}' found in evidence text"
    return True, ""


def check_vectors_unmodified(vectors_path: Path, hash_before: str) -> tuple[bool, str]:
    """G2 — never change a test vector to make the implementation pass."""
    now = file_hash(vectors_path)
    if hash_before and now != hash_before:
        return False, "held-back/seed vector file changed after generation began"
    return True, ""


def check_untraceable_reported(untraceable_findings: list, evidence_text: str) -> tuple[bool, str]:
    """G4 — undocumented behaviour must be reported, not silently implemented."""
    if not untraceable_findings:
        return True, ""
    for finding in untraceable_findings:
        marker = finding["field"]
        if marker not in evidence_text:
            return False, f"untraceable behaviour on '{marker}' found but not mentioned in evidence pack"
    return True, ""


def check_coverage_uses_rule_citations(matrix: dict) -> tuple[bool, str]:
    """G5 — coverage means a test that cites the rule id, not incidental execution."""
    for rule_id, row in matrix.items():
        if row["covered"] and not row["tested_by"]:
            return False, f"{rule_id} marked covered with no citing test"
    return True, ""


def check_no_expected_from_generated_code(vectors: list, generated_available_at_synthesis: bool) -> tuple[bool, str]:
    """G1 — expected values must come only from core/cobol_runner.py, and test
    synthesis must never have had the generated implementation in scope."""
    if generated_available_at_synthesis:
        return False, "generated implementation was in scope during test synthesis"
    for v in vectors:
        if v.expected is None:
            return False, f"vector {v.id} has no oracle-derived expected value"
    return True, ""


def run_all(*, vectors, generated_available_at_synthesis, evidence_text,
            untraceable_findings, matrix, vectors_path: Path, hash_before: str):
    checks = [
        ("G1_no_expected_from_generated_code",
         check_no_expected_from_generated_code(vectors, generated_available_at_synthesis)),
        ("G2_vectors_unmodified",
         check_vectors_unmodified(vectors_path, hash_before)),
        ("G3_no_equivalence_claim",
         check_no_equivalence_claim(evidence_text)),
        ("G4_untraceable_reported",
         check_untraceable_reported(untraceable_findings, evidence_text)),
        ("G5_coverage_uses_citations",
         check_coverage_uses_rule_citations(matrix)),
    ]
    return [(name, ok, reason) for name, (ok, reason) in checks]
