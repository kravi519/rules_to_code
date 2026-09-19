"""tests/test_implementation.py — PRE-BUILT. Do not modify."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.rules_loader import load_rules, load_io_signature
from core.cobol_runner import run_cobol
from ai.test_synthesis import TestSynthesisAI
from ai.implementation import ImplementationAI
from core.pipeline import _load_module_from_source

RULES = load_rules()
SIG = load_io_signature()


def _all_vectors():
    ai = TestSynthesisAI(None, None, None)
    vectors = []
    for r in RULES:
        vectors.extend(ai.synthesise(r, SIG).value)
    for v in vectors:
        v.expected = run_cobol(v.inputs)
    return vectors


def test_generated_module_imports_and_exposes_calculate():
    impl = ImplementationAI(None, None, None)
    source = impl.generate(RULES, SIG, _all_vectors()).value
    module = _load_module_from_source(source.content)
    assert hasattr(module, "calculate")


def test_generated_module_honours_io_signature_output_keys():
    impl = ImplementationAI(None, None, None)
    source = impl.generate(RULES, SIG, _all_vectors()).value
    module = _load_module_from_source(source.content)
    out = module.calculate({
        "principal": "1000.00", "tier": 1, "year_2d": 25,
        "balance_overpunch": "0001000+",
    })
    for key in ("interest", "capped_interest", "balance_magnitude", "windowed_year"):
        assert key in out


def test_generated_module_carries_rule_citations():
    impl = ImplementationAI(None, None, None)
    source = impl.generate(RULES, SIG, _all_vectors()).value
    import re
    cited = set(re.findall(r"#\s*rule:\s*(R-\d+)", source.content, re.I))
    all_ids = {r.id for r in RULES}
    assert cited == all_ids, f"missing citations for {all_ids - cited}"


def test_generated_module_runs_all_easy_vectors_without_crashing():
    """A 'seed' style smoke check: plain, non-pathological inputs should never
    raise, whatever the pass/fail verdict on exact value."""
    impl = ImplementationAI(None, None, None)
    source = impl.generate(RULES, SIG, _all_vectors()).value
    module = _load_module_from_source(source.content)
    easy_inputs = [
        {"principal": "5000.00", "tier": 1, "year_2d": 25, "balance_overpunch": "0005000+"},
        {"principal": "2000.00", "tier": 2, "year_2d": 30, "balance_overpunch": "0002000+"},
        {"principal": "9000.00", "tier": 3, "year_2d": 10, "balance_overpunch": "0009000+"},
    ]
    for inp in easy_inputs:
        module.calculate(inp)  # must not raise
