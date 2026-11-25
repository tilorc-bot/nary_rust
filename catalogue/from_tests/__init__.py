"""Catalogue entries generated from SymPy's own test files.

``python -m catalogue.from_tests`` reads the asserts of each test file in
``rules.FILES`` (of the pinned SymPy) with ``ast`` and writes, for the file
with stem ``power``, ``power.py`` (the ledger and the generated entries) and
``power.md`` (the ledger as a table with links). ``generate`` says how,
``rules`` holds every hand-made decision.
"""
