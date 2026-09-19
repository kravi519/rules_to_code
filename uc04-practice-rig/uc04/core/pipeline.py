"""
core/pipeline.py — PRE-BUILT. Wires the nine steps and calls your AI layer.
Do not edit. Practice-sandbox note: the real event ships this file as-is on
your machine; reading it is the fastest way to see exactly where your four
methods plug in and in what order.
"""
from __future__ import annotations
import time
import types
from pathlib import Path

import yaml

from core.rules_loader import load_rules, load_io_signature
from core.cobol_runner import run_cobol
from core.harness import run_harness
from core.evidence_render import render as render_evidence
from infra.tracer import Tracer
from infra.llm_client import PromptLoader, LLMClient
from infra import guardrails
from ai.test_synthesis import TestSynthesisAI
from ai.implementation import ImplementationAI
from ai.divergence import DivergenceAI
from ai.evidence import EvidenceAI

ROOT = Path(__file__).resolve().parent.parent
VECTORS_PATH = ROOT / "data" / "vectors" / "seed_vectors.jsonl"  # placeholder, unused by this pipeline


def _load_module_from_source(source_code: str):
    module = types.ModuleType("generated_implementation")
    exec(compile(source_code, "<generated>", "exec"), module.__dict__)
    return module


def run_pipeline(case_id: str = "local") -> dict:
    config = yaml.safe_load((ROOT / "infra" / "config.yaml").read_text())
    trace_path = ROOT / "traces" / f"run_{case_id}_{int(time.time())}.html"
    tracer = Tracer(trace_path, case_id, config)
    prompts = PromptLoader()
    llm = LLMClient()

    t0 = time.time()
    rules = load_rules()
    sig = load_io_signature()
    tracer.record_step("1_load_rules_and_signature", "deterministic", time.time() - t0)

    # 2. Synthesise test vectors PER RULE — implementation not in scope yet.
    t0 = time.time()
    synth = TestSynthesisAI(llm, prompts, tracer)
    all_vectors = []
    for rule in rules:
        result = synth.synthesise(rule, sig)
        if result.abstained:
            continue
        all_vectors.extend(result.value)
    tracer.record_step("2_synthesise_test_vectors", "ai", time.time() - t0, f"{len(all_vectors)} vectors")

    # 3. Execute COBOL (oracle) for the golden output — fills `.expected`.
    t0 = time.time()
    for v in all_vectors:
        v.expected = run_cobol(v.inputs)
    tracer.record_step("3_execute_cobol_oracle", "deterministic", time.time() - t0)

    # 4. Generate the implementation. Note: this happens AFTER step 2/3 —
    #    test synthesis never had this in scope (guardrail G1).
    t0 = time.time()
    impl_ai = ImplementationAI(llm, prompts, tracer)
    impl_result = impl_ai.generate(rules, sig, all_vectors)
    source = impl_result.value
    generated_module = _load_module_from_source(source.content)
    tracer.record_step("4_generate_implementation", "ai", time.time() - t0)

    # 5. Run both, find divergences.
    t0 = time.time()
    facts_bundle = run_harness(rules, all_vectors, generated_module, source.content)
    tracer.record_step("5_run_differential", "deterministic", time.time() - t0,
                        f"{len(facts_bundle['divergences'])} divergence(s)")

    # 6. Diagnose each divergence.
    t0 = time.time()
    diag_ai = DivergenceAI(llm, prompts, tracer)
    rules_by_id = {r.id: r for r in rules}
    vectors_by_id = {v.id: v for v in all_vectors}
    diagnoses = []
    for d in facts_bundle["divergences"]:
        rule = rules_by_id[d["rule_id"]]
        vector = vectors_by_id[d["vector_id"]]
        result = diag_ai.diagnose(rule, vector, d["expected"], d["actual"])
        diagnoses.append(result.value)
    tracer.record_step("6_diagnose_divergences", "ai", time.time() - t0)

    # 7. Traceability matrix — already built inside run_harness (step 5/7 combined
    #    here since both are pure functions of the same inputs).
    matrix = facts_bundle["matrix"]

    # 8. Draft evidence sections.
    t0 = time.time()
    ev_ai = EvidenceAI(llm, prompts, tracer)
    sections = {}
    for kind, facts in facts_bundle["facts"].items():
        result = ev_ai.write_section(kind, facts)
        sections[kind] = result.value
    tracer.record_step("8_draft_evidence_sections", "ai", time.time() - t0)

    # 9. Render the approval pack.
    t0 = time.time()
    out_path = ROOT / "out" / "evidence_pack.html"
    render_evidence(sections, out_path)
    tracer.record_step("9_render_evidence_pack", "deterministic", time.time() - t0)

    # Guardrails, checked after the run.
    evidence_text = " ".join(sections.values())
    checks = guardrails.run_all(
        vectors=all_vectors,
        generated_available_at_synthesis=False,
        evidence_text=evidence_text,
        untraceable_findings=facts_bundle["untraceable"],
        matrix=matrix,
        vectors_path=VECTORS_PATH,
        hash_before="",
    )
    for name, ok, reason in checks:
        tracer.record_guardrail(name, ok, reason)

    return {
        "vectors": all_vectors,
        "pass_rate": facts_bundle["pass_rate"],
        "divergences": facts_bundle["divergences"],
        "diagnoses": diagnoses,
        "matrix": matrix,
        "untraceable": facts_bundle["untraceable"],
        "untested_rules": facts_bundle["untested_rules"],
        "guardrails": checks,
        "trace_path": str(trace_path),
        "evidence_path": str(out_path),
    }
