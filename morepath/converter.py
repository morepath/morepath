"""Convert path variables and URL parameters to Python objects.

This module contains functionality that can convert traject and URL
parameters (``?foo=3``) into Python values (ints, date, etc) that are
passed into model factories that are configured using the
:meth:`morepath.App.path` and :meth:`morepath.App.mount`
directives. The inverse conversion back from Python value to string
also needs to be provided to support link generation.

:class:`morepath.Converter` is exported to the public API.

See also :class:`morepath.directive.ConverterRegistry`
"""

import reg
from dectate import DirectiveError

try:
    from types import ClassType
except ImportError:
    # You're running Python 3!
    ClassType = type
class_types = tuple({type, ClassType})


class Converter(object):
    """Decode from strings to objects and back.

    Used internally by the :meth:`morepath.App.converter` directive.

    Only used for decoding for a list with a single value, will
    error if more or less than one value is entered.

    Used for decoding/encoding URL parameters and path parameters.
    """

    # must be set explicitly because __eq__ is defined below.
    # see https://docs.python.org/3.1/reference/datamodel.html#object.__hash__
    __hash__ = object.__hash__

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
        """Decode list of strings into Python value.

        String must have only a single entry.

        :param strings: list of strings.
        :return: Python value
        """
        if len(strings) != 1:
            raise ValueError
        return self.single_decode(strings[0])

    def encode(self, value):
        """Encode Python value into list of strings.

        :param value: Python value
        :return: List of strings with only a single entry
        """
        return [self.single_encode(value)]

    def is_missing(self, value):
        """True is a given value is the missing value.
        """
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

    Used :class:`morepath.converter.ConverterRegistry` to handle
    lists of repeated names in parameters.

    Used for decoding/encoding URL parameters and path variables.
    """
    def __init__(self, converter):
        """Create new converter.

        :param converter: the converter to use for list entries
        """
        self.converter = converter

    def decode(self, strings):
        """Decode list of strings into list of Python values.

        :param strings: list of strings
        :return: list of Python values
        """
        decode = self.converter.single_decode
        return [decode(s) for s in strings]

    def encode(self, values):
        """Encode list of Python values into list of strings

        :param values: list of Python values.
        :return: List of strings.
        """
        encode = self.converter.single_encode
        return [encode(v) for v in values]

    def is_missing(self, value):
        """True is a given value is the missing value.
        """
        # a list value is never missing, even if the list is empty
        return False

    def __eq__(self, other):
        if not isinstance(other, ListConverter):
            return False
        return self.converter == other.converter

    def __ne__(self, other):
        return not self == other


IDENTITY_CONVERTER = Converter(lambda s: s, lambda s: s)
"""Converter that has no effect.

String becomes string.
"""


def get_converter(type):
    """Get the converter for a given type.

    :param type: a class or type.
    :return: a :class:`morepath.Converter` instance.
    """
    raise DirectiveError(
        "Cannot find converter for type: %r" % type)


class ConverterRegistry(object):
    """A registry for converters.

    Used to decode/encode URL parameters and path variables used
    by the :meth:`morepath.App.path` directive.

    Is aware of inheritance.
    """
    def __init__(self):
        self.get_converter = reg.dispatch(
            reg.match_class('type'),
            get_key_lookup=reg.DictCachingKeyLookup)(get_converter)
        self.register_converter(type(None), IDENTITY_CONVERTER)

    def register_converter(self, type, converter):
        """Register a converter for type.

        :param type: the Python type for which to register
          the converter.
        :param converter: a :class:`morepath.Converter` instance.
        """
        self.get_converter.register(type=type)(lambda type: converter)

    def actual_converter(self, spec):
        """Return an actual converter for a given spec.

        :param spec: if a type, return the registered converter for
          that; if a list use its first element as a spec for a
          converter; else, assume it is a converter and return it.
        :return: a :class:`morepath.Converter` instance.
        """
        if isinstance(spec, list):
            if len(spec) == 0:
                spec = IDENTITY_CONVERTER
            else:
                spec = self.actual_converter(spec[0])
            return ListConverter(spec)
        if isinstance(spec, class_types):
            return self.get_converter(spec)
        return spec

    def argument_and_explicit_converters(self, arguments, converters):
        """Use explict converters unless none supplied, then use default args.
        """
        result = {name: self.get_converter(type(value))
                  for name, value in arguments.items()}
        for name, conv in converters.items():
            result[name] = self.actual_converter(conv)
        return result
