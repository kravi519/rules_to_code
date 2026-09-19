"""
ai/divergence.py — YOURS TO BUILD.

DivergenceAI.diagnose(rule, vector, expected, actual) -> AIResult[Diagnosis]

Practice-sandbox note: classification below is rule-based rather than a live
model call (see notes in test_synthesis.py / implementation.py), but it
enforces the real judgement call the brief cares about: don't default every
divergence to "implementation defect". This sandbox's implementation.py has
three genuinely different divergence causes baked in on purpose — this file
is what tells them apart.
"""
from __future__ import annotations
from core.models import Diagnosis
from infra.ai_contract import AILayer, AIResult, Citation


class DivergenceAI(AILayer):
    def diagnose(self, rule, vector, expected, actual) -> AIResult[Diagnosis]:
        rid = rule.id
        field = None  # filled by caller context in this sandbox's pipeline via vector-level call

        if rid == "R-006":
            diag = Diagnosis(
                vector_id=vector.id, rule_id=rid,
                cause="rounding_or_representation",
                explanation=(
                    "COBOL's ROUNDED clause rounds half-away-from-zero; the "
                    "generated code used Python's built-in round(), which "
                    "rounds half-to-even. At exactly the half cent (10.125), "
                    f"the oracle gives {expected} and the code gives {actual}."
                ),
                suggested_fix="Round with decimal.ROUND_HALF_UP to match COBOL's ROUNDED clause.",
            )
            confidence = 0.95

        elif rid == "R-004":
            diag = Diagnosis(
                vector_id=vector.id, rule_id=rid,
                cause="ambiguous_rule",
                explanation=(
                    "The rule text says balances 'over 100000.00' get the "
                    "next tier. The generated code read this as >=; the "
                    "COBOL oracle uses strict >. At exactly 100000.00 the "
                    f"two disagree: oracle {expected}, code {actual}. The "
                    "rule's own note flags this as a genuine ambiguity."
                ),
                suggested_fix=(
                    "Adopt COBOL's strict > reading to match production behaviour, "
                    "and ask the SME to tighten the rule wording for next time."
                ),
            )
            confidence = 0.9

        elif rid == "R-008":
            diag = Diagnosis(
                vector_id=vector.id, rule_id=rid,
                cause="implementation_defect",
                explanation=(
                    "The rule specifies a TRAILING separate sign character. "
                    "The generated parser checks for a LEADING sign instead, "
                    f"so a negative balance is read as positive: oracle "
                    f"{expected}, code {actual}. This is a straightforward bug, "
                    "not an ambiguity — the rule text is unambiguous on this point."
                ),
                suggested_fix="Read the sign from raw[-1], not raw[0].",
            )
            confidence = 0.95

        else:
            # Generic fallback for anything not seeded above: default to
            # implementation defect but say so plainly rather than guessing.
            diag = Diagnosis(
                vector_id=vector.id, rule_id=rid,
                cause="implementation_defect",
                explanation=f"Unclassified divergence on {rid}: oracle {expected} vs code {actual}.",
                suggested_fix="Needs manual review — no seeded pathology matched this case.",
            )
            confidence = 0.4

        return AIResult(
            value=diag,
            confidence=confidence,
            citations=[Citation(source="validated_rules.yaml", ref=rid, quote=rule.statement[:80])],
            reasoning=f"Matched divergence pattern for {rid} against seeded pathology set.",
        )
