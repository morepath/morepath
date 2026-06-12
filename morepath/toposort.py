"""Topological sort functionality."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generic, TypeVar

from dectate import topological_sort

if TYPE_CHECKING:
    from collections.abc import Collection


_T = TypeVar("_T")
_InfoT = TypeVar("_InfoT", bound="Info[Any]")


def toposorted(infos: Collection[_InfoT]) -> list[_InfoT]:
    """Sort infos topologically.

    Info object must have a ``key`` attribute, and ``before`` and ``after``
    attributes that returns a list of keys. You can use :class:`Info`.
    """
    key_to_info: dict[Any, _InfoT] = {}
    depends: dict[Any, list[_InfoT]] = {}
    for info in infos:
        key_to_info[info.key] = info
        depends[info.key] = []
    for info in infos:
        for after in info.after:
            after_info = key_to_info[after]
            depends[info.key].append(after_info)
        for before in info.before:
            before_info = key_to_info[before]
            depends[before_info.key].append(info)
    return topological_sort(infos, lambda info: depends[info.key])


class Info(Generic[_T]):
    """Toposorted info helper.

    Base class that helps with toposorted. ``before`` and ``after``
    can be lists of keys, or a single key, or ``None``.
    """

    def __init__(
        self,
        key: _T,
        before: list[_T] | tuple[_T, ...] | _T | None,
        after: list[_T] | tuple[_T, ...] | _T | None,
    ) -> None:
        self.key = key
        self.before = _convert_before_after(before)
        self.after = _convert_before_after(after)


def _convert_before_after(
    keys: list[_T] | tuple[_T, ...] | _T | None,
) -> list[_T]:
    if isinstance(keys, (list, tuple)):
        return list(keys)
    elif keys is None:
        return []
    else:
        return [keys]
