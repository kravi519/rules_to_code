"""
core/cobol_runner.py — PRE-BUILT. The oracle. This is what a generated
implementation is judged against; nothing you write should ever influence it.

PRACTICE-SANDBOX STAND-IN: this container has no GnuCOBOL and no network, so
this file is a pure-Python transliteration of data/src/legacy/INTCALC.cbl,
line for line, including its rounding convention and its one undocumented
branch (PARA-CAP-CHECK). On a machine with GnuCOBOL installed, replace the
body of run_cobol() with a subprocess call to a compiled INTCALC and keep the
same function signature — nothing else in core/ needs to change.
"""
from __future__ import annotations
from decimal import Decimal, ROUND_HALF_UP

TWO_PLACES = Decimal("0.01")


def _tier_rate_bp(tier: int, principal: Decimal) -> int:
    if tier == 1:
        rate_bp = 150
    elif tier == 2:
        rate_bp = 275
    elif tier == 3:
        rate_bp = 400
    else:
        rate_bp = 150  # R-011: unknown tier treated as Tier 1

    # R-004: boundary is strictly GREATER-THAN 100000.00, not >=.
    if tier == 1 and principal > Decimal("100000.00"):
        rate_bp = 275
    return rate_bp


def _parse_overpunch(raw: str) -> Decimal:
    """R-008: trailing separate sign — last char is '+'/'-', not a digit."""
    sign = raw[-1]
    digits = raw[:-1]
    value = Decimal(digits)
    return -value if sign == "-" else value


def _window_year(yy: int) -> int:
    """R-007: pivot at 50. 00-49 -> 20xx, 50-99 -> 19xx."""
    return 2000 + yy if yy < 50 else 1900 + yy


def run_cobol(inputs: dict) -> dict:
    """The golden output for one input vector. Mirrors INTCALC.cbl exactly,
    including PARA-CAP-CHECK, which no validated rule documents."""
    principal = Decimal(str(inputs["principal"]))
    tier = int(inputs["tier"])

    if principal <= 0:
        interest = Decimal("0.00")               # R-009
    else:
        rate_bp = _tier_rate_bp(tier, principal)
        rate_dec = Decimal(rate_bp) / Decimal(10000)
        raw_interest = principal * rate_dec * 100  # rate_dec already /100 baked via bp/10000*100... see note
        # NOTE: matches R-005/R-012 exactly: rate_bp/10000 gives the decimal
        # ANNUAL rate as a fraction of 1 (e.g. 150bp -> 0.0150), so:
        raw_interest = principal * rate_dec
        interest = raw_interest.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)  # R-006

    if interest < 0:
        interest = Decimal("0.00")  # R-010

    # PARA-CAP-CHECK — UNDOCUMENTED. No rule in validated_rules.yaml describes
    # this. It exists so the traceability checker has something real to find.
    capped_interest = interest
    if tier == 3 and interest > Decimal("500.00"):
        capped_interest = Decimal("500.00")

    balance_magnitude = _parse_overpunch(inputs["balance_overpunch"])
    windowed_year = _window_year(int(inputs["year_2d"]))

    return {
        "interest": str(interest),
        "capped_interest": str(capped_interest),
        "balance_magnitude": str(balance_magnitude),
        "windowed_year": windowed_year,
    }
