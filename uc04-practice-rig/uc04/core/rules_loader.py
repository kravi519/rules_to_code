"""
core/rules_loader.py — PRE-BUILT. Loads and validates the rule list and IO
signature. Do not edit.
"""
from __future__ import annotations
import yaml
from pathlib import Path
from core.models import BusinessRule, IOSignature

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def load_rules() -> list[BusinessRule]:
    raw = yaml.safe_load((DATA_DIR / "rules" / "validated_rules.yaml").read_text())
    rules = []
    for r in raw["rules"]:
        rules.append(BusinessRule(
            id=r["id"],
            statement=r["statement"].strip(),
            fields=r.get("fields", []),
            note=r.get("note"),
        ))
    ids = [r.id for r in rules]
    assert len(ids) == len(set(ids)), "duplicate rule ids in validated_rules.yaml"
    return rules


def load_io_signature() -> IOSignature:
    raw = yaml.safe_load((DATA_DIR / "signature" / "io_signature.yaml").read_text())
    return IOSignature(raw=raw)
