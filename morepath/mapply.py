from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeVar

from reg import arginfo

if TYPE_CHECKING:
    from collections.abc import Callable

_T = TypeVar("_T")


def mapply(func: Callable[..., _T], *args: Any, **kw: Any) -> _T:
    """Apply keyword arguments to function only if it defines them.

    So this works without error as ``b`` is ignored::

      def foo(a):
          pass

      mapply(foo, a=1, b=2)

    Zope has an mapply that does this but a lot more too. pytest has
    an implementation of getting the argument names for a
    function/method that we've borrowed.
    """
    info = arginfo(func)
    assert info is not None
    if info.varkw:
        return func(*args, **kw)
    # XXX we don't support nested arguments
    # FIXME: we don't support keyword-only arguments
    new_kw = {name: kw[name] for name in info.args if name in kw}
    return func(*args, **new_kw)
