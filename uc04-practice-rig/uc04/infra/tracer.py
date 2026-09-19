"""
infra/tracer.py — PRE-BUILT. Writes a self-contained HTML trace, flushed
after every step, so it can be opened mid-run. Simplified for the practice
sandbox (no live refresh loop) but the sections match the real brief:
run header, step timeline, AI call detail, guardrail verdicts, abstentions,
run summary.
"""
from __future__ import annotations
import html
import json
import time
from pathlib import Path


class Tracer:
    def __init__(self, out_path: Path, case_id: str, config: dict):
        self.out_path = out_path
        self.case_id = case_id
        self.config = config
        self.steps: list[dict] = []
        self.ai_calls: list[dict] = []
        self.guardrail_verdicts: list[dict] = []
        self.abstentions: list[dict] = []
        self.start = time.time()

    def record_step(self, name: str, kind: str, elapsed: float, note: str = ""):
        self.steps.append({"name": name, "kind": kind, "elapsed": round(elapsed, 4), "note": note})
        self._flush()

    def record_ai_call(self, prompt_name: str, ctx: dict, result):
        self.ai_calls.append({
            "prompt": prompt_name,
            "ctx_keys": list(ctx.keys()),
            "confidence": getattr(result, "confidence", None),
            "abstained": getattr(result, "abstained", False),
        })
        if getattr(result, "abstained", False):
            self.abstentions.append({
                "prompt": prompt_name,
                "reason": getattr(result, "abstain_reason", ""),
            })
        self._flush()

    def record_guardrail(self, name: str, passed: bool, reason: str = ""):
        self.guardrail_verdicts.append({"name": name, "passed": passed, "reason": reason})
        self._flush()

    def _flush(self):
        elapsed_total = time.time() - self.start
        rows_steps = "".join(
            f"<tr><td>{html.escape(s['name'])}</td><td>{s['kind']}</td>"
            f"<td>{s['elapsed']}s</td><td>{html.escape(s['note'])}</td></tr>"
            for s in self.steps
        )
        rows_ai = "".join(
            f"<tr><td>{html.escape(a['prompt'])}</td><td>{a['confidence']}</td>"
            f"<td>{a['abstained']}</td></tr>"
            for a in self.ai_calls
        )
        rows_guard = "".join(
            f"<tr><td>{html.escape(g['name'])}</td>"
            f"<td>{'PASS' if g['passed'] else 'BREACH'}</td>"
            f"<td>{html.escape(g['reason'])}</td></tr>"
            for g in self.guardrail_verdicts
        )
        rows_abstain = "".join(
            f"<tr><td>{html.escape(a['prompt'])}</td><td>{html.escape(a['reason'])}</td></tr>"
            for a in self.abstentions
        )
        doc = f"""<!doctype html><html><head><meta charset="utf-8">
<title>trace {html.escape(self.case_id)}</title>
<style>
body{{font-family:monospace;background:#0b0b0f;color:#ddd;padding:2rem}}
h2{{color:#9ad}} table{{width:100%;border-collapse:collapse;margin-bottom:2rem}}
td,th{{border:1px solid #333;padding:4px 8px;text-align:left;font-size:0.85rem}}
.breach{{color:#f66}}
</style></head><body>
<h1>Run trace — {html.escape(self.case_id)}</h1>
<p>model: {html.escape(str(self.config.get('model', {})))} | elapsed: {round(elapsed_total,2)}s</p>
<h2>Step timeline</h2><table><tr><th>step</th><th>kind</th><th>elapsed</th><th>note</th></tr>{rows_steps}</table>
<h2>AI call detail</h2><table><tr><th>prompt</th><th>confidence</th><th>abstained</th></tr>{rows_ai}</table>
<h2>Guardrail verdicts</h2><table><tr><th>guardrail</th><th>verdict</th><th>reason</th></tr>{rows_guard}</table>
<h2>Abstentions</h2><table><tr><th>prompt</th><th>reason</th></tr>{rows_abstain}</table>
</body></html>"""
        self.out_path.write_text(doc)
