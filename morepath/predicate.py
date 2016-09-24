"""
The :meth:`morepath.App.predicate` directive lets you install predicates
for function that use :func:`reg.dispatch_method`. This is
used by :mod:`morepath.core` to install the view predicates, and you can
also use it for your own functions.

This implements the functionality that drives Reg to install these
predicates.

See also :class:`morepath.directive.PredicateRegistry`
"""

from reg import Predicate
from .toposort import toposorted, Info
from collections import defaultdict


class PredicateRegistry(object):
    """A registry of what predicates are registered for which functions.

    It also keeps track of how predicates are to be ordered.

    """
    app_class_arg = True

    def __init__(self, app_class):
        self.app_class = app_class
        self._predicate_infos = defaultdict(list)
        self._predicate_fallbacks = defaultdict(dict)

    def register_predicate(self, func, dispatch, name, default, index,
                           before, after):
        """Register a predicate for installation into the reg registry.

        See :meth:`morepath.App.predicate` for details.

        :param func: the function that implements the predicate.
        :param dispatch: the dispatch function to register the predicate on.
        :param name: name of the predicate.
        :param default: default value.
        :param index: index to use.
        :param before: predicate function to have priority over.
        :param after: predicate function that has priority over this one.
        """
        info = PredicateInfo(func, name, default, index, before, after)
        self._predicate_infos[dispatch].append(info)

    def register_predicate_fallback(self, dispatch, func, fallback_func):
        """Register a predicate fallback for installation into reg registry.

        See :meth:`morepath.App.predicate_fallback` for details.

        :param dispatch: the dispatch function to register fallback on.
        :param func: the predicate function to register fallback for.
        :param fallback_func: the fallback function.
        """
        self._predicate_fallbacks[dispatch][func] = fallback_func

    def install_predicates(self):
        """Install the predicates with reg.

        This should be called during configuration once all predicates
        and fallbacks are known. Uses
        :meth:`PredicateRegistry.get_predicates` to get out the
        predicates in the correct order.
        """
        for dispatch in self._predicate_infos.keys():
            getattr(self.app_class, dispatch.__name__).add_predicates(
                self.get_predicates(dispatch))

    def get_predicates(self, dispatch):
        """Create Reg predicates.

        This creates :class:`reg.Predicate` objects for a particular
        dispatch function.

        Uses :meth:`PredicateRegistry.sorted_predicate_infos` to sort
        the predicate infos.

        :param dispatch: the dispatch function to create the predicates for.

        :return: a list of :class:`reg.Predicate` instances in the
          correct order.
        """
        infos = self.sorted_predicate_infos(dispatch)
        result = []
        for info in infos:
            fallback = self._predicate_fallbacks[dispatch].get(info.func)
            predicate = Predicate(info.name, info.index,
                                  adapt(info.func),
                                  fallback=fallback,
                                  default=info.default)
            result.append(predicate)
        return result

    def sorted_predicate_infos(self, dispatch):
        """Topologically sort predicate infos for a dispatch function.

        :param dispatch: the dispatch function to sort for.
        :return: a list of sorted :class:`PredicateInfo` instances.
        """
        return toposorted(self._predicate_infos[dispatch])


def adapt(func):
    def wrapper(d):
        return func(**d)
    return wrapper


class PredicateInfo(Info):
    """Used by :class:`PredicateRegistry` internally.

    Is used to store registration information on a predicate
    before it is registered with Reg.
    """
    def __init__(self, func, name, default, index, before, after):
        super(PredicateInfo, self).__init__(func, before, after)
        self.func = func
        self.name = name
        self.default = default
        self.index = index
