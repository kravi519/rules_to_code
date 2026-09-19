"""
ai/evidence.py — YOURS TO BUILD.

EvidenceAI.write_section(kind, facts) -> AIResult[str]

Every sentence below is built from the `facts` object passed in — nothing is
invented, and "equivalent"/"equivalence" is never written (guardrail G3);
the closest we get is "no divergence found over N vectors", with N stated.
"""
from __future__ import annotations
from infra.ai_contract import AILayer, AIResult, Citation


class EvidenceAI(AILayer):
    def write_section(self, kind: str, facts) -> AIResult[str]:
        f = facts.facts
        text = ""

        if kind == "change_summary":
            text = (
                f"This pack covers a proposed reimplementation of INTCALC "
                f"against {f['rule_count']} SME-validated business rules, "
                f"tested against {f['vector_count']} vectors "
                f"({f['pass_rate']['passed']} of {f['pass_rate']['total']} passing)."
            )

        elif kind == "test_evidence":
            n = f["pass_rate"]["total"]
            div = f["divergence_count"]
            if div == 0:
                text = f"No divergence found over {n} vectors."
            else:
                text = (
                    f"{f['pass_rate']['passed']} of {n} vectors matched the oracle exactly; "
                    f"{div} field-level divergence(s) were found and are itemised in "
                    f"the Known Divergences section below, over this stated, finite vector set."
                )

        elif kind == "impact_assessment":
            untested = f["untested_rules"]
            coverage_pct = round(f["matrix_coverage"] * 100, 1)
            if untested:
                text = (
                    f"Traceable rule coverage is {coverage_pct}%. The following rules have "
                    f"no traceable test citing them and must be addressed before sign-off: "
                    f"{', '.join(untested)}."
                )
            else:
                text = f"Traceable rule coverage is {coverage_pct}%; every validated rule is cited by at least one test."

        elif kind == "known_divergences":
            divergences = f["divergences"]
            n = f["vector_count"]
            if not divergences:
                text = f"No divergence found over {n} vectors."
            else:
                lines = []
                for d in divergences:
                    lines.append(
                        f"Vector {d['vector_id']} (rule {d['rule_id']}, field '{d['field']}'): "
                        f"expected {d['expected']}, got {d['actual']}."
                    )
                text = f"No divergence found over {n} vectors." if not lines else " ".join(lines)

        elif kind == "rollback_plan":
            untested = f["untested_rules"]
            untraceable = f["untraceable_findings"]
            parts = []
            if untraceable:
                for u in untraceable:
                    parts.append(
                        f"Untraceable behaviour was found on field '{u['field']}' "
                        f"(example vector {u['example_vector_id']}): {u['note']}"
                    )
            if untested:
                parts.append(f"Rules with no traceable test: {', '.join(untested)}.")
            if not parts:
                parts.append("No untested rules and no untraceable behaviour were found; rollback risk is limited to the itemised divergences above.")
            text = " ".join(parts)

        else:
            text = f"Unknown section kind: {kind}"

        return AIResult(
            value=text,
            confidence=0.85,
            citations=[Citation(source="harness_output", ref=kind)],
            reasoning=f"Drafted '{kind}' strictly from the EvidenceFacts object; no external claims added.",
        )
