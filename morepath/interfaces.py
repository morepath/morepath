# -*- coding: utf-8 -*-
from abc import abstractmethod
from comparch import Interface

class IConsumer(Interface):
    """A consumer consumes steps in a stack to find an object.
    """

    @abstractmethod
    def __call__(self, obj, stack, lookup):
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

# XXX incomplete
class ITraject(Interface):
    pass

class IInverse(Interface):
    """Marker interface to hook in inverse component in a traject."""

class IRoot(Interface):
    """Mark this object as the root.
    """

class ILookup(Interface):
    """Mark this model as an model that can change the lookup.
    """
    
class IApp(Interface):
    """An application."""
    # XXX fill in details
    
class IModelBase(Interface):
    """Mark this object as a base of a model.
    """

class IPath(Interface):
    """Get the path for a model."""

class IConfigItem(Interface):
    """A configuration item.
    """

    @abstractmethod
    def discriminator(self):
        """Returns an immutable that uniquely identifies this config.

        Used for configuration conflict detection.
        """

    @abstractmethod
    def register(self, registry, name, obj):
        """Register whatever is being configured.

        registry - the registry in which to register
        name - the name of the obj in its module
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
    
