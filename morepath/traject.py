import re
from functools import total_ordering
from .converter import IDENTITY_CONVERTER
from .error import TrajectError

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
                 parameter_names):
        self.path = path
        self.interpolation_path = Path(path).interpolation_str()
        self.get_variables = get_variables
        self.converters = converters
        self.parameter_names = set(parameter_names)

    def __call__(self, model):
        converters = self.converters
        parameter_names = self.parameter_names
        all_variables = self.get_variables(model)
        extra_parameters = all_variables.pop('extra_parameters', None)
        assert isinstance(all_variables, dict)
        variables = {
            name: converters.get(name, IDENTITY_CONVERTER).encode(value)[0] for
            name, value in all_variables.items()
            if name not in parameter_names}

        # all remaining variables need to show up in the path
        # XXX not sure about value != []
        parameters = {
            name: converters.get(name, IDENTITY_CONVERTER).encode(value) for
            name, value in all_variables.items()
            if (name in parameter_names and
                value is not None and value != [])
            }
        if extra_parameters:
            for name, value in extra_parameters.items():
                parameters[name] = converters.get(
                    name, IDENTITY_CONVERTER).encode(value)
        return self.interpolation_path % variables, parameters


class Traject(object):
    def __init__(self):
        super(Traject, self).__init__()
        self._root = Node()

    def add_pattern(self, path, value, converters=None):
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

    def consume(self, stack):
        stack = stack[:]
        node = self._root
        variables = {}
        while stack:
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
        return node.value, stack, variables


def parse_path(path):
    """Parse a path /foo/bar/baz to a stack of steps.

    A step is a string, such as 'foo', 'bar' and 'baz'.
    """
    path = path.strip('/')
    if not path:
        return []
    result = PATH_SEPARATOR.split(path)
    result.reverse()
    return result


def create_path(stack):
    """Builds a path from a stack.
    """
    return '/' + u'/'.join(reversed(stack))


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
