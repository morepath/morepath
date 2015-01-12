from morepath.toposort import toposorted


def test_toposorted_single_before_after():
    class Info(object):
        def __init__(self, key, before=None, after=None):
            self.key = key
            self._before = before
            self._after = after

        def __repr__(self):
            return '<Info %r>' % self.key

        def before(self):
            if self._before is None:
                return []
            return [self._before]

        def after(self):
            if self._after is None:
                return []
            return [self._after]

    a = Info(1)
    b = Info(2, 1)
    c = Info(3, None, 1)

    infos = [a, b, c]

    assert toposorted(infos) == [b, a, c]

    a = Info(1)
    b = Info(2, None, 1)
    c = Info(3, 1, None)

    infos = [a, b, c]
    assert toposorted(infos) == [c, a, b]


def test_toposorted_multi_before_after():
    class Info(object):
        def __init__(self, key, before=None, after=None):
            self.key = key
            self._before = before or []
            self._after = after or []

        def __repr__(self):
            return '<Info %r>' % self.key

        def before(self):
            return self._before

        def after(self):
            return self._after

    a = Info(1)
    b = Info(2, [1])
    c = Info(3, None, [1, 2])

    infos = [a, b, c]

    assert toposorted(infos) == [b, a, c]
