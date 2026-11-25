"""How much of what SymPy's own tests check does nary do? (issue #35)

``python -m scoreboard.report`` runs the SymPy test files of ``rules.FILES``
on nary and writes one report for each, such as ``power.md``: how many
cases pass, the gaps, and the cases left out, each with its reason.
``collect`` runs the tests, ``report`` scores the cases and writes the
report, ``rules`` holds the hand-written tables.
"""
