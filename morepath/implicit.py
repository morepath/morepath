"""Track whether we want implicit lookup behavior.

You can control this behavior from here.
:func:`morepath.enable_implicit` and :func:`morepath.disable_implicit`
are exported to the public API.
"""

from reg import implicit

_implicit_enabled = True


def set_implicit(lookup):
    """Set the implicit :class:`reg.Lookup` to use for generic dispatch.

    :lookup: :class:`reg.Lookup` instance.
    """
    if _implicit_enabled:
        implicit.lookup = lookup


def enable_implicit():
    """Enable implicit Reg lookups.

    By default this is turned on. This means Morepath does not require
    a ``lookup`` argument when you use generic functions such as
    :func:`morepath.settings`. This lookup argument is implicitly
    determined from the application that is mounted.
    """
    global _implicit_enabled
    _implicit_enabled = True


def disable_implicit():
    """Disable implicit Reg lookups.

    The Morepath core itself does not rely on any implicit behavior,
    and it is therefore disabled for many of the tests.

    How to disable implicit lookups for all tests in a module::

       def setup_module(module):
           morepath.disable_implicit()
    """
    global _implicit_enabled
    _implicit_enabled = False
