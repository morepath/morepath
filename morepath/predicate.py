from reg import Predicate, KeyExtractor
from .toposort import topological_sort


class PredicateInfo(object):
    def __init__(self, func, name, default, index, before, after):
        self.func = func
        self.name = name
        self.default = default
        self.index = index
        self.before = before
        self.after = after


class PredicateRegistry(object):
    def __init__(self):
        self.clear()

    def clear(self):
        self._predicate_infos = {}
        self._predicate_fallbacks = {}

    def register_predicate(self, func, dispatch, name, default, index,
                           before, after):
        self._predicate_infos.setdefault(
            dispatch, []).append(PredicateInfo(
                func, name, default, index, before, after))

    def register_predicate_fallback(self, dispatch, func, fallback_func):
        self._predicate_fallbacks.setdefault(
            dispatch, {})[func] = fallback_func

    def install_predicates(self, dispatch):
        if not dispatch.external_predicates:
            return
        self.register_external_predicates(
            dispatch,
            self.get_predicates(dispatch))

    def get_predicates(self, dispatch):
        infos = self.sorted_predicate_infos(dispatch)
        result = []
        for info in infos:
            fallback = self._predicate_fallbacks.get(dispatch, {}).get(
                info.func)
            predicate = Predicate(info.name, info.index,
                                  KeyExtractor(info.func),
                                  fallback=fallback,
                                  default=info.default)
            result.append(predicate)
        return result

    def sorted_predicate_infos(self, dispatch):
        predicate_infos = self._predicate_infos.get(dispatch)
        if predicate_infos is None:
            return []
        func_to_info = {}
        depends = {}
        for info in predicate_infos:
            func_to_info[info.func] = info
            depends[info.func] = []
        for info in predicate_infos:
            if info.after is not None:
                after_info = func_to_info[info.after]
                depends[info.func].append(after_info)
            if info.before is not None:
                before_info = func_to_info[info.before]
                depends[before_info.func].append(info)
        return topological_sort(
            predicate_infos, lambda info: depends[info.func])
