from morepath import compat


def test_text_type():
    assert isinstance(u'foo', compat.text_type)
    assert not isinstance(b'foo', compat.text_type)


def test_string_types():
    assert isinstance('foo', compat.string_types)
    assert isinstance(u'foo', compat.string_types)
    if compat.PY3:
        assert not isinstance(b'foo', compat.string_types)
    else:
        assert isinstance(b'foo', compat.string_types)


def test_bytes_():
    text = u'Z\N{latin small letter u with diaeresis}rich'
    code = compat.bytes_(text)
    assert isinstance(code, bytes)
    assert code == compat.bytes_(code)


def test_withclass():
    class Meta(type):
        pass

    class Class(compat.with_metaclass(Meta)):
        pass

    assert type(Class) == Meta
    assert Class.__bases__ == (object,)
