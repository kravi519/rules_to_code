# Divergence diagnosis prompt

You are given: the rule, the triggering test vector, the oracle's expected
value, and the generated code's actual value. Classify the cause as exactly
one of:

- `implementation_defect` — the code is simply wrong against the rule as written
- `rounding_or_representation` — a numeric convention mismatch (rounding
  mode, decimal representation), not a logic error
- `ambiguous_rule` — the rule text genuinely supports more than one reading,
  and the code took a defensible one that isn't COBOL's
- `bad_test_vector` — the vector itself doesn't correctly exercise what it
  claims to

All four are legitimate. Concluding "COBOL is right, code is wrong" is the
common case, not the only acceptable one. State the fix; do not apply it to
the test yourself.
