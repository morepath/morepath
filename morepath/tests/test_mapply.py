from __future__ import annotations

import pytest

from ..mapply import mapply


def test_mapply() -> None:
    def foo(a: int) -> str:
        return "foo with %s" % a

    assert mapply(foo, a=1) == "foo with 1"
    assert mapply(foo, a=1, b=2) == "foo with 1"


def test_mapply_fail() -> None:
    def foo(a: int) -> str:
        return "foo with %s" % a

    with pytest.raises(TypeError):
        mapply(foo, b=2)


def test_mapply_args() -> None:
    def foo(a: int) -> str:
        return "foo with %s" % a

    assert mapply(foo, 1) == "foo with 1"


def test_mapply_with_method() -> None:
    class Foo:
        def method(self, a: int) -> str:
            return "method with %s" % a

    f = Foo()
    assert mapply(f.method, a=1) == "method with 1"
    assert mapply(f.method, a=1, b=2) == "method with 1"


def test_mapply_with_constructor() -> None:
    class Foo:
        def __init__(self, a: int) -> None:
            self.a = a

    assert mapply(Foo, a=1).a == 1
    assert mapply(Foo, a=1, b=1).a == 1


def test_mapply_with_old_style_class() -> None:
    class Foo:
        def __init__(self, a: int) -> None:
            self.a = a

    assert mapply(Foo, a=1).a == 1
    assert mapply(Foo, a=1, b=1).a == 1


def test_mapply_callable_object() -> None:
    class Foo:
        def __call__(self, a: int) -> str:
            return "called with %s" % a

    f = Foo()
    assert mapply(f, a=1) == "called with 1"
    assert mapply(f, a=1, b=1) == "called with 1"


def test_mapply_non_function() -> None:
    a = 1

    with pytest.raises(Exception):
        assert mapply(a, a=1)  # type: ignore


def test_mapply_builtin() -> None:
    assert mapply(int, "1") == 1


def test_mapply_kw() -> None:
    def foo(**kw: int) -> dict[str, int]:
        return kw

    assert mapply(foo, a=1) == {"a": 1}


def test_mapply_args2() -> None:
    def foo(*args: int) -> tuple[int, ...]:
        return args

    assert mapply(foo, a=1) == ()
    assert mapply(foo, 1) == (1,)


def test_mapply_args_kw() -> None:
    def foo(*args: int, **kw: int) -> tuple[tuple[int, ...], dict[str, int]]:
        return args, kw

    assert mapply(foo, a=1) == ((), {"a": 1})
    assert mapply(foo, 1) == ((1,), {})
    assert mapply(foo, 1, a=1) == ((1,), {"a": 1})


def test_mapply_all_args_kw() -> None:
    def foo(
        a: int, *args: int, **kw: int
    ) -> tuple[int, tuple[int, ...], dict[str, int]]:
        return a, args, kw

    assert mapply(foo, 1) == (1, (), {})
    assert mapply(foo, 2, b=1) == (2, (), {"b": 1})
    assert mapply(foo, 2, 3, b=1) == (2, (3,), {"b": 1})


def test_mapply_class() -> None:
    class Foo:
        def __init__(self) -> None:
            pass

    assert isinstance(mapply(Foo), Foo)


def test_mapply_class_too_much() -> None:
    class Foo:
        def __init__(self) -> None:
            pass

    assert isinstance(mapply(Foo, a=1), Foo)


def test_mapply_classic_class_too_much() -> None:
    class Foo:
        def __init__(self) -> None:
            pass

    assert isinstance(mapply(Foo, a=1), Foo)


def test_mapply_class_no_init_too_much() -> None:
    class Foo:
        pass

    variables = {"base": None}
    assert isinstance(mapply(Foo, **variables), Foo)


def test_mapply_classic_class_no_init_too_much() -> None:
    class Foo:
        pass

    assert isinstance(mapply(Foo, a=1), Foo)


def test_mapply_kw_class() -> None:
    class Foo:
        def __init__(self, **kw: int) -> None:
            self.kw = kw

    assert mapply(Foo, a=1).kw == {"a": 1}


def test_mapply_args_class() -> None:
    class Foo:
        def __init__(self, *args: int) -> None:
            self.args = args

    assert mapply(Foo, a=1).args == ()
    assert mapply(Foo, 1).args == (1,)


def test_mapply_args_kw_class() -> None:
    class Foo:
        def __init__(self, *args: int, **kw: int) -> None:
            self.args = args
            self.kw = kw

    r = mapply(Foo, a=1)
    assert (r.args, r.kw) == ((), {"a": 1})
    r = mapply(Foo, 1)
    assert (r.args, r.kw) == ((1,), {})
    r = mapply(Foo, 1, a=1)
    assert (r.args, r.kw) == ((1,), {"a": 1})


def test_mapply_all_args_kw_class() -> None:
    class Foo:
        def __init__(self, a: int, *args: int, **kw: int) -> None:
            self.a = a
            self.args = args
            self.kw = kw

    r = mapply(Foo, 1)
    assert (r.a, r.args, r.kw) == (1, (), {})
    r = mapply(Foo, 2, b=1)
    assert (r.a, r.args, r.kw) == (2, (), {"b": 1})
    r = mapply(Foo, 2, 3, b=1)
    assert (r.a, r.args, r.kw) == (2, (3,), {"b": 1})
