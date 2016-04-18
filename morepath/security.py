import warnings

warnings.warn("""\
The module morepath.security used to be in the public API of Morepath,
but this usage is deprecated. Import directly from the morepath
namespace instead. For instance:

  from morepath.security import Identity

becomes:

  from morepath import Identity

Note that morepath.security.BasicAuthIdentityPolicy has moved to
an extension package, more.basicauth.
""", DeprecationWarning)

from .authentication import (
    NoIdentity, NO_IDENTITY,
    Identity, IdentityPolicy)  # flake8: noqa
