"""Implementation of routing.

The idea is to turn the routes into a tree, so that the routes::

  a/b
  a/b/c
  a/d

become a tree like this::

  a
    b
    b
      c
    d

Nodes in the tree can have a value attached that can be found through
routing; in Morepath the value is a model instance factory.

When presented with a path, Traject traverses this internal tree.

For a description of a similar algorithm also read: http://littledev.nl/?p=99

.. testsetup::

  from morepath.traject import *

"""

import re
from functools import total_ordering
from reg import arginfo
from webob.exc import HTTPBadRequest

from .converter import IDENTITY_CONVERTER
from .error import TrajectError


IDENTIFIER = re.compile(r'^[^\d\W]\w*$')
"""regex for a valid variable name in a route.

same rule as for Python identifiers.
"""

PATH_VARIABLE = re.compile(r'\{([^}]*)\}')
"""regex to find curly-brace marked variables ``{foo}`` in routes.
"""


@total_ordering
class Step(object):
    """A single step in the tree.

    :param s: the path segment, such as ``'foo'`` or ``'{variable}'`` or
      ``'foo{variable}bar'``.
    :param converters: dict of converters for variables.
    """
    def __init__(self, s, converters=None):
        self.s = s
        self.converters = converters or {}
        self.generalized = generalize_variables(s)
        self.parts = tuple(self.generalized.split('{}'))
        self.names = parse_variables(s)
        if len(set(self.names)) != len(self.names):
            raise TrajectError("Duplicate variable")
        self._variables_re = create_variables_re(s)
        self.cmp_converters = [
            self.converters.get(name, IDENTITY_CONVERTER)
            for name in self.names]
        self.validate()
        self.named_interpolation_str = interpolation_str(s) % tuple(
            [('%(' + name + ')s') for name in self.names])

    def validate(self):
        """Validate whether step makes sense.

        Raises :class:`morepath.error.TrajectError` if there is a problem
        with the segment.
        """
        self.validate_parts()
        self.validate_variables()

    def validate_parts(self):
        """Check whether all non-variable parts of the segment are valid.

        Raises :class:`morepath.error.TrajectError` if there is a problem
        with the segment.
        """
        # XXX should also check for valid URL characters
        for part in self.parts:
            if '{' in part or '}' in part:
                raise TrajectError("invalid step: %s" % self.s)

    def validate_variables(self):
        """Check whether all variables of the segment are valid.

        Raises :class:`morepath.error.TrajectError` if there is a problem
        with the variables.
        """
        parts = self.parts
        if parts[0] == '':
            parts = parts[1:]
        if parts[-1] == '':
            parts = parts[:-1]
        for part in parts:
            if part == '':
                raise TrajectError(
                    "illegal consecutive variables: %s" % self.s)

    def discriminator_info(self):
        """Information needed to construct path discriminator.
        """
        return self.generalized

    def has_variables(self):
        """True if there are any variables in this step.
        """
        return bool(self.names)

    def match(self, s, variables):
        """Match this step with actual path segment.

        :param s: path segment to match with
        :param variables: variables dictionary to update with new converted
          variables that are found in this segment.
        :return: bool. The bool indicates whether ``s`` matched with
          the step or not.
        """
        matched = self._variables_re.match(s)
        if matched is None:
            return False
        get_converter = self.converters.get
        for name, value in matched.groupdict().items():
            converter = get_converter(name, IDENTITY_CONVERTER)
            try:
                variables[name] = converter.decode([value])
            except ValueError:
                return False
        return True

    def __eq__(self, other):
        """True if this step is the same as another.
        """
        if self.s != other.s:
            return False
        return self.cmp_converters == other.cmp_converters

    def __ne__(self, other):
        """True if this step is not equal to another.
        """
        if self.s != other.s:
            return True
        return self.cmp_converters != other.cmp_converters

    def __lt__(self, other):
        """Used for inserting steps in correct place in the tree.

        The order in which a step is inserted into the tree compared
        to its siblings affects which step preferentially matches first.

        In Traject, steps that contain no variables match before steps
        that do contain variables. Steps with more specific variables
        sort before steps with more general ones, i.e. ``prefix{foo}`` sorts
        before ``{foo}`` as ``prefix{foo}`` is more specific.
        """
        # if we have the same non-variable parts, we sort after the other
        # but this should generally be a conflict
        if self.parts == other.parts:
            return False
        # if we can absorb the other's variables we sort after it,
        # we'd have less hardcoded and more variables
        if self._variables_re.match(other.s) is not None:
            return False
        # we sort before other if other's variables can absorb us,
        # this means we have less variables and more hardcoded.
        if other._variables_re.match(self.s) is not None:
            return True
        # sort by non-variable parts alphabetically
        return self.parts > other.parts


class Node(object):
    """A node in the traject tree.
    """
    def __init__(self):
        self._name_nodes = {}
        self._variable_nodes = []
        self.absorb = False
        self.create = lambda variables, request: None

    def add(self, step):
        """Add a step into the tree as a child node of this node.
        """
        if not step.has_variables():
            return self.add_name_node(step)
        return self.add_variable_node(step)

    def add_name_node(self, step):
        """Add a step into the tree as a node that doesn't match variables.
        """
        node = self._name_nodes.get(step.s)
        if node is not None:
            return node
        node = StepNode(step)
        self._name_nodes[step.s] = node
        return node

    def add_variable_node(self, step):
        """Add a step into the tree as a node that matches variables.
        """
        for i, node in enumerate(self._variable_nodes):
            if node.step == step:
                return node
            if node.step.generalized == step.generalized:
                raise TrajectError("step %s and %s are in conflict" %
                                   (node.step.s, step.s))
            if step > node.step:
                continue
            result = StepNode(step)
            self._variable_nodes.insert(i, result)
            return result
        result = StepNode(step)
        self._variable_nodes.append(result)
        return result

    def resolve(self, segment, variables):
        """Match a path segment, traversing this node.

        Matches non-variable nodes before nodes with variables in them.

        Updates the ``variables`` argument.

        :segment: a path segment
        :variables: variables dictionary to update.
        :return: matched node, or ``None`` if node didn't match.
        """
        node = self._name_nodes.get(segment)
        if node is not None:
            return node
        for node in self._variable_nodes:
            matched = node.match(segment, variables)
            if matched:
                return node
        return None


class StepNode(Node):
    """A node that is also a step in that it can match.

    :param step: the step
    """
    def __init__(self, step):
        super(StepNode, self).__init__()
        self.step = step

    def match(self, segment, variables):
        """Match a segment with the step.
        """
        return self.step.match(segment, variables)


class Path(object):
    """Helper when registering paths.

    Used by :meth:`morepath.App.path` to register inverse paths used for
    link generation.

    Also used by :meth:`morepath.App.path` for creating discriminators.

    :param path: the route.
    """
    def __init__(self, path):
        self.steps = [Step(segment) for segment in parse_path(path)]

    def discriminator(self):
        """Creates a unique discriminator for the path.
        """
        return '/'.join([step.discriminator_info() for step in self.steps])

    def interpolation_str(self):
        """Create a string for interpolating variables.

        Used for link generation (inverse).
        """
        return '/'.join([step.named_interpolation_str for step in self.steps])

    def variables(self):
        """Get the variables used by the path.

        :return: a list of variable names
        """
        result = []
        for step in self.steps:
            result.extend(step.names)
        return set(result)


class TrajectRegistry(object):
    """Tree of route steps.
    """
    def __init__(self):
        self._root = Node()

    def add_pattern(self, path, model_factory, defaults=None,
                    converters=None, absorb=False, required=None,
                    extra=None):
        """Add a route to the tree.

        :path: route to add.
        :model_factory: the factory used to construct the model instance
        :defaults: mapping of URL parameters to default value for parameter
        :converters: converters to store with the end step of the route
        :absorb: does this path absorb all segments
        :required: list or set of required URL parameters
        :extra: bool indicating whether extra parameters are expected
        """
        node = self._root
        known_variables = set()
        for segment in parse_path(path):
            step = Step(segment, converters)
            node = node.add(step)
            variables = set(step.names)
            if known_variables.intersection(variables):
                raise TrajectError("Duplicate variables")
            known_variables.update(variables)
        if defaults or converters or required or extra:
            parameter_factory = ParameterFactory(
                defaults, converters, required, extra)
        else:
            parameter_factory = _simple_parameter_factory

        model_args = set(arginfo(model_factory).args)
        wants_request = 'request' in model_args
        wants_app = 'app' in model_args

        def create(path_variables, request):
            variables = parameter_factory(request)
            if wants_request:
                variables['request'] = request
            if wants_app:
                variables['app'] = request.app
            variables.update(path_variables)
            return model_factory(**variables)

        node.create = create
        node.absorb = absorb

    def consume(self, request):
        """Consume a stack given route, returning object.

        Removes the successfully consumed path segments from
        :attr:`morepath.Request.unconsumed`.

        Extracts variables from the path and URL parameters from the request.

        Then constructs the model instance given this information.
        (or :class:`morepath.App` instance in case of mounted apps).

        :param request: the request to consume segments from and to
          retrieve URL parameters from.
        :return: the model instance that can be found, or ``None`` if
          no model instance exists for this sequence of segments.
        """
        stack = request.unconsumed
        node = self._root
        variables = {}
        segment = None
        while stack:
            if node.absorb:
                variables['absorb'] = '/'.join(reversed(stack))
                request.unconsumed = []
                return node.create(variables, request)
            segment = stack.pop()
            # special view prefix
            if segment.startswith('+'):
                stack.append(segment)
                return node.create(variables, request)
            new_node = node.resolve(segment, variables)
            # could still be a view without prefix,
            # or going into a mounted app
            if new_node is None:
                stack.append(segment)
                return node.create(variables, request)
            node = new_node
        if node.absorb:
            variables['absorb'] = ''
        return node.create(variables, request)


class ParameterFactory(object):
    """Convert URL parameters.

    Given expected URL parameters, converters for them and required
    parameters, create a dictionary of converted URL parameters with
    Python values.

    :param parameters: dictionary of parameter names -> default values.
    :param converters: dictionary of parameter names -> converters.
    :param required: dictionary of parameter names -> required booleans.
    :param extra: should extra unknown parameters be included?
    """
    def __init__(self, parameters, converters, required, extra=False):
        self.parameters = parameters
        self.converters = converters
        self.required = required
        self.extra = extra

    def __call__(self, request):
        """Convert URL parameters to Python dictionary with values.
        """
        result = {}
        # it's possible we are not actually interested in parameters
        # but this parameter factory is used as we defined converters
        if not self.parameters:
            return result
        url_parameters = request.GET
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


def _simple_parameter_factory(request):
    return {}


def create_path(segments):
    """Builds a path from a list of segments.

    :param stack: a list of segments
    :return: a path
    """
    return '/' + '/'.join(segments)


def parse_path(path):
    """Parses path, creates normalized segment list.

    Dots are collapsed:

        >>> parse_path('../static//../app.py')
        ['app.py']

    :param path: path string to parse
    :return: normalized list of path segments.
    """
    segments = path.split('/')
    result = []
    for segment in segments:
        if not segment or segment == '.':
            continue
        if segment == '..':
            try:
                result.pop()
            except IndexError:
                pass
        else:
            result.append(segment)
    return result


def normalize_path(path):
    """Converts path into normalized path.

    Rules:

    * Collapse dots:

        >>> normalize_path('/../blog')
        '/blog'

    * Ensure absolute paths:

        >>> normalize_path('./site')
        '/site'

    * Remove double-slashes:

        >>> normalize_path('//index')
        '/index'

    For example:

        >>> normalize_path('../static//../app.py')
        '/app.py'

    :param path: path string to parse
    :return: normalized path.
    """
    return create_path(parse_path(path))


def is_identifier(s):
    """Check whether a variable name is a proper identifier.

    :param s: variable
    :return: True if variable is an identifier.
    """
    return IDENTIFIER.match(s) is not None


def parse_variables(s):
    """Parse variables out of a segment.

    Raised a :class:`morepath.error.TrajectError`` if a variable
    is not a valid identifier.

    :param s: a path segment
    :return: a list of variables.
    """
    result = PATH_VARIABLE.findall(s)
    for name in result:
        if not is_identifier(name):
            raise TrajectError(
                "illegal variable identifier: %s" % name)
    return result


def create_variables_re(s):
    """Create regular expression that matches variables from route segment.

    :param s: a route segment with variables in it.
    :return: a regular expression that matches with variables for the route.
    """
    def _repl(m):
        return '(?P<%s>.+)' % m.group(0)[1:-1]
    return re.compile('^' + PATH_VARIABLE.sub(_repl, s) + '$')


def generalize_variables(s):
    """Generalize a route segment.

    :param s: a route segment.
    :return: a generalized route where all variables are empty ({}).
    """
    return PATH_VARIABLE.sub('{}', s)


def interpolation_str(s):
    """Create a Python string with interpolation variables for a route segment.

    Given ``a{foo}b``, creates ``a%sb``.
    """
    return PATH_VARIABLE.sub('%s', s)
