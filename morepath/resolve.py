# -*- coding: utf-8 -*-
from .interfaces import (IConsumer, IResource, ILookup,
                         ResolveError, ModelError, ResourceError)
from .pathstack import create_path, RESOURCE, DEFAULT

DEFAULT_NAME = u''

def resolve_model(obj, stack, lookup):
    """Resolve path to a model using consumers.
    """
    unconsumed = stack[:]
    while unconsumed:
        for consumer in IConsumer.all(obj, lookup=lookup):
            any_consumed, obj, unconsumed = consumer(
                obj, unconsumed, lookup)
            if any_consumed:
                # get new lookup for whatever we found if it exists
                lookup = ILookup.adapt(obj, lookup=lookup, default=lookup)
                break
        else:
            # nothing could be consumed
            break
    return obj, unconsumed, lookup

# handy for debuggability
class ResourceSentinel(object):
    def __repr__(self):
        return "<ResourceSentinel>"
    
RESOURCE_SENTINEL = ResourceSentinel()

def resolve_resource(request, model, stack, lookup):
    ns, name = get_resource_step(model, stack)

    if ns not in (DEFAULT, RESOURCE):
        # XXX also report on resource name
        raise ResourceError(
            "namespace %r is not supported:" % ns)

    request.set_resolver_info({'name': name})
    resource = IResource.adapt(request, model,
                               default=RESOURCE_SENTINEL,
                               lookup=lookup)
    if resource is not RESOURCE_SENTINEL:
        return resource

    # XXX how can we report if failure is there due to predicate
    # mismatch as opposed to the name being missing?
    if ns == RESOURCE:
        if name == DEFAULT_NAME:
            raise ResourceError(
                "%r has no default resource" % model)
        else:
            raise ResourceError(
                "%r has no resource: %s" % (model, create_path(stack)))
    raise ResolveError(
        "%r has neither resource nor sub-model: %s" %
        (model, create_path(stack)))


def get_resource_step( model, stack):
    unconsumed_amount = len(stack)
    if unconsumed_amount == 0:
        return RESOURCE, DEFAULT_NAME
    elif unconsumed_amount == 1:
        return stack[0]
    raise ModelError(
        "%r has unresolved path %s" % (model, create_path(stack)))

class ResourceResolver(object):
    default_name = u''

    def __init__(self, lookup):
        self.lookup = lookup

    def get_resource_step(self, model, stack):
        unconsumed_amount = len(stack)
        if unconsumed_amount == 0:
            return RESOURCE, self.default_name
        elif unconsumed_amount == 1:
            return stack[0]
        raise ModelError(
            "%r has unresolved path %s" % (model, create_path(stack)))
        
    def __call__(self, request, model, stack):
        ns, name = self.get_resource_step(model, stack)
        
        if ns not in (DEFAULT, RESOURCE):
            # XXX also report on resource name
            raise ResourceError(
                "namespace %r is not supported:" % ns)

        request.set_resolver_info({'name': name})
        resource = IResource.adapt(request, model,
                                   default=RESOURCE_SENTINEL,
                                   lookup=self.lookup)
        if resource is not RESOURCE_SENTINEL:
            return resource

        # XXX how can we report if failure is there due to predicate
        # mismatch as opposed to the name being missing?
        if ns == RESOURCE:
            if name == self.default_name:
                raise ResourceError(
                    "%r has no default resource" % model)
            else:
                raise ResourceError(
                    "%r has no resource: %s" % (model, create_path(stack)))
        raise ResolveError(
            "%r has neither resource nor sub-model: %s" %
            (model, create_path(stack)))

class Traverser(IConsumer):
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
