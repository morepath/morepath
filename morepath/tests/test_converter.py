from ..converter import (
    ConverterRegistry, Converter, ListConverter, IDENTITY_CONVERTER)
from dectate import DirectiveError
import pytest


def test_converter_registry():
    r = ConverterRegistry()

    c = Converter(int, type(u""))
    r.register_converter(int, c)
    assert r.get_converter(int) is c
    assert r.get_converter(type(1)) is c
    assert r.get_converter(type(None)) is IDENTITY_CONVERTER
    with pytest.raises(DirectiveError):
        r.get_converter(type('s'))


def test_converter_registry_inheritance():
    r = ConverterRegistry()

    class Lifeform(object):
        def __init__(self, name):
            self.name = name

    class Animal(Lifeform):
        pass

    seaweed = Lifeform('seaweed')
    elephant = Animal('elephant')

    lifeforms = {
        'seaweed': seaweed,
        'elephant': elephant,
    }

    def lifeform_decode(s):
        try:
            return lifeforms[s]
        except KeyError:
            raise ValueError

    def lifeform_encode(l):
        return l.name

    c = Converter(lifeform_decode, lifeform_encode)
    r.register_converter(Lifeform, c)
    assert r.get_converter(Lifeform) is c
    assert r.get_converter(Animal) is c
    assert r.get_converter(type(Lifeform('seaweed'))) is c
    assert r.get_converter(type(Animal('elephant'))) is c
    assert r.get_converter(type(None)) is IDENTITY_CONVERTER
    with pytest.raises(DirectiveError):
        assert r.get_converter(type('s')) is None
    assert r.get_converter(Lifeform).decode(['elephant']) is elephant
    assert r.get_converter(Lifeform).encode(seaweed) == ['seaweed']


def test_converter_equality():
    def decode():
        pass

    def encode():
        pass

    def other_encode():
        pass

    def other_decode():
        pass

    one = Converter(decode, encode)
    two = Converter(decode, encode)
    three = Converter(other_decode, other_encode)
    four = Converter(decode, other_encode)
    five = Converter(other_decode, encode)
    six = Converter(decode)

    l0 = ListConverter(one)
    l1 = ListConverter(one)
    l2 = ListConverter(two)
    l3 = ListConverter(three)

    assert one == two
    assert one != three
    assert one != four
    assert one != five
    assert one != six
    assert three != four
    assert four != five
    assert five != six

    assert one != l0
    assert l0 != one
    assert l0 == l1
    assert not l0 != l1
    assert l0 == l2
    assert l1 != l3
    assert not l1 == l3
