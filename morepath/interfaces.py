# -*- coding: utf-8 -*-

# class IConsumer(Interface):
#     """A consumer consumes steps in a stack to find an object.
#     """

#     @abstractmethod
#     def __call__(self, obj, stack, lookup):
#         """Returns a boolean meaning that some stack has been consumed,
#         an object and the rest of unconsumed stack
#         """


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
