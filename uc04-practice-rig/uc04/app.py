"""
app.py — Streamlit control panel for the UC-04 Rules-to-Code Practice Lab.

A small command-driven UI over the same pipeline you'd otherwise drive from
the terminal (run.py / demo.py / eval/score.py / tools/manifest.py). Type a
command in the box at the top, or use the sidebar buttons — both do the same
thing.

Run it with:
    pip install streamlit
    streamlit run app.py

Commands understood in the text box:
    run [case_id]      — full pipeline once (default case_id: "ui")
    demo               — the 3-beat demo script
    test               — the pytest suite
    score [N]          — score, optionally repeated N times (default 1)
    verify             — checksum check (nothing outside ai/ changed)
    manifest           — (re)write the checksum manifest
    help               — show this list
"""
from __future__ import annotations
import subprocess
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from core.pipeline import run_pipeline  # noqa: E402

st.set_page_config(page_title="UC-04 Rules-to-Code Practice Lab", layout="wide")


# ---------------------------------------------------------------- helpers --

def _run_subprocess(args: list[str]) -> tuple[int, str]:
    proc = subprocess.run(args, cwd=str(ROOT), capture_output=True, text=True)
    output = proc.stdout + ("\n" + proc.stderr if proc.stderr else "")
    return proc.returncode, output


def _render_pipeline_result(result: dict):
    pr = result["pass_rate"]
    col1, col2, col3 = st.columns(3)
    col1.metric("Pass rate", f"{pr['passed']}/{pr['total']}", f"{pr['pass_rate']*100:.1f}%")
    col2.metric("Divergences", len(result["divergences"]))
    breaches = [name for name, ok, _ in result["guardrails"] if not ok]
    col3.metric("Guardrail breaches", len(breaches), delta_color="inverse")

    if result["divergences"]:
        st.subheader("Divergences & diagnoses")
        diag_by_vector = {d.vector_id: d for d in result["diagnoses"]}
        rows = []
        for d in result["divergences"]:
            diag = diag_by_vector.get(d["vector_id"])
            rows.append({
                "vector": d["vector_id"],
                "rule": d["rule_id"],
                "field": d["field"],
                "expected": d["expected"],
                "actual": d["actual"],
                "cause": diag.cause if diag else "?",
                "suggested_fix": diag.suggested_fix if diag else "",
            })
        st.table(rows)
    else:
        st.success("No divergence found.")

    if result["untraceable"]:
        st.subheader("Untraceable behaviour")
        for u in result["untraceable"]:
            st.warning(f"**{u['field']}** — example vector `{u['example_vector_id']}`: {u['note']}")

    if result["untested_rules"]:
        st.subheader("Untested rules")
        st.write(result["untested_rules"])

    st.subheader("Guardrails")
    st.table([{"guardrail": name, "verdict": "PASS" if ok else "BREACH", "reason": reason}
              for name, ok, reason in result["guardrails"]])

    st.subheader("Evidence pack")
    evidence_path = Path(result["evidence_path"])
    if evidence_path.exists():
        st.components.v1.html(evidence_path.read_text(), height=500, scrolling=True)
    st.caption(f"Trace file: `{result['trace_path']}`")
    trace_path = Path(result["trace_path"])
    if trace_path.exists():
        with st.expander("Open HTML trace inline"):
            st.components.v1.html(trace_path.read_text(), height=600, scrolling=True)


def dispatch(command: str):
    parts = command.strip().split()
    if not parts:
        return
    cmd, args = parts[0].lower(), parts[1:]

    if cmd == "run":
        case_id = args[0] if args else "ui"
        with st.spinner(f"Running pipeline (case: {case_id})..."):
            result = run_pipeline(case_id=case_id)
        st.session_state["last_result"] = result
        _render_pipeline_result(result)

    elif cmd == "demo":
        with st.spinner("Running demo..."):
            code, out = _run_subprocess([sys.executable, "demo.py"])
        st.code(out, language="text")
        if code != 0:
            st.error(f"demo.py exited with code {code}")

    elif cmd == "test":
        with st.spinner("Running pytest..."):
            code, out = _run_subprocess([sys.executable, "-m", "pytest", "tests/", "-v"])
        st.code(out, language="text")
        (st.success if code == 0 else st.error)(f"pytest exited with code {code}")

    elif cmd == "score":
        repeat = args[0] if args else "1"
        with st.spinner(f"Scoring (repeat={repeat})..."):
            code, out = _run_subprocess([sys.executable, "eval/score.py", "--repeat", repeat])
        st.code(out, language="text")

    elif cmd == "verify":
        code, out = _run_subprocess([sys.executable, "tools/manifest.py", "check"])
        st.code(out, language="text")
        (st.success if code == 0 else st.error)(out.strip().splitlines()[-1] if out.strip() else "")

    elif cmd == "manifest":
        code, out = _run_subprocess([sys.executable, "tools/manifest.py", "write"])
        st.code(out, language="text")

    elif cmd == "help":
        st.info(__doc__)

    else:
        st.error(f"Unknown command: '{cmd}'. Type 'help' for the list.")


# --------------------------------------------------------------------- UI --

st.title("UC-04 Rules-to-Code Practice Lab")
st.caption("From Validated Rules to Tested Code — command console")

command = st.text_input(
    "Command",
    placeholder="run | demo | test | score [N] | verify | manifest | help",
)
run_clicked = st.button("Run command", type="primary")

st.sidebar.header("Quick actions")
if st.sidebar.button("Run pipeline"):
    command, run_clicked = "run", True
if st.sidebar.button("Run demo"):
    command, run_clicked = "demo", True
if st.sidebar.button("Run tests"):
    command, run_clicked = "test", True
repeat_n = st.sidebar.number_input("Score repeat", min_value=1, max_value=5, value=1)
if st.sidebar.button("Run score"):
    command, run_clicked = f"score {int(repeat_n)}", True
if st.sidebar.button("Verify (no core edits)"):
    command, run_clicked = "verify", True
if st.sidebar.button("Write manifest"):
    command, run_clicked = "manifest", True

st.divider()

if run_clicked and command:
    dispatch(command)
elif "last_result" in st.session_state:
    st.caption("Showing the last pipeline run. Enter a command above to run again.")
    _render_pipeline_result(st.session_state["last_result"])
else:
    st.info("Enter a command above, or use the sidebar, to get started. Try `run` first.")
