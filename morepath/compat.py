# taken from pyramid.compat

import sys

# True if we are running on Python 3.
PY3 = sys.version_info[0] == 3


if PY3:  # pragma: no cover
    text_type = str
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


# the with_meta in python-future doesn't work as it has an inconsistent
# stack frame. the with_meta in newer versions of six has the same issue.
# an older version does the job for us, so copy it in here
# see:
# https://bitbucket.org/gutworth/six/issue/83/with_meta-and-stack-frame-issues
# https://github.com/PythonCharmers/python-future/issues/75
def with_metaclass(meta, *bases):
    """Create a base class with a metaclass."""
    return meta("NewBase", bases, {})
