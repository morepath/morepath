import posixpath
import re
from functools import total_ordering
from .converter import IDENTITY_CONVERTER
from .error import TrajectError, LinkError


IDENTIFIER = re.compile(r'^[^\d\W]\w*$')
PATH_VARIABLE = re.compile(r'\{([^}]*)\}')
VARIABLE = '{}'
PATH_SEPARATOR = re.compile(r'/+')
VIEW_PREFIX = '+'


@total_ordering
class Step(object):
    def __init__(self, s, converters=None):
        self.s = s
        self.converters = converters or {}
        self.generalized = generalize_variables(s)
        self.parts = tuple(self.generalized.split('{}'))
        self._variables_re = create_variables_re(s)
        self.names = parse_variables(s)
        self.cmp_converters = [self.get_converter(name) for name in self.names]
        self.validate()
        self.named_interpolation_str = interpolation_str(s) % tuple(
            [('%(' + name + ')s') for name in self.names])
        if len(set(self.names)) != len(self.names):
            raise TrajectError("Duplicate variable")

    def validate(self):
        self.validate_parts()
        self.validate_variables()

    def validate_parts(self):
        # XXX should also check for valid URL characters
        for part in self.parts:
            if '{' in part or '}' in part:
                raise TrajectError("invalid step: %s" % self.s)

    def validate_variables(self):
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
        return self.generalized

    def has_variables(self):
        return bool(self.names)

    def match(self, s):
        result = {}
        matched = self._variables_re.match(s)
        if matched is None:
            return False, result
        for name, value in zip(self.names, matched.groups()):
            converter = self.get_converter(name)
            try:
                result[name] = converter.decode([value])
            except ValueError:
                return False, {}
        return True, result

    def get_converter(self, name):
        return self.converters.get(name, IDENTITY_CONVERTER)

    def __eq__(self, other):
        if self.s != other.s:
            return False
        return self.cmp_converters == other.cmp_converters

    def __ne__(self, other):
        if self.s != other.s:
            return True
        return self.cmp_converters != other.cmp_converters

    def __lt__(self, other):
        if self.parts == other.parts:
            return False
        if self._variables_re.match(other.s) is not None:
            return False
        if other._variables_re.match(self.s) is not None:
            return True
        return self.parts > other.parts


class Node(object):
    def __init__(self):
        self._name_nodes = {}
        self._variable_nodes = []
        self.value = None
        self.absorb = False

    def add(self, step):
        if not step.has_variables():
            return self.add_name_node(step)
        return self.add_variable_node(step)

    def add_name_node(self, step):
        node = self._name_nodes.get(step.s)
        if node is not None:
            return node
        node = StepNode(step)
        self._name_nodes[step.s] = node
        return node

    def add_variable_node(self, step):
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

    def get(self, segment):
        node = self._name_nodes.get(segment)
        if node is not None:
            return node, {}
        for node in self._variable_nodes:
            matched, variables = node.match(segment)
            if matched:
                return node, variables
        return None, {}


class StepNode(Node):
    def __init__(self, step):
        super(StepNode, self).__init__()
        self.step = step

    def match(self, segment):
        return self.step.match(segment)


class Path(object):
    def __init__(self, path):
        self.path = path
        self.stack = parse_path(path)
        self.steps = [Step(segment) for segment in reversed(parse_path(path))]

    def discriminator(self):
        return '/'.join([step.discriminator_info() for step in self.steps])

    def interpolation_str(self):
        return '/'.join([step.named_interpolation_str for step in self.steps])

    def variables(self):
        result = []
        for step in self.steps:
            result.extend(step.names)
        return set(result)


class Inverse(object):
    def __init__(self, path, get_variables, converters,
                 parameter_names, absorb):
        self.path = path
        self.interpolation_path = Path(path).interpolation_str()
        self.get_variables = get_variables
        self.converters = converters
        self.parameter_names = set(parameter_names)
        self.absorb = absorb

    def path_variables(self, all_variables):
        converters = self.converters
        parameter_names = self.parameter_names
        result = {}
        for name, value in all_variables.items():
            if name in parameter_names:
                continue
            if value is None:
                raise LinkError(
                    "Path variable %s for path %s is None" % (
                        name, self.path))
            result[name] = converters.get(
                name, IDENTITY_CONVERTER).encode(value)[0]
        return result

    def query_parameters(self, all_variables, extra_parameters):
        converters = self.converters
        parameter_names = self.parameter_names
        result = {}
        for name, value in all_variables.items():
            if name not in parameter_names:
                continue
            if value is None or value == []:
                continue
            result[name] = converters.get(
                name, IDENTITY_CONVERTER).encode(value)
        if extra_parameters:
            for name, value in extra_parameters.items():
                result[name] = converters.get(
                    name, IDENTITY_CONVERTER).encode(value)
        return result

    def __call__(self, model):
        all_variables = self.get_variables(model)
        if not isinstance(all_variables, dict):
            raise LinkError("variables function for path %s "
                            "did not return a dict" % self.path)
        return self.with_variables(all_variables)

    def with_variables(self, all_variables):
        extra_parameters = all_variables.pop('extra_parameters', None)
        if self.absorb:
            absorbed_path = all_variables.pop('absorb')
        else:
            absorbed_path = None
        assert isinstance(all_variables, dict)

        path_variables = self.path_variables(all_variables)

        path = self.interpolation_path % path_variables
        if absorbed_path is not None:
            if path:
                path += '/' + absorbed_path
            else:
                # when there is no path yet, we are absorbing from
                # the root, and we don't want an additional /
                path = absorbed_path
        return path, self.query_parameters(all_variables, extra_parameters)


class TrajectRegistry(object):
    def __init__(self):
        self._root = Node()

    def add_pattern(self, path, value, converters=None, absorb=False):
        node = self._root
        known_variables = set()
        for segment in reversed(parse_path(path)):
            step = Step(segment, converters)
            node = node.add(step)
            variables = set(step.names)
            if known_variables.intersection(variables):
                raise TrajectError("Duplicate variables")
            known_variables.update(variables)
        node.value = value
        if absorb:
            node.absorb = True

    def consume(self, stack):
        stack = stack[:]
        node = self._root
        variables = {}
        while stack:
            if node.absorb:
                variables['absorb'] = '/'.join(reversed(stack))
                return node.value, [], variables
            segment = stack.pop()
            if segment.startswith(VIEW_PREFIX):
                stack.append(segment)
                return node.value, stack, variables
            new_node, new_variables = node.get(segment)
            if new_node is None:
                stack.append(segment)
                return node.value, stack, variables
            node = new_node
            variables.update(new_variables)
        if node.absorb:
            variables['absorb'] = ''
            return node.value, stack, variables
        return node.value, stack, variables


def parse_path(path):
    """Parse a path /foo/bar/baz to a stack of steps.

    A step is a string, such as 'foo', 'bar' and 'baz'.
    """

    # make sure dots are normalized away (may leave a single dot -> '.')
    path = posixpath.normpath(path).strip('/')

    if not path or path == '.':
        return []

    result = PATH_SEPARATOR.split(path)
    result.reverse()
    return result


def create_path(stack):
    """Builds a path from a stack.
    """
    return '/' + u'/'.join(reversed(stack))


def normalize_path(path):
    """ Normalizes the path as follows:

    * Collapses dots (``/../blog`` -> ``/blog``)
    * Ensures absolute paths (``./site`` -> ``/site``)
    * Removes double-slashes (``//index`` -> ``/index``)

    For example:

        ``../static//../app.py`` is turned into ``/app.py``

    """
    # the path is always absolute
    path = path.lstrip('.')

    # normpath returns '.' instead of '' if the path is empty, we want '/'
    path = posixpath.normpath(path)
    return path if path != '.' else '/'


def is_identifier(s):
    return IDENTIFIER.match(s) is not None


def parse_variables(s):
    result = PATH_VARIABLE.findall(s)
    for name in result:
        if not is_identifier(name):
            raise TrajectError(
                "illegal variable identifier: %s" % name)
    return result


def create_variables_re(s):
    return re.compile('^' + PATH_VARIABLE.sub(r'(.+)', s) + '$')


def generalize_variables(s):
    return PATH_VARIABLE.sub('{}', s)


def interpolation_str(s):
    return PATH_VARIABLE.sub('%s', s)
