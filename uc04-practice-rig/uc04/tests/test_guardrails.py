"""tests/test_guardrails.py — PRE-BUILT. Do not modify."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from infra import guardrails


def test_g3_flags_equivalent_and_equivalence():
    ok, _ = guardrails.check_no_equivalence_claim("the systems are equivalent")
    assert ok is False
    ok, _ = guardrails.check_no_equivalence_claim("we found no divergence over 200 vectors")
    assert ok is True


def test_g1_requires_oracle_derived_expected_and_synthesis_isolation():
    from core.models import TestVector
    v = TestVector(id="x", rule_id="R-001", inputs={}, expected={"interest": "1.00"})
    ok, _ = guardrails.check_no_expected_from_generated_code([v], generated_available_at_synthesis=False)
    assert ok is True
    ok, _ = guardrails.check_no_expected_from_generated_code([v], generated_available_at_synthesis=True)
    assert ok is False
    v2 = TestVector(id="y", rule_id="R-001", inputs={}, expected=None)
    ok, _ = guardrails.check_no_expected_from_generated_code([v2], generated_available_at_synthesis=False)
    assert ok is False


def test_g4_untraceable_must_be_mentioned_in_evidence():
    findings = [{"field": "capped_interest", "example_vector_id": "x", "note": "n/a"}]
    ok, _ = guardrails.check_untraceable_reported(findings, "no mention here")
    assert ok is False
    ok, _ = guardrails.check_untraceable_reported(findings, "we found untraceable behaviour on capped_interest")
    assert ok is True


def test_g5_coverage_requires_a_citing_test():
    matrix = {"R-001": {"covered": True, "tested_by": []}}
    ok, _ = guardrails.check_coverage_uses_rule_citations(matrix)
    assert ok is False
    matrix = {"R-001": {"covered": True, "tested_by": ["R-001-v1"]}}
    ok, _ = guardrails.check_coverage_uses_rule_citations(matrix)
    assert ok is True


def test_g2_detects_vector_file_mutation(tmp_path):
    p = tmp_path / "vectors.jsonl"
    p.write_text("original")
    h = guardrails.file_hash(p)
    ok, _ = guardrails.check_vectors_unmodified(p, h)
    assert ok is True
    p.write_text("tampered")
    ok, _ = guardrails.check_vectors_unmodified(p, h)
    assert ok is False


def test_test_files_are_not_the_place_to_fix_a_failing_run():
    """Guardrail on the guardrails: this test file's own hash-check tests
    exist to make sure a failing pipeline gets fixed in ai/, not by editing
    tests/. There's nothing to assert programmatically here beyond the
    presence of this note — make verify (checksums) is what actually
    enforces it."""
    assert True
