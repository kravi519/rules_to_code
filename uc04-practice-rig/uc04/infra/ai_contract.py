"""
infra/ai_contract.py — PRE-BUILT. The envelope every AI method returns.
Do not edit. (Practice-sandbox note: dataclasses stand in for the real
event's Pydantic v2 models — same fields, swap the base class later.)
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Generic, TypeVar, Optional

T = TypeVar("T")


@dataclass
class Citation:
    source: str                 # shipped file or table the evidence came from
    ref: str                    # row id, line range, or record key
    quote: Optional[str] = None


@dataclass
class AIResult(Generic[T]):
    value: Optional[T] = None
    confidence: float = 0.0     # 0.0-1.0, your own calibrated estimate
    citations: list[Citation] = field(default_factory=list)
    abstained: bool = False
    abstain_reason: Optional[str] = None
    reasoning: str = ""         # goes to the trace, never to an output document


class AILayer:
    """Base for every AI component. Implement the abstract method in ai/."""
    def __init__(self, llm, prompts, tracer=None):
        self.llm = llm
        self.prompts = prompts
        self.tracer = tracer

    def call(self, prompt_name: str, ctx: dict, schema=None):
        """Loads the named prompt, calls the LLM client, traces the call."""
        prompt = self.prompts.get(prompt_name)
        result = self.llm.call(prompt_name=prompt_name, prompt=prompt, ctx=ctx)
        if self.tracer:
            self.tracer.record_ai_call(prompt_name, ctx, result)
        return result
