# Originally taken from pyramid.decorator


class reify(object):
    """Cache a property.

    Use as a method decorator.  It operates almost exactly like the
    Python ``@property`` decorator, but it puts the result of the
    method it decorates into the instance dict after the first call,
    effectively replacing the function it decorates with an instance
    variable.  It is, in Python parlance, a non-data descriptor. An
    example:

    .. testcode::

      from morepath import reify

      class Foo(object):
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

    def __init__(self, wrapped):
        self.wrapped = wrapped
        self.__doc__ = wrapped.__doc__

    def __get__(self, inst, objtype=None):
        if inst is None:
            return self
        val = self.wrapped(inst)
        setattr(inst, self.wrapped.__name__, val)
        return val
