from .toposort import topological_sort


class TweenRegistry(object):
    def __init__(self):
        self._tween_factories = {}

    def register_tween_factory(self, tween_factory, over, under):
        self._tween_factories[tween_factory] = over, under

    def clear(self):
        self._tween_factories = {}

    def sorted_tween_factories(self):
        tween_factory_depends = {}
        for tween_factory, (over, under) in self._tween_factories.items():
            depends = []
            if under is not None:
                depends.append(under)
            tween_factory_depends[tween_factory] = depends
        for tween_factory, (over, under) in self._tween_factories.items():
            if over is not None:
                depends = tween_factory_depends[over]
                depends.append(tween_factory)
        return topological_sort(
            self._tween_factories.keys(),
            lambda tween_factory: tween_factory_depends.get(tween_factory, []))
