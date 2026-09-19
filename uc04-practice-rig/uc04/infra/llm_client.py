"""
infra/llm_client.py — PRE-BUILT (but designed to be the ONE file you swap
wholesale on the real event day, alongside this docstring's advice).

PRACTICE-SANDBOX STAND-IN: no network here, so there is no real model call.
PromptLoader is real and used as intended (prompts are files, not inline
strings — that part of the contract holds even in practice). LLMClient.call()
is a stub that raises on purpose: your ai/*.py files in this sandbox compute
their results directly in Python (that's where the practice value is — the
decomposition and the abstention judgement, not prompting a live model). On
the real event day, wire LLMClient.call() to the bank-provided endpoint and
your ai/*.py can be simplified to just build ctx + schema and call self.llm.
"""
from __future__ import annotations
from pathlib import Path

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "ai" / "prompts"


class PromptLoader:
    def __init__(self):
        self._cache: dict[str, str] = {}

    def get(self, name: str) -> str:
        if name not in self._cache:
            path = PROMPTS_DIR / name
            if not path.exists():
                raise FileNotFoundError(
                    f"prompt file missing: {path} — prompts must be files, "
                    f"not inline strings (infra contract rule 7)."
                )
            self._cache[name] = path.read_text()
        return self._cache[name]


class LLMClient:
    def call(self, prompt_name: str, prompt: str, ctx: dict):
        raise NotImplementedError(
            "No live model in this practice sandbox (no network). Your ai/*.py "
            "files compute results directly for now; wire this method to the "
            "real endpoint on event day and route ai/*.py through it."
        )
