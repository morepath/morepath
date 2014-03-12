from reg.mapping import Map, ClassMapKey


class Converter(object):
    """How to decode from strings to objects and back.

    Only used for decoding for a list with a single value, will
    error if more or less than one value is entered.

    Used for decoding/encoding URL parameters and path parameters.
    """
    def __init__(self, decode, encode=None):
        """Create new converter.

        :param decode: function that given string can decode them into objects.
        :param encode: function that given objects can encode them into
            strings.
        """
        self.single_decode = decode
        self.single_encode = encode or unicode

    def decode(self, strings):
        if len(strings) != 1:
            raise ValueError
        return self.single_decode(strings[0])

    def encode(self, value):
        return [self.single_encode(value)]

    def is_missing(self, value):
        # a single value is missing if the list is empty
        return value == []

    def __eq__(self, other):
        if not isinstance(other, Converter):
            return False
        return (self.single_decode is other.single_decode and
                self.single_encode is other.single_encode)

    def __ne__(self, other):
        return not self == other


class ListConverter(object):
    """How to decode from list of strings to list of objects and back.

    Used for decoding/encoding URL parameters and path parameters.
    """
    def __init__(self, converter):
        """Create new converter.

        :param converter: the converter to use for list entries.
        """
        self.converter = converter

    def decode(self, strings):
        decode = self.converter.single_decode
        return [decode(s) for s in strings]

    def encode(self, values):
        encode = self.converter.single_encode
        return [encode(v) for v in values]

    def is_missing(self, value):
        # a list value is never missing, even if the list is empty
        return False

    def __eq__(self, other):
        if not isinstance(other, ListConverter):
            return False
        return self.converter == other.converter

    def __ne__(self, other):
        return not self == other


IDENTITY_CONVERTER = Converter(lambda s: s, lambda s: s)


class ConverterRegistry(object):
    """A registry for converters.

    Used to decode/encode URL parameters and path variables used
    by the :meth:`morepath.AppBase.path` directive.

    Is aware of inheritance.
    """
    def __init__(self):
        self._map = Map()

    def register_converter(self, type, converter):
        """Register a converter for type.

        :param type: the Python type for which to register
          the converter.
        :param converter: a :class:`morepath.Converter` instance.
        """
        self._map[ClassMapKey(type)] = converter

    def converter_for_type(self, type):
        """Get converter for type.

        Is aware of inheritance; if nothing is registered for given
        type it returns the converter registered for its base class.

        :param type: The type for which to look up the converter.
        :returns: a :class:`morepath.Converter` instance.
        """
        return self._map.get(ClassMapKey(type))

    def converter_for_value(self, v):
        """Get converter for value.

        Is aware of inheritance; if nothing is registered for type of
        given value it returns the converter registered for its base class.

        :param value: The value for which to look up the converter.
        :returns: a :class:`morepath.Converter` instance.
        """
        if v is None:
            return IDENTITY_CONVERTER
        return self.converter_for_type(type(v))
