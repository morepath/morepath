from pdb import Pdb


morepath_pdb = Pdb(skip=['reg.*', 'inspect', 'repoze.lru'])


def set_trace(*args, **kw):
    """Set pdb trace as in ``import pdb; pdb.set_trace``, ignores ``reg``.

    Use ``from morepath import pdbsupport; pdbsupport.set_trace()`` to use.

    The debugger won't step into ``reg``, ``inspect`` or ``repoze.lru``.
    """
    return morepath_pdb.set_trace(*args, **kw)  # pragma: nocoverage
