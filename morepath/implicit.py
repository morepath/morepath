from reg import ClassRegistry, CachedLookup, implicit


def initialize():
    registry = ClassRegistry()
    implicit.initialize(CachedLookup(registry))
