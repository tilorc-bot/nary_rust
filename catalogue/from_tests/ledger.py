"""A row of the ledger: one per assert statement of a SymPy test file."""

from dataclasses import dataclass

from ..entry import Source

__all__ = ["Row"]


@dataclass(frozen=True)
class Row:
    """What became of the assert at ``source``: its ``category`` (a key of
    ``rules.CATEGORIES``), the ``reason`` where it is not an entry, and the
    names of the catalogue entries it gave (generated or hand-written)."""
    source: Source
    category: str
    reason: str = ""
    entries: tuple = ()

    @property
    def id(self):
        return self.source.id
