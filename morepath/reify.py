# Originally taken from pyramid.decorator
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generic, TypeVar, overload

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing_extensions import Self

_T = TypeVar("_T")


class reify(Generic[_T]):
    """Cache a property.

    Use as a method decorator.  It operates almost exactly like the
    Python ``@property`` decorator, but it puts the result of the
    method it decorates into the instance dict after the first call,
    effectively replacing the function it decorates with an instance
    variable.  It is, in Python parlance, a non-data descriptor. An
    example:

    .. testcode::

      from morepath import reify

      class Foo:
          @reify
          def jammy(self):
              print('jammy called')
              return 1

    And usage of Foo:

      >>> f = Foo()
      >>> v = f.jammy
      jammy called
      >>> print(v)
      1
      >>> print(f.jammy)
      1
      >>> # jammy func not called the second time; it replaced itself with 1

    """

    def __init__(self, wrapped: Callable[[Any], _T]) -> None:
        self.wrapped = wrapped
        self.__doc__ = wrapped.__doc__

    @overload
    def __get__(
        self, inst: None, objtype: type[object] | None = None
    ) -> Self: ...
    @overload
    def __get__(
        self, inst: object, objtype: type[object] | None = None
    ) -> _T: ...

    def __get__(
        self, inst: object | None, objtype: type[object] | None = None
    ) -> Self | _T:
        if inst is None:
            return self
        val = self.wrapped(inst)
        setattr(inst, self.wrapped.__name__, val)
        return val
