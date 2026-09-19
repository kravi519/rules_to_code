"""
core/traceability.py — PRE-BUILT. Builds the rule -> test -> code matrix and
reports untested rules and untraceable behaviour (code paths no rule explains).

Practice-sandbox note: real static traceability tooling would parse the
generated AST for rule-id citations. This uses a simple text-scan for
`# rule: R-0xx` comments in the generated module instead — good enough to
practice the discipline of citing rule ids from generated code, which is
what ai/implementation.py is asked to do.
"""
from __future__ import annotations
import re
from core.cobol_runner import run_cobol

CITATION_RE = re.compile(r"#\s*rule:\s*(R-\d+)", re.IGNORECASE)

# Output fields a validated rule is allowed to "own". Anything the oracle
# produces that isn't claimed by any rule's `fields` list is untraceable.
KNOWN_OUTPUT_FIELDS = {"interest", "capped_interest", "balance_magnitude", "windowed_year"}


def build_matrix(rules: list, vectors: list, source_code: str) -> dict:
    cited_rule_ids = set(CITATION_RE.findall(source_code))
    matrix = {}
    for rule in rules:
        tested_by = [v.id for v in vectors if v.rule_id == rule.id]
        cited = rule.id in cited_rule_ids
        matrix[rule.id] = {
            "tested_by": tested_by,
            "tested": len(tested_by) > 0,
            "cited_in_code": cited,
            "covered": len(tested_by) > 0 and cited,
        }
    return matrix


def find_untraceable_behavior(rules: list, sample_vectors: list) -> list[dict]:
    """Looks for oracle output fields that differ from a 'no special case'
    baseline (interest) in a way no rule's `fields` list documents."""
    documented_fields = set()
    for rule in rules:
        documented_fields.update(rule.fields)

    findings = []
    seen_fields = set()
    for v in sample_vectors:
        golden = run_cobol(v.inputs)
        if golden["capped_interest"] != golden["interest"] and "capped_interest" not in documented_fields:
            if "capped_interest" not in seen_fields:
                seen_fields.add("capped_interest")
                findings.append({
                    "field": "capped_interest",
                    "example_vector_id": v.id,
                    "example_inputs": v.inputs,
                    "note": (
                        "capped_interest differs from interest for this vector, "
                        "but no validated rule's `fields` list documents "
                        "capped_interest. This is code behaviour no rule explains."
                    ),
                })
    return findings


def untested_rules(matrix: dict) -> list[str]:
    return [rule_id for rule_id, row in matrix.items() if not row["tested"]]
