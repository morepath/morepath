from morepath.toposort import toposorted


def test_toposorted_single_before_after():
    class Info(object):
        def __init__(self, key, before=None, after=None):
            self.key = key
            if before is not None:
                self.before = [before]
            else:
                self.before = []
            if after is not None:
                self.after = [after]
            else:
                self.after = []

        def __repr__(self):
            return '<Info %r>' % self.key

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
            self.before = before or []
            self.after = after or []

        def __repr__(self):
            return '<Info %r>' % self.key

    a = Info(1)
    b = Info(2, [1])
    c = Info(3, None, [1, 2])

    infos = [a, b, c]

    assert toposorted(infos) == [b, a, c]
