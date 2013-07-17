from comparch import ClassRegistry, CachedLookup, implicit

def initialize():
    registry = ClassRegistry()
    implicit.initialize(CachedLookup(registry))
