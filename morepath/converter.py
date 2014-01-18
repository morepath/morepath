from reg.mapping import Map, ClassMapKey


class Converter(object):
    """A converter that knows how to decode from string to object and back.

    Used for decoding/encoding URL parameters and path parameters.
    """
    def __init__(self, decode, encode=None):
        """Create new converter.

        :param decode: function that given string can decode it into object.
        :param encode: function that given object can encode it into object.
        """
        self.decode = decode
        self.encode = encode or unicode

    def __eq__(self, other):
        return (self.decode is other.decode and
                self.encode is other.encode)

    def __ne__(self, other):
        return not self == other


IDENTITY_CONVERTER = Converter(lambda s: s, lambda s: s)


class ConverterRegistry(object):
    """A registry for converters.

    Used to decode/encode URL parameters and path variables used
    by the :meth:`morepath.AppBase.model` directive.

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
        type will return converter registered for base class.

        :param type: The type for which to look up the converter.
        :returns: a :class:`morepath.Converter` instance.
        """
        return self._map.get(ClassMapKey(type))

    def converter_for_value(self, v):
        """Get converter for value.

        Is aware of inheritance; if nothing is registered for type of
        given value will return converter registered for base class.

        :param value: The value for which to look up the converter.
        :returns: a :class:`morepath.Converter` instance.
        """
        if v is None:
            return IDENTITY_CONVERTER
        return self.converter_for_type(type(v))
