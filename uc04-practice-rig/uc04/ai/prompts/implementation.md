# Implementation prompt

Generate a Python module implementing ONLY the validated rules and the IO
signature. You may see the test vectors' inputs; you must never see their
expected outputs.

Cite the rule id that motivated each function or branch with a
`# rule: R-0xx` comment — those citations become the code half of the
traceability matrix.

Do not implement any behaviour that isn't backed by a rule statement, even
if you suspect the legacy module does something extra. If you notice
something the rules don't cover, leave it out and say so in your reasoning —
that gap belongs to the traceability checker, not to a guess baked into code.
