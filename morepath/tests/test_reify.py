from morepath import reify

# from pyramid.tests.test_decorator


def test__get__with_inst():
    def wrapped(inst):
        return 'a'
    decorator = reify(wrapped)
    inst = Dummy()
    result = decorator.__get__(inst)
    assert result == 'a'
    assert inst.__dict__['wrapped'] == 'a'


def test__get__noinst():
    decorator = reify(None)
    result = decorator.__get__(None)
    assert result is decorator


def test__doc__copied():
    def wrapped(inst):
        """My doc"""

    decorator = reify(wrapped)
    assert decorator.__doc__ == 'My doc'


def test_no_doc():
    def wrapped(inst):
        pass

    decorator = reify(wrapped)
    assert decorator.__doc__ is None


class Dummy(object):
    pass
