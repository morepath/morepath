import re
from .interfaces import ITraject, TrajectError
from .pathstack import parse_path
from .publisher import SHORTCUTS

VARIABLE = '{}'

def normalize(pattern_str):
    if pattern_str.startswith('/'):
        return pattern_str[1:]
    return pattern_str

def parse(pattern_str):
    pattern_str = normalize(pattern_str)
    stack = parse_path(pattern_str, SHORTCUTS)
    return tuple(reversed(stack))

def subpatterns(pattern):
    subpattern = []
    result = []
    for step in pattern:
        subpattern.append(step)
        result.append(tuple(subpattern))
    return result

class Traject(object):
    def __init__(self):
        self._step_matchers = set()
        self._variable_matchers = {}
        self._model_factories = {}
        
    def register(self, path, model_factory):
        pattern = parse(path)
        for p in subpatterns(pattern):
            last_step = p[-1]
            ns, name = last_step
            variable_matcher = VariableMatcher(ns, name)
            if variable_matcher.has_variables():
                variable_pattern = p[:-1] + (VARIABLE,)
                variable_matchers = self._variable_matchers.setdefault(
                    variable_pattern, [])
                variable_matchers.append(variable_matcher)
            else:
                self._step_matchers.add(p)
        self._model_factories[pattern] = model_factory
        
    def match(self, pattern, step):
        step_pattern = self.match_step(pattern, step)
        if step_pattern is not None:
            return step_pattern, {}
        return self.match_variables(pattern, step)
        
    def match_step(self, pattern, step):
        pattern = pattern + (step,)
        if pattern in self._step_matchers:
            return pattern
        else:
            return None
    
    def match_variables(self, pattern, step):
        variable_pattern = pattern + (VARIABLE,)
        for variable_matcher in self._variable_matchers.get(pattern, []):
            matched = variable_matcher(step)
            if matched:
                break
        else:
            return None, {}
        return pattern + step, matched

    def get_model(self, pattern, variables):
        model_factory = self._model_factories.get(pattern)
        if model_factory is None:
            return None
        return model_factory(**variables)
    
IDENTIFIER = re.compile(r'^[^\d\W]\w*$')
PATH_VARIABLE = re.compile(r'\{([^}]*)\}')

def is_identifier(s):
    return IDENTIFIER.match(s) is not None

def parse_variables(s):
    return PATH_VARIABLE.findall(s)

def create_variables_re(s):
    return re.compile('^' + PATH_VARIABLE.sub(r'(.+)', s) + '$')


# XXX need to make this pluggable
KNOWN_TYPES = {
    'str': str,
    'int': int
    }

class NameParser(object):
    def __init__(self, known_types):
        self.known_types = known_types

    def __call__(self, pattern, s):
        parts = s.split(':')
        if len(parts) > 2:
            raise TrajectError("illegal path '%s', illegal identifier: %s" % (
                    pattern, s))
        if len(parts) == 1:
            name = s.strip()
            type_id = 'str'
        else:
            name, type_id = parts
            name = name.strip()
            type_id = type_id.strip()
        if not is_identifier(name):
            raise TrajectError("illegal path '%s', illegal identifier: %s" % (
                    pattern, name))
        converter = self.known_types.get(type_id)
        if converter is None:
            return TrajectError("illegal path '%s', unknown type: %s" % (
                                pattern, type_id))
        return name, converter

def parse_variable_name(pattern, name):
    parts = name.split(':')
    if len(parts) == 1:
        return name.strip(), str
    if len(parts) != 2:
        raise TrajectError(
            "path '%s' cannot be parsed, illegal identifier: %s" %
            (pattern, name))
    name, type_id = parts
    name = name.strip()
    type_id = type_id.strip()

class VariableMatcher(object):
    def __init__(self, ns, pattern):
        self.ns = ns
        self.pattern = pattern
        self.variables_re = create_variables_re(pattern)
        matched = parse_variables(pattern)
        parser = NameParser(KNOWN_TYPES)
        names = []
        converters = []
        for m in matched:
            name, converter = parser(pattern, m)
            names.append(name)
            converters.append(converter)
        self.names = names
        self.converters = converters

    def has_variables(self):
        return bool(self.names)

    def __call__(self, step):
        ns, name = step
        if ns != self.ns:
            return {}
        matched = self.variables_re.match(name)
        if matched is None:
            return {}
        result = {}
        for name, converter, match in zip(
            self.names, self.converters, matched.groups()): 
            try:
                result[name] = converter(match)
            except ValueError:
                # cannot convert, so isn't a match
                return {}
        return result
        
class TrajectConsumer(object):
    def __init__(self, lookup):
        self.lookup = lookup

    def __call__(self, base, stack):
        traject = ITraject.component(base, lookup=self.lookup)
        variables = {}
        pattern = ()
        consumed = []
        while stack:
            step = stack.pop()
            consumed.append(step)
            next_pattern, matched = traject.match(pattern, step)
            if next_pattern is None:
                break
            pattern = next_pattern
        model = traject.get_model(pattern, variables)
        if model is None:
            # put what we tried to consume back on stack
            stack.extend(reversed(consumed))
            return False, base, stack
        return True, model, stack

