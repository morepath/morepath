from __future__ import annotations

from pdb import Pdb  # pragma: nocoverage
from typing import Any

morepath_pdb = Pdb(
    skip=["reg.*", "inspect", "repoze.lru"]
)  # pragma: nocoverage


def set_trace(*args: Any, **kw: Any) -> None:  # pragma: nocoverage
    """Set pdb trace as in ``import pdb; pdb.set_trace``, ignores ``reg``.

    Use ``from morepath import pdbsupport; pdbsupport.set_trace()`` to use.

    The debugger won't step into ``reg``, ``inspect`` or ``repoze.lru``.
    """
    return morepath_pdb.set_trace(*args, **kw)
