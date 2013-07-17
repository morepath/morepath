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

class ResolveError(Exception):
    pass

class ModelError(ResolveError):
    """Exception raised when a model cannot be resolved
    """

class ResourceError(ResolveError):
    """Exception raised when a resource cannot be resolved
    """
