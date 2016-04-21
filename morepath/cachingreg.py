"""
We define a Reg registry that is used for generic function
configuration that provides a special lookup that caches.

See also :class:`morepath.directive.RegRegistry`.
"""

from reg import CachingKeyLookup, Registry

from .reify import reify

COMPONENT_CACHE_SIZE = 5000
ALL_CACHE_SIZE = 5000
FALLBACK_CACHE_SIZE = 5000


class RegRegistry(Registry):
    """A :class:`reg.Registry` with a cached lookup.

    Morepath uses Reg to implement generic function lookups which
    are used for various aspects of configuration, in particular
    view lookup.

    We cache the lookup using a :class:`reg.CachingKeyLookup` so that
    generic function lookups are faster.
    """
    @reify
    def caching_lookup(self):
        """Cached :class:`reg.Lookup`

        Property is reified with :func:`morepath.reify.reify` so cache
        is shared between :class:`morepath.App` instances that use
        this registry.

        """
        return CachingKeyLookup(
            self,
            COMPONENT_CACHE_SIZE,
            ALL_CACHE_SIZE,
            FALLBACK_CACHE_SIZE).lookup()
