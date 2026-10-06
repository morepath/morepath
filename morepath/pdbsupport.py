from __future__ import annotations

from pdb import Pdb
from typing import Any

morepath_pdb = Pdb(skip=["reg.*", "inspect"])


def set_trace(*args: Any, **kw: Any) -> None:
    """Set pdb trace as in ``import pdb; pdb.set_trace``, ignores ``reg``.

    Use ``from morepath import pdbsupport; pdbsupport.set_trace()`` to use.

    The debugger won't step into ``reg`` or ``inspect``.
    """
    return morepath_pdb.set_trace(*args, **kw)
