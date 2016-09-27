"""
Tweens are lightweight middleware using webob.

A tween is a function that takes a :class:`morepath.Request` and returns
a :class:`morepath.Response`. A tween factory is a function that given
an application instance and tween constructs another tween that wraps it.

Used by :meth:`morepath.App.tween_factory`.

See also :class:`morepath.directive.TweenRegistry`
"""
from .toposort import toposorted, Info


class TweenRegistry(object):
    """Registry for tweens.
    """
    def __init__(self):
        self._tween_infos = []

    def register_tween_factory(self, tween_factory, over, under):
        """Register a tween factory.

        :param tween_factory: a function that constructs a tween given
          a :class:`morepath.App` instance and a function that takes a
          :class:`morepath.Request` argument and returns a
          :class:`morepath.Response` (or a :class:`webob.response.Response`).
        :over: this tween factory wraps the tween created by the ``over``
          factory (possibly indirectly).
        :under: the ``under`` factory wraps the tween created by this one
          (possibly indirectly).
        """
        self._tween_infos.append(Info(tween_factory, over, under))

    def sorted_tween_factories(self):
        """Sort tween factories topologically by over and under.

        :return: a sorted list of tween infos.
        """
        return [info.key for info in toposorted(self._tween_infos)]

    def wrap(self, app):
        """Wrap app with tweens.

        This wraps :func:`morepath.publish.publish` with tweens.

        :param app: an instance of :class:`morepath.App`.
        :return: the application wrapped with tweens. This is a function
          that takes request and returns a a response.
        """
        # to avoid circular import import publish here
        from .publish import publish as result
        for tween_factory in reversed(self.sorted_tween_factories()):
            result = tween_factory(app, result)
        return result
