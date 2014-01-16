import re
from functools import total_ordering
from reg import Registry
from werkzeug.exceptions import BadRequest

IDENTIFIER = re.compile(r'^[^\d\W]\w*$')
PATH_VARIABLE = re.compile(r'\{([^}]*)\}')
VARIABLE = '{}'
PATH_SEPARATOR = re.compile(r'/+')
VIEW_PREFIX = '+'

# XXX need to make this pluggable
# XXX need support for encoding, i.e. unicode URL parameters
KNOWN_CONVERTERS = {
    'str': str,
    'int': int,
    'unicode': unicode,
    }

CONVERTER_SET = set(KNOWN_CONVERTERS.values())

class TrajectError(Exception):
    pass


@total_ordering
class Step(object):
    def __init__(self, s):
        self.s = s
        self.generalized = generalize_variables(s)
        self.parts = tuple(self.generalized.split('{}'))
        self._variables_re = create_variables_re(s)
        self.names, self.converters = parse_variables(s)
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
        for name, converter, value in zip(self.names, self.converters,
                                          matched.groups()):
            try:
                result[name] = converter(value)
            except ValueError:
                return False, {}
        return True, result

    def __eq__(self, other):
        return self.s == other.s

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
            if node.step.s == step.s:
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
        return result


class Traject(object):
    def __init__(self):
        super(Traject, self).__init__()
        # XXX caching is not enabled
        # also could this really be registering things in the main
        # application registry instead? if it did and we solve caching
        # for that this would get it automatically. but this would
        # require each traject base to have its own lookup
        self._root = Node()
        self._inverse = Registry()

    def add_pattern(self, path, value):
        node = self._root
        known_variables = set()
        for segment in reversed(parse_path(path)):
            step = Step(segment)
            node = node.add(step)
            variables = set(step.names)
            if known_variables.intersection(variables):
                raise TrajectError("Duplicate variables")
            known_variables.update(variables)
        node.value = value

    def inverse(self, model_class, path, get_variables, parameter_names):
        # XXX should we do checking for duplicate variables here too?
        path = Path(path)
        self._inverse.register('inverse',
                               [model_class],
                               (path.interpolation_str(), get_variables,
                                parameter_names))

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

    def path(self, model):
        path, get_variables, parameter_names = self._inverse.component(
            'inverse', [model])
        variables = get_variables(model)
        assert isinstance(variables, dict)
        parameters = { name: variables[name] for name in parameter_names }
        return path % variables, parameters


class ParameterFactory(object):
    def __init__(self, parameters):
        self.parameters = parameters
        self.info = info = []
        for name, value in parameters.items():
            if value is None:
                convert = str
                default = None
            elif value in CONVERTER_SET:
                convert = value
                default = None
            else:
                convert = type(value)
                default = value
                assert convert in CONVERTER_SET
            info.append((name, convert, default))

    def __call__(self, request):
        result = {}
        for name, convert, default in self.info:
            value = request.args.get(name)
            if value is None:
                result[name] = default
                continue
            try:
                result[name] = convert(value)
            except ValueError:
                raise BadRequest()
        return result


class NameParser(object):
    def __init__(self, known_converters):
        self.known_converters = known_converters

    def __call__(self, s):
        parts = s.split(':')
        if len(parts) > 2:
            raise TrajectError(
                "illegal variable: %s" % s)
        if len(parts) == 1:
            name = s.strip()
            converter_id = 'str'
        else:
            name, converter_id = parts
            name = name.strip()
            converter_id = converter_id.strip()
        if not is_identifier(name):
            raise TrajectError(
                "illegal variable identifier: %s" % name)
        converter = self.known_converters.get(converter_id)
        if converter is None:
            raise TrajectError("unknown converter: %s" % converter_id)
        return name, converter


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
    names = []
    converters = []
    parser = NameParser(KNOWN_CONVERTERS)
    variables = PATH_VARIABLE.findall(s)
    for variable in variables:
        name, converter = parser(variable)
        names.append(name)
        converters.append(converter)
    return names, converters


def create_variables_re(s):
    return re.compile('^' + PATH_VARIABLE.sub(r'(.+)', s) + '$')


def generalize_variables(s):
    return PATH_VARIABLE.sub('{}', s)


def interpolation_str(s):
    return PATH_VARIABLE.sub('%s', s)
