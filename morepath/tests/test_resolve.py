# -*- coding: utf-8 -*-

from comparch import Lookup, ClassRegistry
from morepath.interfaces import (IConsumer, IResource,
                                 ResolveError, ModelError, ResourceError)
from morepath.pathstack import parse_path, create_path, DEFAULT, RESOURCE
from morepath.request import Request
from morepath.resolve import ModelResolver, ResourceResolver, Traverser
from werkzeug.test import EnvironBuilder
import pytest

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
    
    return root

def test_resolve_no_consumers():
    resolver = ModelResolver(get_lookup(get_registry()))
    base = object()

    stack = parse_path(u'/a')
    obj, unconsumed = resolver(base, stack)

    assert obj is base
    assert unconsumed == [(DEFAULT, u'a')]

def test_resolve_traverse():
    reg = get_registry()
    
    resolver = ModelResolver(get_lookup(reg))

    reg.register(IConsumer, (Container,), Traverser(traverse_container))

    base = get_structure()

    assert resolver(base, parse_path(u'/a')) == (base['a'], [])
    assert resolver(base, parse_path(u'/sub')) == (base['sub'], []) 
    assert resolver(base, parse_path(u'/sub/b')) == (base['sub']['b'], [])

    # there is no /c
    assert resolver(base, parse_path(u'/c')) == (base, [(DEFAULT, u'c')])

    # there is a sub, but no c in sub
    assert resolver(base, parse_path(u'/sub/c')) == (
        base['sub'], [(DEFAULT, u'c')])

def test_resolve_resource():
    reg = get_registry()

    model = Model()

    def resource(request, model):
        return 'resource'
    
    reg.register(IResource, (Request, Model), resource)
    
    resolver = ResourceResolver(get_lookup(reg))

    req = get_request()
    assert resolver(req, model, parse_path(u'')) == 'resource'
    assert req.resolver_info()['name'] == u''
    req = get_request()
    # this will work for any name given the resource we registered
    assert resolver(req, model, parse_path(u'something')) == 'resource'
    assert req.resolver_info()['name'] == u'something'
    
def test_resolve_errors():
    reg = get_registry()
    model = Model()
    
    resolver = ResourceResolver(get_lookup(reg))
    
    request = get_request()

    with pytest.raises(ModelError) as e:
        resolver(request, model, parse_path(u'a/b'))
    assert str(e.value) == (
        "<Model> has unresolved path /a/b")
    
    with pytest.raises(ResolveError) as e:
        resolver(request, model, [])
    assert str(e.value) == "<Model> has no default resource"
        
    with pytest.raises(ResolveError) as e:
        resolver(request, model, parse_path(u'test'))
    assert str(e.value) == "<Model> has neither resource nor sub-model: /test"
    
def traverse_container(container, ns, name):
    if ns != DEFAULT:
        return None
    return container.get(name)
