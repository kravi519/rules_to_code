"""
core/evidence_render.py — PRE-BUILT. Renders your five drafted sections into
out/evidence_pack.html. Refuses to render if the "equivalent" claim leaks in
(a second line of defence behind infra/guardrails.py) — the pack is an
evidence document, not a narrative about one.
"""
from __future__ import annotations
import html
from pathlib import Path

SECTION_ORDER = ["change_summary", "test_evidence", "impact_assessment",
                  "known_divergences", "rollback_plan"]
SECTION_TITLES = {
    "change_summary": "1. Change Summary",
    "test_evidence": "2. Test Evidence",
    "impact_assessment": "3. Impact Assessment",
    "known_divergences": "4. Known Divergences",
    "rollback_plan": "5. Rollback Plan",
}


def render(sections: dict, out_path: Path) -> str:
    for kind, text in sections.items():
        if "equivalent" in text.lower():
            raise ValueError(
                f"REFUSED: section '{kind}' claims equivalence. "
                f"State 'no divergence found over N vectors' and give N instead."
            )

    body = "".join(
        f"<section><h2>{SECTION_TITLES.get(k, k)}</h2><p>{html.escape(sections[k])}</p></section>"
        for k in SECTION_ORDER if k in sections
    )
    doc = f"""<!doctype html><html><head><meta charset="utf-8">
<title>Change-Approval Evidence Pack</title>
<style>
body{{font-family:Georgia,serif;max-width:760px;margin:2rem auto;line-height:1.5}}
h1{{border-bottom:2px solid #333}} h2{{color:#334}} section{{margin-bottom:1.5rem}}
</style></head><body>
<h1>Change-Approval Evidence Pack — INTCALC modernisation</h1>
{body}
</body></html>"""
    out_path.write_text(doc)
    return doc
