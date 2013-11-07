import re
from functools import total_ordering

IDENTIFIER = re.compile(r'^[^\d\W]\w*$')
PATH_VARIABLE = re.compile(r'\{([^}]*)\}')
VARIABLE = '{}'

# XXX need to make this pluggable
KNOWN_CONVERTERS = {
    'str': str,
    'int': int
    }

class TrajectError(Exception):
    pass


@total_ordering
class Step(object):
    def __init__(self, s):
        self.s = s
        self.generalized = generalize_variables(s)
        self.parts = tuple(self.generalized.split('{}'))
        self._variables_re = create_variables_re(s)
        parser = NameParser(KNOWN_CONVERTERS)
        self.names, self.converters = parse_variables(s)
        self.validate()

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
        return self.generalized == other.generalized

    def __lt__(self, other):
        # XXX ordering based on converter?
        if self._variables_re.match(other.s) is not None:
            return False
        if other._variables_re.match(self.s) is not None:
            return True
        if sum([len(p) for p in self.parts]) > sum([len(p) for p in other.parts]):
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

        for i, node in enumerate(self._variable_nodes):
            pass
        self._variable_nodes.append(StepNode(step))

    def add_name_node(self, step):
        node = self._name_nodes.get(step.s)
        if node is not None:
            return node
        node = StepNode(step)
        self._name_nodes[step.s] = node
        return node

    def add_variable_node(self, step):
        for i, node in enumerate(self._variable_nodes):
            if node.step.generalized == step.generalized:
                if node.step.s == step.s:
                    return node
                raise TrajectError("conflict")
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


class Traject(Node):
    def __init__(self):
        super(Traject, self).__init__()

    def add_pattern(self, segments, value):
        node = self
        for segment in segments:
            node = node.add(Step(segment))
        node.value = value

    def __call__(self, stack):
        stack = stack[:]
        node = self
        variables = {}
        while stack:
            segment = stack.pop()
            new_node, new_variables = node.get(segment)
            if new_node is None:
                stack.append(segment)
                return node.value, stack, variables
            node = new_node
            variables.update(new_variables)
        return node.value, stack, variables

# class Step(object):
#     def __init__(self, s, data):
#         self.s = s
#         self.data = data
#         self._name_children = {}
#         self._variable_children = {}
#         self.generalized = generalize_variables(s)
#         self.variables_re = create_variables_re(s)
#         parser = NameParser(KNOWN_TYPES)
#         names = []
#         converters = []
#         for m in parse_variables(s):
#             name, converter = parser(m)
#             names.append(name)
#             converters.append(converter)
#         self.names = names
#         self.converters = converters

#     def has_variables(self):
#         return bool(self.names)

#     def add_step(self, s, data):
#         new_step = Step(s, data)
#         generalized = new_step.generalized
#         if not new_step.has_variables():
#             self._name_children[s] = new_step
#             return
#         for patterns in self._variable_children:
#             for i, pattern in enumerate(patterns):
#                 if not new_step.superset(pattern):
#                     patterns.insert(i, new_step)
                    
#         for child_generalized, possible_steps in self._children.items():
#             if not superset(generalized, child_generalized):
#                 continue
#             for i, possible_step in enumerate(possible_steps):
#                 if not superset(generalized, possible_step.generalized):
#                     possible_steps.insert(i, new_step)
#                     break
#         if generalized not in self._children:
#             self._children[generalized] = [new_step]
#         return new_step

#     def add_steps(self, segments, data):
#         step = self
#         for segment in segments[:-1]:
#             step = step.add_step(segment, None)
#         step.add_step(segments[-1], data)

#     def match(self, stack):
#         stack = stack[:]
#         if not stack:
#             return self.data, stack, {}
#         s = stack.pop()
#         #generalized = generalize_variables(s)
#         import pdb; pdb.set_trace()
#         possible_steps = self._children.get(generalized)
#         variables = {}
#         if possible_steps is None:
#             return self.data, stack, variables
#         for possible_step in possible_steps:
#             matched, matched_variables = possible_step.match_variables(s)
#             if not matched:
#                 continue
#             variables.update(matched_variables)
#             data, stack, matched_variables = possible_step.match(stack)
#             # allow back tracking
#             if data is not None:
#                 variables.update(matched_variables)
#                 return data, stack, variables
#         return self.data, stack, variables

#     def match_variables(self, s):
#         result = {}
#         matched = self.variables_re.match(s)
#         if matched is None:
#             return False, result
#         for name, converter, value in zip(self.names, self.converters,
#                                           matched.groups()):
#             try:
#                 result[name] = converter(value)
#             except ValueError:
#                 return False, {}
#         return True, result

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
        # XXX error if name is already seen?
    return names, converters


def create_variables_re(s):
    return re.compile('^' + PATH_VARIABLE.sub(r'(.+)', s) + '$')


def generalize_variables(s):
    return PATH_VARIABLE.sub('{}', s)


def interpolation_path(s):
    return PATH_VARIABLE.sub(r'%(\1)s', s)
