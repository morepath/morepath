from morepath.converter import (ConverterRegistry, Converter,
                                IDENTITY_CONVERTER)


def test_converter_registry():
    r = ConverterRegistry()

    c = Converter(int, unicode)
    r.register_converter(int, c)
    assert r.converter_for_type(int) is c
    assert r.converter_for_value(1) is c
    assert r.converter_for_value(None) is IDENTITY_CONVERTER
    assert r.converter_for_value('s') is None


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
    assert r.converter_for_type(Lifeform) is c
    assert r.converter_for_type(Animal) is c
    assert r.converter_for_value(Lifeform('seaweed')) is c
    assert r.converter_for_value(Animal('elephant')) is c
    assert r.converter_for_value(None) is IDENTITY_CONVERTER
    assert r.converter_for_value('s') is None
    assert r.converter_for_type(Lifeform).decode('elephant') is elephant
    assert r.converter_for_type(Lifeform).encode(seaweed) == 'seaweed'


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

    assert one == two
    assert one != three
    assert one != four
    assert one != five
    assert one != six
    assert three != four
    assert four != five
    assert five != six

