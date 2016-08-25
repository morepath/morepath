from reg.arginfo import arginfo


def mapply(func, *args, **kw):
    """Apply keyword arguments to function only if it defines them.

    So this works without error as ``b`` is ignored::

      def foo(a):
          pass

      mapply(foo, a=1, b=2)

    Zope has an mapply that does this but a lot more too. py.test has
    an implementation of getting the argument names for a
    function/method that we've borrowed.
    """
    info = arginfo(func)
    if info.keywords:
        return func(*args, **kw)
    # XXX we don't support nested arguments
    new_kw = dict((name, kw[name]) for name in info.args if name in kw)
    return func(*args, **new_kw)
