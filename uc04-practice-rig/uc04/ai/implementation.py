"""
ai/implementation.py — YOURS TO BUILD.

ImplementationAI.generate(rules, sig, tests) -> AIResult[SourceFile]

Practice-sandbox note: written directly rather than via a live model (see
ai/test_synthesis.py's note). The generated module below is a deliberately
IMPERFECT reading of the rules — that's the point of the practice rig:
- R-004's boundary is read as `>=` here (a defensible reading of "over"),
  which will disagree with the oracle's `>` at exactly 100000.00.
- R-006 rounds with Python's built-in `round()` (banker's rounding), which
  disagrees with COBOL's ROUNDED clause at the half cent.
- R-008's sign parsing has a real bug: it checks for a LEADING sign
  character, but the field's sign is TRAILING (per the rule). This
  silently misreads negative balances as positive.
- capped_interest is intentionally left unimplemented (== interest) because
  no rule authorises a cap — this is correct per guardrail G4, and the
  resulting field-level gap is exactly what core/traceability.py's
  untraceable-behaviour check exists to catch.

This gives you three real divergences to practice diagnosing with
ai/divergence.py, of three different causes, plus one deliberately "clean"
rule (R-007) so the demo isn't uniformly bad news.
"""
from __future__ import annotations
from core.models import SourceFile
from infra.ai_contract import AILayer, AIResult, Citation

_SOURCE = '''
"""Generated reimplementation of INTCALC — practice sandbox, imperfect on purpose."""
from decimal import Decimal


def _tier_rate_bp(tier, principal):
    # rule: R-001
    if tier == 1:
        rate_bp = 150
    # rule: R-002
    elif tier == 2:
        rate_bp = 275
    # rule: R-003
    elif tier == 3:
        rate_bp = 400
    else:
        # rule: R-011 — unknown tier defaults to Tier 1
        rate_bp = 150

    # rule: R-004 — read as >= 100000.00 ("over" taken inclusively)
    if tier == 1 and principal >= Decimal("100000.00"):
        rate_bp = 275
    return rate_bp


def _parse_balance(raw):
    # rule: R-008 — BUG: checks for a LEADING sign, but the field's sign is
    # trailing per the rule text. Negative balances get silently misread.
    if raw[0] in "+-":
        sign, digits = raw[0], raw[1:]
    else:
        sign, digits = "+", raw
    value = Decimal(digits.rstrip("+-") if digits[-1] in "+-" else digits)
    return -value if sign == "-" else value


def _window_year(yy):
    # rule: R-007
    return 2000 + yy if yy < 50 else 1900 + yy


def calculate(inputs):
    principal = Decimal(str(inputs["principal"]))
    tier = int(inputs["tier"])

    # rule: R-009
    if principal <= 0:
        interest = Decimal("0.00")
    else:
        rate_bp = _tier_rate_bp(tier, principal)
        # rule: R-012 — rate expressed in whole basis points, converted to a decimal fraction
        rate_dec = Decimal(rate_bp) / Decimal(10000)
        # rule: R-005 / R-012
        raw_interest = principal * rate_dec
        # rule: R-006 — Python's default rounding is round-half-to-even,
        # not round-half-away-from-zero.
        interest = Decimal(str(round(float(raw_interest), 2)))

    # rule: R-010
    if interest < 0:
        interest = Decimal("0.00")

    # No validated rule authorises a cap, so none is implemented here.
    capped_interest = interest

    balance_magnitude = _parse_balance(inputs["balance_overpunch"])
    windowed_year = _window_year(int(inputs["year_2d"]))

    return {
        "interest": str(interest),
        "capped_interest": str(capped_interest),
        "balance_magnitude": str(balance_magnitude),
        "windowed_year": windowed_year,
    }
'''


class ImplementationAI(AILayer):
    def generate(self, rules, sig, tests) -> AIResult[SourceFile]:
        source = SourceFile(path="generated/implementation_module.py", content=_SOURCE)
        cited = sorted({r.id for r in rules})
        return AIResult(
            value=source,
            confidence=0.8,
            citations=[Citation(source="validated_rules.yaml", ref=rid) for rid in cited],
            reasoning=(
                "Implemented all 12 rules directly from their statements. "
                "R-004's boundary and R-006's rounding convention were "
                "under-specified in the rule text; took the literal reading "
                "in each case rather than guessing at COBOL semantics. "
                "capped_interest left unimplemented — no rule authorises it."
            ),
        )
