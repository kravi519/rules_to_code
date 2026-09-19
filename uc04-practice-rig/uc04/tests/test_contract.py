"""tests/test_contract.py — PRE-BUILT. Do not modify."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from infra.ai_contract import AIResult, Citation


def test_airesult_defaults():
    r = AIResult()
    assert r.value is None
    assert r.confidence == 0.0
    assert r.citations == []
    assert r.abstained is False


def test_airesult_abstain_has_null_value_and_reason():
    r = AIResult(abstained=True, abstain_reason="confidence below floor")
    assert r.abstained is True
    assert r.abstain_reason


def test_citation_shape():
    c = Citation(source="validated_rules.yaml", ref="R-001")
    assert c.source and c.ref


def test_prompts_load_from_files():
    from infra.llm_client import PromptLoader
    pl = PromptLoader()
    text = pl.get("test_synthesis.md")
    assert len(text) > 10


def test_prompts_missing_file_raises():
    from infra.llm_client import PromptLoader
    pl = PromptLoader()
    try:
        pl.get("does_not_exist.md")
        assert False, "should have raised"
    except FileNotFoundError:
        pass


def test_llm_client_has_no_live_call_in_sandbox():
    from infra.llm_client import LLMClient
    try:
        LLMClient().call("x", "y", {})
        assert False, "should have raised NotImplementedError in this sandbox"
    except NotImplementedError:
        pass
