# taken from pyramid.compat

import sys

# True if we are running on Python 3.
PY3 = sys.version_info[0] == 3


if PY3:  # pragma: no cover
    text_type = str  # pragma: nocoverage
else:
    text_type = unicode


# XXX we don't want to use this in too many places, as the isinstance
# checks may slow us down like in werkzeug
def bytes_(s, encoding='latin-1', errors='strict'):
    """ If ``s`` is an instance of ``text_type``, return
    ``s.encode(encoding, errors)``, otherwise return ``s``"""
    if isinstance(s, text_type):  # pragma: no cover
        return s.encode(encoding, errors)
    return s


if PY3:
    string_types = (str,)  # pragma: nocoverage
else:
    string_types = (basestring,)
