"""
Infrastructure to help make Morepath work with both Python 2 and
Python 3.

It used throughout the code to make Morepath portable
across Python versions.
"""

# originally taken from pyramid.compat

import sys

PY3 = sys.version_info[0] == 3
"""True if we are running on Python 3"""

# text_type is the type used for non-bytes text
try:
    text_type = unicode
except NameError:
    text_type = str

# string_types can be used in isinstance to determine
# whether an object considered to be a string
try:
    string_types = (basestring,)
except NameError:
    string_types = (str,)


# XXX we don't want to use this in too many places, as the isinstance
# checks may slow us down like in werkzeug
def bytes_(s, encoding='latin-1', errors='strict'):
    """Encode string if needed

    If ``s`` is an instance of ``text_type``, return
    ``s.encode(encoding, errors)``, otherwise return ``s``
    """
    if isinstance(s, text_type):
        return s.encode(encoding, errors)
    return s


# From Benjamin Peterson's six library
def with_metaclass(meta, *bases):
    """Create a base class with a metaclass."""
    # This requires a bit of explanation: the basic idea is to make a
    # dummy metaclass for one level of class instantiation that replaces
    # itself with the actual metaclass.
    class metaclass(type):
        def __new__(cls, name, this_bases, attrs):
            return meta(name, bases, attrs)
    return type.__new__(metaclass, 'temporary_class', (), {})
