from reg import Predicate, KeyExtractor
from .toposort import topological_sort


class PredicateInfo(object):
    def __init__(self, func, index, default, before, after):
        self.func = func
        self.index = index
        self.default = default
        self.before = before
        self.after = after
        self.depends = []


class PredicateRegistry(object):
    def __init__(self):
        self.clear()

    def clear(self):
        self._predicate_infos = {}

    def register_predicate(self, func, dispatch, index, default,
                           before, after):
        self._predicate_infos.setdefault(dispatch, []).append(PredicateInfo(
            func, index, default, before, after))

    def get_predicates(self, dispatch):
        infos = self.sorted_predicate_infos(dispatch)
        return [Predicate(info.index, KeyExtractor(info.func)) for
                info in infos]

    def sorted_predicate_infos(self, dispatch):
        func_to_info = {}
        for info in self._predicate_infos[dispatch]:
            func_to_info[info.func] = info
        for info in self._predicate_infos[dispatch]:
            if info.after is not None:
                after_info = func_to_info[info.after]
                info.depends.append(after_info)
            if info.before is not None:
                before_info = func_to_info[info.before]
                before_info.depends.append(info)
        return topological_sort(
            self._predicate_infos[dispatch],
            lambda info: info.depends)
