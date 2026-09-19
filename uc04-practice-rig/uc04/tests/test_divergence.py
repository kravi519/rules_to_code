"""tests/test_divergence.py — PRE-BUILT. Do not modify."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.rules_loader import load_rules, load_io_signature
from core.cobol_runner import run_cobol
from core.harness import run_harness
from ai.test_synthesis import TestSynthesisAI
from ai.implementation import ImplementationAI
from ai.divergence import DivergenceAI
from core.pipeline import _load_module_from_source

RULES = load_rules()
SIG = load_io_signature()
RULES_BY_ID = {r.id: r for r in RULES}


def _run():
    synth = TestSynthesisAI(None, None, None)
    vectors = []
    for r in RULES:
        vectors.extend(synth.synthesise(r, SIG).value)
    for v in vectors:
        v.expected = run_cobol(v.inputs)
    impl = ImplementationAI(None, None, None)
    source = impl.generate(RULES, SIG, vectors).value
    module = _load_module_from_source(source.content)
    bundle = run_harness(RULES, vectors, module, source.content)
    vectors_by_id = {v.id: v for v in vectors}
    return bundle, vectors_by_id


def test_three_seeded_divergences_found():
    bundle, _ = _run()
    rule_ids_diverged = {d["rule_id"] for d in bundle["divergences"]}
    assert {"R-004", "R-006", "R-008"} <= rule_ids_diverged


def test_diagnosis_does_not_attribute_everything_to_implementation_defect():
    bundle, vectors_by_id = _run()
    diag_ai = DivergenceAI(None, None, None)
    causes = set()
    for d in bundle["divergences"]:
        rule = RULES_BY_ID[d["rule_id"]]
        vector = vectors_by_id[d["vector_id"]]
        result = diag_ai.diagnose(rule, vector, d["expected"], d["actual"])
        causes.add(result.value.cause)
    assert len(causes) >= 2, (
        "a diagnosis system that calls every divergence an implementation "
        "defect has not done the diagnostic work"
    )
    assert "ambiguous_rule" in causes
    assert "rounding_or_representation" in causes


def test_ambiguous_rule_diagnosis_names_the_ambiguity():
    bundle, vectors_by_id = _run()
    diag_ai = DivergenceAI(None, None, None)
    r004 = next(d for d in bundle["divergences"] if d["rule_id"] == "R-004")
    result = diag_ai.diagnose(RULES_BY_ID["R-004"], vectors_by_id[r004["vector_id"]],
                               r004["expected"], r004["actual"])
    assert result.value.cause == "ambiguous_rule"
    assert result.value.suggested_fix
