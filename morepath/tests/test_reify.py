from __future__ import annotations

from typing import Any

from morepath import reify

# from pyramid.tests.test_decorator


def test__get__with_inst() -> None:
    def wrapped(inst: object) -> str:
        return "a"

    decorator = reify(wrapped)
    inst = Dummy()
    result = decorator.__get__(inst)
    assert result == "a"
    assert inst.__dict__["wrapped"] == "a"


def test__get__noinst() -> None:
    decorator: reify[Any] = reify(None)  # type: ignore[arg-type]
    assert decorator.__get__(None) is decorator


def test__doc__copied() -> None:
    def wrapped(inst: object) -> None:
        """My doc"""

    decorator = reify(wrapped)
    assert decorator.__doc__ == "My doc"


def test_no_doc() -> None:
    def wrapped(inst: object) -> None:
        pass

    decorator = reify(wrapped)
    assert decorator.__doc__ is None


class Dummy:
    pass
