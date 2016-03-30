from .toposort import toposorted, Info


class TweenRegistry(object):
    def __init__(self):
        self._tween_infos = []

    def register_tween_factory(self, tween_factory, over, under):
        self._tween_infos.append(Info(tween_factory, over, under))

    def sorted_tween_factories(self):
        return [info.key for info in toposorted(self._tween_infos)]
