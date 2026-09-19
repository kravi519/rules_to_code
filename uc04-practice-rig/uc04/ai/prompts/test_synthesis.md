# Test synthesis prompt

You are given ONE validated business rule and the IO signature. You are not
given, and must never look at, any implementation.

Produce input vectors that exercise this rule, INCLUDING its boundaries.
Think specifically about:
- a value exactly on any numeric boundary the rule mentions
- a value that would land exactly on a rounding boundary (half a cent)
- a value using an atypical but legal representation (signed overpunch,
  two-digit year at the pivot)
- at least one "obviously fine" value so a naive implementation isn't
  penalised for the wrong reason

Do not fabricate expected outputs — leave them blank; the oracle fills them
in afterwards. Cite which part of the rule statement or its note motivated
each boundary you chose.
