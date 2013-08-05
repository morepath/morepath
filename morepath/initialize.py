from .registry import Registry
from .traject import traject_consumer
from .interfaces import IConsumer

global_registry = Registry()

# XXX should be done inside a function
global_registry.register(IConsumer, (object,), traject_consumer)
