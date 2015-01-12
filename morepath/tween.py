from .toposort import toposorted


class TweenInfo(object):
    def __init__(self, key, before, after):
        self.key = key
        if before is not None:
            self.before = [before]
        else:
            self.before = []
        if after is not None:
            self.after = [after]
        else:
            self.after = []


class TweenRegistry(object):
    def __init__(self):
        self.clear()

    def register_tween_factory(self, tween_factory, over, under):
        self._tween_infos.append(TweenInfo(tween_factory, over, under))

    def clear(self):
        self._tween_infos = []

    def sorted_tween_factories(self):
        return [info.key for info in toposorted(self._tween_infos)]
