# UC-04 Rules-to-Code Practice Lab — From Validated Rules to Tested Code

This is a **practice sandbox** for the UC-04 hackathon statement, built so you can
rehearse the pipeline end-to-end before the real event. It is NOT the real
hackathon data (you'll get the actual `INTCALC.cbl`, the real 24 rules, and the
real held-back vectors on the day) — it's a same-shape stand-in so you can:

1. Get comfortable with the pipeline order (synthesise → oracle → generate →
   diff → diagnose → trace → score → evidence pack) before the clock starts.
2. Practice writing the four `ai/*.py` methods and their prompts.
3. Rehearse `make demo` so it's muscle memory on the day.

## What's different from the real event (and why)

- **No GnuCOBOL / no network here.** The container this was built in has
  neither `cobc` nor internet access, so `core/cobol_runner.py` is a **pure-Python
  transliteration** of `data/src/legacy/INTCALC.cbl`'s logic, clearly marked as
  a stand-in for the real oracle. On your own machine (which will have
  GnuCOBOL per the real brief), swap it for an actual `cobc`-compiled call —
  the function signature is designed to make that a small change.
- **No `pydantic`, no bank LLM endpoint here either.** `infra/ai_contract.py`
  uses plain `dataclasses` instead of Pydantic v2 (same shape, swap trivially),
  and `infra/llm_client.py` is a **local heuristic stand-in**, not a real
  model call — because there's no network in this sandbox. Your four `ai/*.py`
  files are written to *use* `llm_client.call(...)`, so on the day you only
  replace `llm_client.py`'s internals with the real bank endpoint call — the
  four AI methods themselves don't need to change much.
- **12 practice rules, not 24.** Same five pathology classes as the real brief
  (COMP-3 rounding, signed overpunch, two-digit-year pivot, an ambiguous tier
  boundary, one undocumented/untraceable branch), just a smaller set so you can
  read the whole thing in one sitting.

## Quick start

```bash
cd uc04
python3 run.py baseline     # confirm everything fails with an empty ai/ (starting number)
make test                   # pre-built test suite — your progress bar
make demo                   # the 3-beat demo script
make score                  # held-back pass rate + diagnosis + evidence pack
```

### UI (optional)

There's also a small Streamlit control panel over the same pipeline, if you'd
rather click/type commands than remember `make` targets:

```bash
pip install streamlit
streamlit run app.py
```

It opens in your browser with a command box (`run`, `demo`, `test`, `score
[N]`, `verify`, `manifest`, `help`) plus sidebar buttons for the same
actions, and renders the pass rate, divergence table, guardrail verdicts,
and the evidence pack / HTML trace inline. It's a thin wrapper — `run.py`,
`demo.py`, `eval/score.py`, and `tools/manifest.py` still work standalone
from the terminal exactly as before.


## Layout

```
data/                 shipped, read-only in the real event
core/                 deterministic pipeline — pre-built, don't edit
platform/             contract, tracer, guardrails, llm client — pre-built
ai/                   THE ONLY FOLDER YOU EDIT (+ ai/prompts/*.md)
tests/                pre-built pass/fail suite
out/, traces/         generated each run
```

Read `core/pipeline.py` first — it's short and shows exactly where your four
methods plug in and in what order (test synthesis happens *before* your
implementation is generated — that's what makes the pass rate mean something).
