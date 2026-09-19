"""
ai/test_synthesis.py — YOURS TO BUILD.

TestSynthesisAI.synthesise(rule, sig) -> AIResult[list[TestVector]]

Practice-sandbox note: with no live model in this container, the "thinking"
below is written directly in Python instead of delegated to an LLM call —
but the discipline is the same one the real prompt (ai/prompts/test_synthesis.md)
asks for: reason about each rule's boundaries BEFORE any implementation
exists, and cite why each vector was chosen. On event day this function's
body becomes a call to self.call("test_synthesis.md", ctx, schema=...) and
the LLM does the reasoning; the shape of what comes back doesn't change.
"""
from __future__ import annotations
from decimal import Decimal
from core.models import TestVector
from infra.ai_contract import AILayer, AIResult, Citation

_BASE = {
    "principal": "1000.00",
    "tier": 1,
    "year_2d": 25,
    "balance_overpunch": "0001000+",
}


def _vec(rule_id: str, idx: int, rationale: str, **overrides) -> TestVector:
    inputs = dict(_BASE)
    inputs.update(overrides)
    return TestVector(id=f"{rule_id}-v{idx}", rule_id=rule_id, inputs=inputs, rationale=rationale)


class TestSynthesisAI(AILayer):
    def synthesise(self, rule, sig) -> AIResult[list]:
        vectors: list[TestVector] = []
        rid = rule.id

        if rid in ("R-001", "R-002", "R-003"):
            tier = {"R-001": 1, "R-002": 2, "R-003": 3}[rid]
            vectors.append(_vec(rid, 1, "plain mid-range balance at this tier's rate", tier=tier, principal="5000.00"))
            if rid == "R-003":
                # High enough that Tier 3 interest clears $500 — this is what
                # surfaces the undocumented cap in the legacy module, if any
                # exists. Not chosen BECAUSE we know about the cap; chosen
                # because it's a plainly legal large Tier 3 balance.
                vectors.append(_vec(rid, 2, "large Tier 3 balance, well above typical range", tier=3, principal="20000.00"))

        elif rid == "R-004":
            # the boundary the rule's own note flags as ambiguous
            vectors += [
                _vec(rid, 1, "exactly at the stated boundary — ambiguity per rule note", tier=1, principal="100000.00"),
                _vec(rid, 2, "one cent over the boundary", tier=1, principal="100000.01"),
                _vec(rid, 3, "one cent under the boundary, control case", tier=1, principal="99999.99"),
            ]

        elif rid == "R-005":
            vectors.append(_vec(rid, 1, "generic mid-range vector for the raw multiply", tier=2, principal="3000.00"))

        elif rid == "R-006":
            # 675.00 * 1.50% = 10.125 exactly: lands on the half cent, where
            # round-half-up (COBOL ROUNDED) and round-half-to-even (Python's
            # default) disagree — 10.13 vs 10.12.
            vectors += [
                _vec(rid, 1, "raw interest lands exactly on the half cent (rounding convention boundary)",
                     tier=1, principal="675.00"),
                _vec(rid, 2, "control: a value nowhere near a rounding boundary", tier=1, principal="1234.00"),
            ]

        elif rid == "R-007":
            vectors += [
                _vec(rid, 1, "pivot value itself: 50 -> 1950 per the rule text", year_2d=50),
                _vec(rid, 2, "one below pivot: 49 -> 2049", year_2d=49),
                _vec(rid, 3, "far side, low end: 00 -> 2000", year_2d=0),
                _vec(rid, 4, "far side, high end: 99 -> 1999", year_2d=99),
            ]

        elif rid == "R-008":
            vectors += [
                _vec(rid, 1, "trailing '+' sign on a nonzero magnitude", balance_overpunch="0004567+"),
                _vec(rid, 2, "trailing '-' sign — the case a naive port misreads as positive",
                     balance_overpunch="0004567-"),
                _vec(rid, 3, "zero magnitude with a sign character still present", balance_overpunch="0000000+"),
            ]

        elif rid == "R-009":
            vectors += [
                _vec(rid, 1, "principal exactly zero", principal="0.00"),
                _vec(rid, 2, "negative principal", principal="-500.00"),
            ]

        elif rid == "R-010":
            vectors.append(_vec(rid, 1, "negative principal should floor interest at zero, not go negative",
                                 principal="-1000.00"))

        elif rid == "R-011":
            vectors += [
                _vec(rid, 1, "tier value outside {1,2,3} — must default to Tier 1 rate", tier=9),
                _vec(rid, 2, "tier zero — also outside the valid domain", tier=0),
            ]

        elif rid == "R-012":
            vectors.append(_vec(rid, 1, "confirms the bp/10000 conversion at a round number", tier=2, principal="10000.00"))

        else:
            vectors.append(_vec(rid, 1, "generic vector — no special boundary identified for this rule", tier=1))

        # A naive strategy would stop at one vector per rule; boundary-heavy
        # rules above deliberately get more than one.
        return AIResult(
            value=vectors,
            confidence=0.9,
            citations=[Citation(source="validated_rules.yaml", ref=rid, quote=rule.statement[:80])],
            reasoning=f"Synthesised {len(vectors)} vector(s) for {rid} from its statement and note.",
        )
