"""tests/test_evidence.py — PRE-BUILT. Do not modify."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.rules_loader import load_rules, load_io_signature
from core.cobol_runner import run_cobol
from core.harness import run_harness
from core.evidence_render import render, SECTION_ORDER
from ai.test_synthesis import TestSynthesisAI
from ai.implementation import ImplementationAI
from ai.evidence import EvidenceAI
from core.pipeline import _load_module_from_source

RULES = load_rules()
SIG = load_io_signature()


def _facts_bundle():
    synth = TestSynthesisAI(None, None, None)
    vectors = []
    for r in RULES:
        vectors.extend(synth.synthesise(r, SIG).value)
    for v in vectors:
        v.expected = run_cobol(v.inputs)
    impl = ImplementationAI(None, None, None)
    source = impl.generate(RULES, SIG, vectors).value
    module = _load_module_from_source(source.content)
    return run_harness(RULES, vectors, module, source.content)


def test_all_five_sections_generated():
    bundle = _facts_bundle()
    ev = EvidenceAI(None, None, None)
    sections = {k: ev.write_section(k, f).value for k, f in bundle["facts"].items()}
    assert set(sections.keys()) == set(SECTION_ORDER)


def test_word_equivalent_appears_nowhere():
    bundle = _facts_bundle()
    ev = EvidenceAI(None, None, None)
    for kind, facts in bundle["facts"].items():
        text = ev.write_section(kind, facts).value
        assert "equivalent" not in text.lower()


def test_known_divergences_states_n():
    bundle = _facts_bundle()
    ev = EvidenceAI(None, None, None)
    text = ev.write_section("known_divergences", bundle["facts"]["known_divergences"]).value
    n = bundle["pass_rate"]["total"]
    assert str(n) in text or all(str(d["vector_id"]) in text for d in bundle["divergences"])


def test_evidence_pack_renders(tmp_path):
    bundle = _facts_bundle()
    ev = EvidenceAI(None, None, None)
    sections = {k: ev.write_section(k, f).value for k, f in bundle["facts"].items()}
    out = tmp_path / "evidence_pack.html"
    doc = render(sections, out)
    assert out.exists()
    assert "Change-Approval Evidence Pack" in doc


def test_renderer_refuses_equivalence_claim(tmp_path):
    out = tmp_path / "evidence_pack.html"
    try:
        render({"change_summary": "the two systems are fully equivalent"}, out)
        assert False, "renderer should have refused"
    except ValueError:
        pass
