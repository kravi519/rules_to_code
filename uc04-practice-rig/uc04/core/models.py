"""
core/models.py — PRE-BUILT. Shared data shapes for the whole pipeline.

Practice-sandbox note: the real event ships these as Pydantic v2 models.
This sandbox has no network to install pydantic, so these are plain
dataclasses with the same field names — swap the base class, not the shape,
when you move to the real stack.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class BusinessRule:
    id: str
    statement: str
    fields: list[str] = field(default_factory=list)
    note: Optional[str] = None


@dataclass
class IOSignature:
    raw: dict


@dataclass
class TestVector:
    id: str
    rule_id: str
    inputs: dict
    expected: Optional[dict] = None       # filled in by the oracle, never by you
    rationale: str = ""                    # why this vector exists (boundary, pathology, ...)


@dataclass
class SourceFile:
    path: str
    content: str


@dataclass
class Diagnosis:
    vector_id: str
    rule_id: str
    cause: str              # one of: implementation_defect | rounding_or_representation |
                             #         ambiguous_rule | bad_test_vector
    explanation: str
    suggested_fix: str


@dataclass
class EvidenceFacts:
    kind: str
    facts: dict
