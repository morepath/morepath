"""The exception classes used by Morepath.

Morepath republishes some configuration related errors from
Dectate:

* :exc:`dectate.ConfigError`

* :exc:`dectate.ConflictError`

* :exc:`dectate.DirectiveReportError`

* :exc:`dectate.DirectiveError`
"""

# -*- coding: utf-8 -*-
import textwrap
from dectate import (ConfigError, ConflictError,  # noqa
                     DirectiveReportError, DirectiveError)  # noqa


# XXX is ConfigError the right base class?
class AutoImportError(ConfigError):
    """Raised when Morepath fails to import a module during
    autoconfig/autosetup.
    """

    def __init__(self, module_name):

        msg = """\
            Morepath wanted to import '{}' during auto-configuration, but
            no such module could be imported.

            Make sure your module name matches the setup.py name, or use
            autoscan directly::

                import autoscan
                import yourmodule
                import morepath

                autoscan.scan(yourmodule)
                morepath.autosetup()

            For more information have a look at the 'configuration' docs.
        """

        msg = textwrap.dedent(msg).format(module_name)
        super(AutoImportError, self).__init__(msg)


class TrajectError(Exception):
    """Raised when path supplied to traject is not allowed.
    """


class LinkError(Exception):
    """Raised when a link cannot be made.
    """


class TopologicalSortError(Exception):
    """Raised if something cannot be sorted topologically.

    This is due to circular dependencies.
    """
