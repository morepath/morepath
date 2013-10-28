# -*- coding: utf-8 -*-
from abc import ABCMeta, abstractmethod

class Interface(object):
    __meta__ = ABCMeta


# class IConsumer(Interface):
#     """A consumer consumes steps in a stack to find an object.
#     """

#     @abstractmethod
#     def __call__(self, obj, stack, lookup):
#         """Returns a boolean meaning that some stack has been consumed,
#         an object and the rest of unconsumed stack
#         """


class IRoot(Interface):
    """Mark this object as the root.
    """

class IApp(Interface):
    """An application."""
    # XXX fill in details


class IConfigAction(Interface):
    """A configuration item.
    """

    @abstractmethod
    def discriminator(self):
        """Returns an immutable that uniquely identifies this config.

        Used for configuration conflict detection.
        """

    @abstractmethod
    def prepare(self, obj):
        """Prepare action for configuration.

        obj - the object being registered
        """

    @abstractmethod
    def perform(self, obj):
        """Register whatever is being configured.

        obj - the object being registered
        """


class ConfigError(Exception):
    """Raised when configuration is bad
    """


class ResolveError(Exception):
    """Raised when path cannot be resolved
    """


class ModelError(ResolveError):
    """Raised when a model cannot be resolved
    """


class ResourceError(ResolveError):
    """Raised when a resource cannot be resolved
    """


class TrajectError(Exception):
    """Raised when path supplied to traject is not allowed.
    """


class LinkError(Exception):
    """Raised when a link cannot be made.
    """
