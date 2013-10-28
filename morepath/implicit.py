from reg import ClassRegistry, CachingClassLookup, Lookup, implicit


def initialize():
    registry = ClassRegistry()
    implicit.initialize(Lookup(CachingClassLookup(registry)))
