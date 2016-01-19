from morepath.toposort import Info, toposorted


def test_toposorted_single_before_after():
    a = Info(1, None, None)
    b = Info(2, 1, None)
    c = Info(3, None, 1)

    infos = [a, b, c]

    assert toposorted(infos) == [b, a, c]

    a = Info(1, None, None)
    b = Info(2, None, 1)
    c = Info(3, 1, None)

    infos = [a, b, c]
    assert toposorted(infos) == [c, a, b]


def test_toposorted_multi_before_after():
    a = Info(1, None, None)
    b = Info(2, [1], None)
    c = Info(3, None, [1, 2])

    infos = [a, b, c]

    assert toposorted(infos) == [b, a, c]
