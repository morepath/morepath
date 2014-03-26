from reg.mapping import Map, ClassMapKey
from types import ClassType
from morepath.error import DirectiveError
from webob.exc import HTTPBadRequest


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

    def get_converters(self, arguments, converters):
        """Get converters for arguments.
        Use explicitly supplied converter if available, otherwise ask
        for converter for the default value of argument.

        :param arguments: a dictionary of arguments to find converters for.
        :param converters: a dictionary of explicitly supplied converters.
        :returns: a dictionary with for each argument a converter supplied.
        """
        result = {}

        def get_converter(converter):
            if type(converter) in [type, ClassType]:
                result = self.converter_for_type(converter)
                if result is None:
                    raise DirectiveError(
                        "Cannot find converter for type: %r" % converter)
                return result
            return converter

        for name, value in arguments.items():
            # find explicit converter
            converter = converters.get(name, None)
            # if explicit converter is type, look it up
            if isinstance(converter, list):
                if len(converter) == 0:
                    c = IDENTITY_CONVERTER
                else:
                    c = get_converter(converter[0])
                converter = ListConverter(c)
            else:
                converter = get_converter(converter)
            # if still no converter, look it up for value
            if converter is None:
                converter = self.converter_for_value(value)
            if converter is None:
                raise DirectiveError(
                    "Cannot find converter for default value: %r (%s)" %
                    (value, type(value)))
            result[name] = converter
        return result


class ParameterFactory(object):
    """Convert URL parameters.

    Given expected URL parameters, converters for them and required
    parameters, create a dictionary of converted URL parameters.
    """
    def __init__(self, parameters, converters, required, extra=False):
        """
        :param parameters: dictionary of parameter names -> default values.
        :param converters: dictionary of parameter names -> converters.
        :param required: dictionary of parameter names -> required booleans.
        :param extra: should extra unknown parameters be processed?
        """
        self.parameters = parameters
        self.converters = converters
        self.required = required
        self.extra = extra

    def __call__(self, url_parameters):
        """Convert URL parameters to program-friendly structure.
        """
        result = {}
        for name, default in self.parameters.items():
            value = url_parameters.getall(name)
            converter = self.converters.get(name, IDENTITY_CONVERTER)
            if converter.is_missing(value):
                if name in self.required:
                    raise HTTPBadRequest(
                        "Required URL parameter missing: %s" %
                        name)
                result[name] = default
                continue
            try:
                result[name] = converter.decode(value)
            except ValueError:
                raise HTTPBadRequest(
                    "Cannot decode URL parameter %s: %s" % (
                        name, value))

        if not self.extra:
            return result, None

        remaining = set(url_parameters.keys()).difference(
            set(result.keys()))
        extra = {}
        for name in remaining:
            value = url_parameters.getall(name)
            converter = IDENTITY_CONVERTER
            try:
                extra[name] = converter.decode(value)
            except ValueError:
                raise HTTPBadRequest(
                    "Cannot decode URL parameter %s: %s" % (
                        name, value))
        return result, extra
