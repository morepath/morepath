from __future__ import unicode_literals
import pytest
from ..mapply import mapply


def test_mapply():
    def foo(a):
        return "foo with %s" % a

    assert mapply(foo, a=1) == "foo with 1"
    assert mapply(foo, a=1, b=2) == "foo with 1"


def test_mapply_fail():
    def foo(a):
        return "foo with %s" % a

    with pytest.raises(TypeError):
        mapply(foo, b=2)


def test_mapply_args():
    def foo(a):
        return "foo with %s" % a

    assert mapply(foo, 1) == 'foo with 1'


def test_mapply_with_method():
    class Foo(object):
        def method(self, a):
            return "method with %s" % a

    f = Foo()
    assert mapply(f.method, a=1) == "method with 1"
    assert mapply(f.method, a=1, b=2) == "method with 1"


def test_mapply_with_constructor():
    class Foo(object):
        def __init__(self, a):
            self.a = a

    assert mapply(Foo, a=1).a == 1
    assert mapply(Foo, a=1, b=1).a == 1


def test_mapply_with_old_style_class():
    class Foo:
        def __init__(self, a):
            self.a = a

    assert mapply(Foo, a=1).a == 1
    assert mapply(Foo, a=1, b=1).a == 1


def test_mapply_callable_object():
    class Foo(object):
        def __call__(self, a):
            return "called with %s" % a

    f = Foo()
    assert mapply(f, a=1) == 'called with 1'
    assert mapply(f, a=1, b=1) == 'called with 1'


def test_mapply_non_function():
    a = 1

    with pytest.raises(Exception):
        assert mapply(a, a=1)


def test_mapply_builtin():
    assert mapply(int, '1') == 1


def test_mapply_kw():
    def foo(**kw):
        return kw
    assert mapply(foo, a=1) == {'a': 1}


def test_mapply_args2():
    def foo(*args):
        return args
    assert mapply(foo, a=1) == ()
    assert mapply(foo, 1) == (1,)


def test_mapply_args_kw():
    def foo(*args, **kw):
        return args, kw
    assert mapply(foo, a=1) == ((), {'a': 1})
    assert mapply(foo, 1) == ((1,), {})
    assert mapply(foo, 1, a=1) == ((1,), {'a': 1})


def test_mapply_all_args_kw():
    def foo(a, *args, **kw):
        return a, args, kw
    assert mapply(foo, 1) == (1, (), {})
    assert mapply(foo, 2, b=1) == (2, (), {'b': 1})
    assert mapply(foo, 2, 3, b=1) == (2, (3,), {'b': 1})


def test_mapply_class():
    class Foo(object):
        def __init__(self):
            pass
    assert isinstance(mapply(Foo), Foo)


def test_mapply_class_too_much():
    class Foo(object):
        def __init__(self):
            pass
    assert isinstance(mapply(Foo, a=1), Foo)


def test_mapply_classic_class_too_much():
    class Foo:
        def __init__(self):
            pass
    assert isinstance(mapply(Foo, a=1), Foo)


def test_mapply_class_no_init_too_much():
    class Foo(object):
        pass
    variables = {'base': None}
    assert isinstance(mapply(Foo, **variables), Foo)


def test_mapply_classic_class_no_init_too_much():
    class Foo:
        pass
    assert isinstance(mapply(Foo, a=1), Foo)


def test_mapply_kw_class():
    class Foo(object):
        def __init__(self, **kw):
            self.kw = kw
    assert mapply(Foo, a=1).kw == {'a': 1}


def test_mapply_args_class():
    class Foo(object):
        def __init__(self, *args):
            self.args = args
    assert mapply(Foo, a=1).args == ()
    assert mapply(Foo, 1).args == (1,)


def test_mapply_args_kw_class():
    class Foo(object):
        def __init__(self, *args, **kw):
            self.args = args
            self.kw = kw
    r = mapply(Foo, a=1)
    assert (r.args, r.kw) == ((), {'a': 1})
    r = mapply(Foo, 1)
    assert (r.args, r.kw) == ((1,), {})
    r = mapply(Foo, 1, a=1)
    assert (r.args, r.kw) == ((1,), {'a': 1})


def test_mapply_all_args_kw_class():
    class Foo(object):
        def __init__(self, a, *args, **kw):
            self.a = a
            self.args = args
            self.kw = kw
    r = mapply(Foo, 1)
    assert (r.a, r.args, r.kw) == (1, (), {})
    r = mapply(Foo, 2, b=1)
    assert (r.a, r.args, r.kw) == (2, (), {'b': 1})
    r = mapply(Foo, 2, 3, b=1)
    assert (r.a, r.args, r.kw) == (2, (3,), {'b': 1})
