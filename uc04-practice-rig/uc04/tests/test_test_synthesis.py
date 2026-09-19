"""tests/test_test_synthesis.py — PRE-BUILT. Do not modify."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.rules_loader import load_rules, load_io_signature
from ai.test_synthesis import TestSynthesisAI

RULES = load_rules()
SIG = load_io_signature()


def _synth_all():
    ai = TestSynthesisAI(None, None, None)
    out = {}
    for r in RULES:
        res = ai.synthesise(r, SIG)
        out[r.id] = res
    return out


def test_every_rule_gets_at_least_one_vector():
    results = _synth_all()
    for rid, res in results.items():
        assert res.abstained or len(res.value) >= 1, f"{rid} produced no vectors"


def test_boundary_rules_get_more_than_one_vector():
    results = _synth_all()
    # R-004 (tier boundary) and R-006 (rounding) both have explicit boundary
    # notes in the rule text and must not be covered by a single happy-path vector.
    assert len(results["R-004"].value) >= 2
    assert len(results["R-006"].value) >= 2


def test_no_implementation_available_during_synthesis():
    """Synthesis must never import or reference the generated implementation."""
    import ai.test_synthesis as mod
    source = Path(mod.__file__).read_text()
    assert "ai.implementation" not in source
    assert "from ai.implementation" not in source


def test_expected_values_not_fabricated_by_synthesis():
    results = _synth_all()
    for res in results.values():
        for v in res.value:
            assert v.expected is None, "expected must be filled by the oracle, not by synthesis"


def test_synthesis_cites_the_rule():
    results = _synth_all()
    for rid, res in results.items():
        assert any(c.ref == rid for c in res.citations)
