from reg.mapping import Map, ClassMapKey
try:
    from types import ClassType
except ImportError:
    # You're running Python 3!
    ClassType = None
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
        fallback_encode = getattr(__builtins__, "unicode", str)
        self.single_decode = decode
        self.single_encode = encode or fallback_encode

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
        result = self._map.get(ClassMapKey(type))
        if result is None:
            raise DirectiveError(
                "Cannot find converter for type: %r" % type)
        return result

    def converter_for_value(self, v):
        """Get converter for value.

        Is aware of inheritance; if nothing is registered for type of
        given value it returns the converter registered for its base class.

        :param value: The value for which to look up the converter.
        :returns: a :class:`morepath.Converter` instance.
        """
        if v is None:
            return IDENTITY_CONVERTER
        try:
            return self.converter_for_type(type(v))
        except DirectiveError:
            raise DirectiveError(
                "Cannot find converter for default value: %r (%s)" %
                (v, type(v)))

    def converter_for_explicit_or_type(self, c):
        """Given a converter or a type, turn it into an explicit one.
        """
        if type(c) in [type, ClassType]:
            return self.converter_for_type(c)
        return c

    def converter_for_explicit_or_type_or_list(self, c):
        """Given a converter or type or list, turn it into an explicit one.

        :param c: can either be a converter, or a type for which
          a converter can be looked up, or a list with a converter or a type
          in it.
        :returns: a :class:`Converter` instance.
        """
        if isinstance(c, list):
            if len(c) == 0:
                c = IDENTITY_CONVERTER
            else:
                c = self.converter_for_explicit_or_type(c[0])
            return ListConverter(c)
        return self.converter_for_explicit_or_type(c)

    def explicit_converters(self, converters):
        """Given converter dictionary, make everything in it explicit.

        This means types have converters looked up for them, and
        lists are turned into :class:`ListConverter`.
        """
        return {name: self.converter_for_explicit_or_type_or_list(value) for
                name, value in converters.items()}

    def argument_and_explicit_converters(self, arguments, converters):
        """Use explict converters unless none supplied, then use default args.
        """
        result = self.explicit_converters(converters)
        for name, value in arguments.items():
            if name not in result:
                result[name] = self.converter_for_value(value)
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
        :param extra: should extra unknown parameters be included?
        """
        self.parameters = parameters
        self.converters = converters
        self.required = required
        self.extra = extra

    def __call__(self, url_parameters):
        """Convert URL parameters to Python dictionary with values.
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
            return result

        remaining = set(url_parameters.keys()).difference(
            set(result.keys()))
        extra = {}
        for name in remaining:
            value = url_parameters.getall(name)
            converter = self.converters.get(name, IDENTITY_CONVERTER)
            try:
                extra[name] = converter.decode(value)
            except ValueError:
                raise HTTPBadRequest(
                    "Cannot decode URL parameter %s: %s" % (
                        name, value))
        result['extra_parameters'] = extra
        return result
