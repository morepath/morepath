# -*- coding: utf-8 -*-

from morepath.pathstack import parse_path, create_path, DEFAULT, VIEW


def test_parse():
    """Parse a path to a stack, default namespaces.
    """
    assert ([(DEFAULT, u'c'),
             (DEFAULT, u'b'),
             (DEFAULT, u'a')] ==
            parse_path(u'/a/b/c'))


def test_multi_slash():
    assert parse_path(u'/a/b/c') == parse_path(u'/a///b//c')
    assert parse_path(u'/a/b/c') == parse_path(u'/a/b/c/')


def test_create():
    assert (u'/a/b/c' ==
            create_path([
                (DEFAULT, u'c'),
                (DEFAULT, u'b'),
                (DEFAULT, u'a')]))


def test_parse_ns():
    """Parse a path to a stack with namespaces.
    """
    assert ([(VIEW, u'c'),
             (DEFAULT, u'b'),
             (DEFAULT, u'a')] ==
            parse_path(u'/a/b/++view++c'))


def test_create_ns():
    assert (u'/a/b/++view++c' ==
            create_path([
                (VIEW, u'c'),
                (DEFAULT, u'b'),
                (DEFAULT, u'a')]))


def test_parse_ns_shortcut():
    assert ([(VIEW, u'c'),
             (DEFAULT, u'b'),
             (DEFAULT, u'a')] ==
            parse_path(u'/a/b/@@c', shortcuts={u'@@': VIEW}))


def test_create_ns_shortcut():
    assert (u'/a/b/@@c' ==
            create_path([
                (VIEW, u'c'),
                (DEFAULT, u'b'),
                (DEFAULT, u'a')], shortcuts={u'@@': VIEW}))


def test_parse_ns_shortcut_not_at_beginning():
    # shortcuts should be at the beginning of a step to be recognized
    assert ([(DEFAULT, u'a@@c'),
             (DEFAULT, u'b'),
             (DEFAULT, u'a')] ==
            parse_path(u'/a/b/a@@c', shortcuts={u'@@': VIEW}))


def test_create_ns_shortcut_not_at_beginning():
    assert (u'/a/b/a@@c' ==
            create_path([
                (DEFAULT, u'a@@c'),
                (DEFAULT, u'b'),
                (DEFAULT, u'a')], shortcuts={u'@@': VIEW}))


def test_parse_ns_weird_no_close():
    # a namespace that opens but doesn't close
    assert (u'/a/b/++c' ==
            create_path([
                (DEFAULT, u'++c'),
                (DEFAULT, u'b'),
                (DEFAULT, u'a')]))


def test_create_ns_weird_no_close():
    assert ([(DEFAULT, u'++c'),
             (DEFAULT, u'b'),
             (DEFAULT, u'a')] ==
            parse_path(u'/a/b/++c'))


def test_parse_ns_weird_no_open():
    # a namespace that closes but doesn't open
    assert ([(DEFAULT, u'view++c'),
             (DEFAULT, u'b'),
             (DEFAULT, u'a')] ==
            parse_path(u'/a/b/view++c'))


def test_create_ns_weird_no_open():
    # a namespace that closes but doesn't open
    assert ([(DEFAULT, u'view++c'),
             (DEFAULT, u'b'),
             (DEFAULT, u'a')] ==
            parse_path(u'/a/b/view++c'))

# XXX removing /./ from paths and checking for ../
