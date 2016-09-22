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

from reg import PredicateRegistry, match_class

try:
    from types import ClassType
except ImportError:
    # You're running Python 3!
    ClassType = None
from dectate import DirectiveError


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


class ConverterRegistry(object):
    """A registry for converters.

    Used to decode/encode URL parameters and path variables used
    by the :meth:`morepath.App.path` directive.

    Is aware of inheritance.
    """
    def __init__(self):
        self._registry = PredicateRegistry(match_class('cls'))

    def register_converter(self, type, converter):
        """Register a converter for type.

        :param type: the Python type for which to register
          the converter.
        :param converter: a :class:`morepath.Converter` instance.
        """
        self._registry.register(type, converter)

    def converter_for_type(self, type):
        """Get converter for type.

        Is aware of inheritance; if nothing is registered for given
        type it returns the converter registered for its base class.

        :param type: The type for which to look up the converter.
        :return: a :class:`morepath.Converter` instance.
        """
        result = self._registry.component(type)
        if result is None:
            raise DirectiveError(
                "Cannot find converter for type: %r" % type)
        return result

    def converter_for_value(self, v):
        """Get converter for value.

        Is aware of inheritance; if nothing is registered for type of
        given value it returns the converter registered for its base class.

        :param value: The value for which to look up the converter.
        :return: a :class:`morepath.Converter` instance.
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
        :return: a :class:`Converter` instance.
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
