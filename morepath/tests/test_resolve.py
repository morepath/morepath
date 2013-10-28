# -*- coding: utf-8 -*-

from reg import Lookup, ClassRegistry
#from morepath.interfaces import IConsumer
from morepath import generic
from morepath.pathstack import parse_path, DEFAULT
from morepath.request import Request
from morepath.publish import resolve_model
from werkzeug.test import EnvironBuilder


class Traverser(object):
    """A traverser is a consumer that consumes only a single step.

    Only the top of the stack is popped.

    Should be constructed with a traversal function. The function
    takes three arguments: the object to traverse into, and the namespace
    and name to traverse. It should return either the object traversed towards,
    or None if this object cannot be found.
    """

    def __init__(self, func):
        self.func = func

    def __call__(self, obj, stack, lookup):
        ns, name = stack.pop()
        next_obj = self.func(obj, ns, name)
        if next_obj is None:
            stack.append((ns, name))
            return False, obj, stack
        return True, next_obj, stack


def get_request(*args, **kw):
    return Request(EnvironBuilder(*args, **kw).get_environ())


def get_registry():
    return ClassRegistry()


def get_lookup(registry):
    return Lookup(registry)


class Container(dict):
    pass


class Model(object):
    def __repr__(self):
        return "<Model>"


def get_structure():
    """A structure of containers and models.

    The structure is:

    /a
    /sub
    /sub/b

    all starting at root.
    """

    root = Container()

    a = Model()
    root['a'] = a

    sub = Container()
    root['sub'] = sub

    b = Model()
    sub['b'] = b
    sub.attr = b

    return root


def test_resolve_no_consumers():
    lookup = get_lookup(get_registry())
    base = object()

    stack = parse_path(u'/a')
    obj, unconsumed, lookup = resolve_model(base, stack, lookup)

    assert obj is base
    assert unconsumed == [(DEFAULT, u'a')]
    assert lookup is lookup


def test_resolve_traverse():
    reg = get_registry()

    lookup = get_lookup(reg)

    reg.register(generic.consumer, [Container], Traverser(traverse_container))

    base = get_structure()

    assert resolve_model(base, parse_path(u'/a'), lookup) == (
        base['a'], [], lookup)
    assert resolve_model(base, parse_path(u'/sub'), lookup) == (
        base['sub'], [], lookup)
    assert resolve_model(base, parse_path(u'/sub/b'), lookup) == (
        base['sub']['b'], [], lookup)

    # there is no /c
    assert resolve_model(base, parse_path(u'/c'), lookup) == (
        base, [(DEFAULT, u'c')], lookup)

    # there is a sub, but no c in sub
    assert resolve_model(base, parse_path(u'/sub/c'), lookup) == (
        base['sub'], [(DEFAULT, u'c')], lookup)


def traverse_container(container, ns, name):
    if ns != DEFAULT:
        return None
    return container.get(name)


def traverse_attributes(container, ns, name):
    if ns != DEFAULT:
        return None
    return getattr(container, name, None)
