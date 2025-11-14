# flake8: noqa
"""This is the main public API of Morepath.

Additional public APIs can be imported from the :mod:`morepath.error`
and :mod:`morepath.pdbsupport` modules. For custom directive
implementations that interact with core directives for grouping or
subclassing purposes, or that need to use one of the Morepath
registries, you may need to import from :mod:`morepath.directive`.

The other submodules are considered private. If you find yourself
needing to import from them in application or extension code, please
report an issue about it on the Morepath issue tracker.
"""

from dectate import commit

from .app import App, dispatch_method
from .authentication import NO_IDENTITY, Identity, IdentityPolicy
from .autosetup import autoscan, scan
from .converter import Converter
from .core import excview_tween_factory as EXCVIEW
from .core import (
    model_predicate,
    name_predicate,
)
from .core import (
    poisoned_host_header_protection_tween_factory as HOST_HEADER_PROTECTION,
)
from .core import request_method_predicate
from .core import request_method_predicate as LAST_VIEW_PREDICATE
from .reify import reify
from .request import Request, Response
from .run import run
from .view import redirect, render_html, render_json
