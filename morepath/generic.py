"""These generic functions are by Morepath's implementation (response
generation, link generation, authentication, json load/restore).

The functions are made pluggable by the use of the
:func:`reg.dispatch` and :func:`reg.dispatch_external_predicates`
decorators. Morepath's configuration function uses this to register
implementations using :meth:`reg.Registry.register_function`.

"""
