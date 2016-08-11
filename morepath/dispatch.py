import reg
from functools import wraps
from . import generic


class delegate(object):

    name_map = dict(
        permits='permits',
    )

    def __init__(self, *predicates):
        self.predicates = predicates

    def __call__(self, func):
        generic_name = self.name_map[func.__name__]

        if not hasattr(generic, generic_name):
            setattr(generic, generic_name,
                    reg.dispatch(*self.predicates)(func))

        @wraps(func)
        def delegator(self, *args, **kw):
            return getattr(generic, generic_name)(
                self, lookup=self.lookup, *args, **kw)

        return delegator
