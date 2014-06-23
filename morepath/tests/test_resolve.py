# -*- coding: utf-8 -*-

from reg import Lookup, ClassRegistry
import morepath
from morepath import generic
from morepath.traject import VIEW_PREFIX
from morepath.request import Request
from morepath.publish import resolve_model
import webob


def setup_module(module):
    morepath.disable_implicit()


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

    def __call__(self, request, model, lookup):
        if not request.unconsumed:
            return None
        name = request.unconsumed.pop()
        next_model = self.func(model, name)
        if next_model is None:
            request.unconsumed.append(name)
            return None
        return next_model


def get_request(path, lookup):
    request = Request(webob.Request.blank(path).environ)
    request.lookup = lookup
    return request


def get_registry():
    return ClassRegistry()


def get_lookup(registry):
    return Lookup(registry)


class Container(dict):
    lookup = None

    def set_implicit(self):
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
    request = get_request(path='/a', lookup=lookup)

    class DummyBase(object):
        lookup = None

        def set_implicit(self):
            pass

    base = DummyBase()

    request.mounted = base

    obj = resolve_model(request)

    assert obj is base
    assert request.unconsumed == [u'a']
    assert request.lookup is lookup


def test_resolve_traverse():
    reg = get_registry()

    lookup = get_lookup(reg)

    reg.register(generic.consume, [Request, Container],
                 Traverser(traverse_container))

    base = get_structure()
    request = get_request(path='/a', lookup=lookup)
    request.mounted = base
    obj = resolve_model(request)
    assert obj is base['a']
    assert request.unconsumed == []
    assert request.lookup is lookup

    request = get_request(path='/sub', lookup=lookup)
    request.mounted = base

    obj = resolve_model(request)
    assert obj is base['sub']
    assert request.unconsumed == []
    assert request.lookup is lookup

    request = get_request(path='/sub/b', lookup=lookup)
    request.mounted = base

    obj = resolve_model(request)
    assert obj is base['sub']['b']
    assert request.unconsumed == []
    assert request.lookup is lookup

    # there is no /c
    request = get_request(path='/c', lookup=lookup)
    request.mounted = base

    obj = resolve_model(request)
    assert obj is base
    assert request.unconsumed == ['c']
    assert request.lookup is lookup

    # there is a sub, but no c in sub
    request = get_request(path='/sub/c', lookup=lookup)
    request.mounted = base

    obj = resolve_model(request)
    assert obj is base['sub']
    assert request.unconsumed == ['c']
    assert request.lookup is lookup


def traverse_container(container, name):
    if name.startswith(VIEW_PREFIX):
        return None
    return container.get(name)


def traverse_attributes(container, name):
    if name.startswith(VIEW_PREFIX):
        return None
    return getattr(container, name, None)
