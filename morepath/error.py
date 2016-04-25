"""The exception classes used by Morepath.

Morepath republishes some configuration related errors from
Dectate:

* :exc:`dectate.ConfigError`

* :exc:`dectate.ConflictError`

* :exc:`dectate.DirectiveReportError`

* :exc:`dectate.DirectiveError`

* :exc:`dectate.TopologicalSortError`
"""

# -*- coding: utf-8 -*-
import textwrap
from dectate import (ConfigError, ConflictError, TopologicalSortError,  # noqa
                     DirectiveReportError, DirectiveError)  # noqa


# XXX is ConfigError the right base class?
class AutoImportError(ConfigError):
    """Raised when Morepath fails to import a module during autoscan."""

    def __init__(self, module_name):

        msg = """\
            Morepath wanted to import '{}' during auto-configuration, but
            no such module could be imported.

            Make sure your module name matches the setup.py name, or use
            morepath.scan directly::

                import yourmodule
                import morepath

                morepath.scan(yourmodule)

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
