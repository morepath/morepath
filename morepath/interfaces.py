# -*- coding: utf-8 -*-
from comparch import Interface
from abc import abstractmethod

class IConsumer(Interface):
    """A consumer consumes steps in a stack to find an object.
    """

    @abstractmethod
    def __call__(self, obj, stack):
        """Returns a boolean meaning that some stack has been consumed,
        an object and the rest of unconsumed stack
        """

class IResource(Interface):
    pass

class IResponseFactory(Interface):
    """When called, a Response instance is returned.
    """
    @abstractmethod
    def __call__(self):
        """Returns a Response instance."""

# XXX complete
class ITraject(Interface):
    pass

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
