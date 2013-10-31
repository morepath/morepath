# -*- coding: utf-8 -*-


class ConfigError(Exception):
    """Raised when configuration is bad
    """


class ResolveError(Exception):
    """Raised when path cannot be resolved
    """


class ModelError(ResolveError):
    """Raised when a model cannot be resolved
    """


class ViewError(ResolveError):
    """Raised when a view cannot be resolved
    """


class TrajectError(Exception):
    """Raised when path supplied to traject is not allowed.
    """


class LinkError(Exception):
    """Raised when a link cannot be made.
    """
