from reg import Predicate, KeyExtractor
from .app import RegRegistry
from .toposort import toposorted, Info


class PredicateInfo(Info):
    def __init__(self, func, name, default, index, before, after):
        super(PredicateInfo, self).__init__(func, before, after)
        self.func = func
        self.name = name
        self.default = default
        self.index = index


class PredicateRegistry(object):
    factory_arguments = {
        'reg_registry': RegRegistry
    }

    def __init__(self, reg_registry):
        self._reg_registry = reg_registry
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

    def install_predicates(self):
        for dispatch in self._predicate_infos.keys():
            if not dispatch.external_predicates:
                continue
            self._reg_registry.register_external_predicates(
                dispatch, self.get_predicates(dispatch))
            self._reg_registry.register_dispatch(dispatch)

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
        return toposorted(predicate_infos)
