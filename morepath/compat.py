"""
Infrastructure to help make Morepath work with both Python 2 and
Python 3.

It used throughout the code to make Morepath portable
across Python versions.
"""

# taken from pyramid.compat

import sys

PY3 = sys.version_info[0] == 3
"""True if we are running on Python 3"""

# text_type is the type used for non-bytes text
if PY3:
    text_type = str
else:  # pragma: no cover
    text_type = unicode  # noqa

# string_types can be used in isinstance to determine
# whether an object considered to be a string
if PY3:
    string_types = (str,)
else:  # pragma: no cover
    string_types = (basestring,)  # noqa


# XXX we don't want to use this in too many places, as the isinstance
# checks may slow us down like in werkzeug
def bytes_(s, encoding='latin-1', errors='strict'):
    """Encode string if needed

    If ``s`` is an instance of ``text_type``, return
    ``s.encode(encoding, errors)``, otherwise return ``s``
    """
    if isinstance(s, text_type):  # pragma: no cover
        return s.encode(encoding, errors)
    return s  # pragma: no cover
