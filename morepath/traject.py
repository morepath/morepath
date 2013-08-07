import re
from .interfaces import ITraject, IInverse, IModelBase, TrajectError
from .pathstack import parse_path, create_path
from .publish import SHORTCUTS
from comparch import Registry

IDENTIFIER = re.compile(r'^[^\d\W]\w*$')
PATH_VARIABLE = re.compile(r'\{([^}]*)\}')
VARIABLE = '{}'

# XXX need to make this pluggable
KNOWN_TYPES = {
    'str': str,
    'int': int
    }

class Traject(object):
    def __init__(self):
        self._step_matchers = set()
        self._conflicting_steps = set()
        self._variable_matchers = {}
        self._model_factories = {}
        self._inverse = Registry() # XXX caching?
        
    def register(self, path, model_factory, conflicting=False):
        pattern = parse(path)
        seen_names = set()
        for p in subpatterns(pattern):
            variable_matcher = VariableMatcher(p[-1], p)
            if variable_matcher.has_variables():
                for name in variable_matcher.names:
                    if name in seen_names:
                        raise TrajectError(
                            "path '%s' has a duplicate variable: %s" %
                            (path, name)
                            )
                    seen_names.add(name)
                variable_pattern = p[:-1] + (VARIABLE,)
                variable_matchers = self._variable_matchers.setdefault(
                    variable_pattern, set())
                for m in variable_matchers:
                    if variable_matcher.conflicts(m):
                        raise TrajectError(
                            "path '%s' conflicts with path '%s'" %
                            (path, create(m.pattern)))
                variable_matchers.add(variable_matcher)
            else:
                if conflicting and p in self._step_matchers:
                    raise TrajectError(
                        "path '%s' conflicts with another" % path)
                if p in self._conflicting_steps:
                    raise TrajectError(
                        "path '%s' conflicts with another" % path)
                self._step_matchers.add(p)
                if conflicting:
                    self._conflicting_steps.add(p)

        existing_model_factory = self._model_factories.get(pattern)
        if existing_model_factory is not None:
            raise TrajectError(
                "path '%s' is already used to register model %r" %
                (path, existing_model_factory))
        self._model_factories[pattern] = model_factory

    def register_inverse(self, model_class, path, get_variables):
        path = interpolation_path(path)
        self._inverse.register(IInverse, (model_class,), (path, get_variables))
        
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
        for variable_matcher in self._variable_matchers.get(variable_pattern,
                                                            []):
            matched = variable_matcher(step)
            if matched:
                break
        else:
            return None, {}
        return pattern + (variable_matcher.step,), matched

    def get_model(self, pattern, variables):
        model_factory = self._model_factories.get(pattern)
        if model_factory is None:
            return None
        return model_factory(**variables)

    def get_path(self, model):
        # XXX what if path cannot be found?
        path, get_variables = IInverse.component(model, lookup=self._inverse)
        variables = get_variables(model)
        assert isinstance(variables, dict)
        return path % variables

def traject_consumer(base, stack, lookup):
    traject = ITraject.component(base, lookup=lookup, default=None)
    if traject is None:
        return False, base, stack
    variables = {}
    pattern = ()
    consumed = []
    while stack:
        step = stack.pop()
        next_pattern, matched = traject.match(pattern, step)
        variables.update(matched)
        if next_pattern is None:
            # put the last step back onto the stack
            stack.append(step)
            break
        consumed.append(step)
        pattern = next_pattern
    model = traject.get_model(pattern, variables)
    if model is None:
        # put everything we tried to consume back on stack
        stack.extend(reversed(consumed))
        return False, base, stack
    return True, model, stack

class VariableMatcher(object):
    def __init__(self, step, pattern=None):
        self.step = step
        self.pattern = pattern # useful to report on conflicts
        self.ns, self.name = step
        self.variables_re = create_variables_re(self.name)
        self.generalized = generalize_variables(self.name)
        matched = parse_variables(self.name)
        parser = NameParser(KNOWN_TYPES)
        names = []
        converters = []
        for m in matched:
            name, converter = parser(self.name, m)
            names.append(name)
            converters.append(converter)
        self.names = names
        self.converters = converters

    def __eq__(self, other):
        return self.step == other.step
    
    def __hash__(self):
        return hash(self.step)

    def conflicts(self, other):
        if self.ns != other.ns:
            return False
        if self.name == other.name:
            return False
        return self.generalized == other.generalized
    
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

def normalize(pattern_str):
    if pattern_str.startswith('/'):
        return pattern_str[1:]
    return pattern_str

def parse(pattern_str):
    pattern_str = normalize(pattern_str)
    stack = parse_path(pattern_str, SHORTCUTS)
    return tuple(reversed(stack))

def create(pattern):
    return create_path(list(reversed(pattern)), SHORTCUTS)[1:]
    
def subpatterns(pattern):
    subpattern = []
    result = []
    for step in pattern:
        subpattern.append(step)
        result.append(tuple(subpattern))
    return result    

def is_identifier(s):
    return IDENTIFIER.match(s) is not None

def parse_variables(s):
    return PATH_VARIABLE.findall(s)

def create_variables_re(s):
    validate_variables(s)
    return re.compile('^' + PATH_VARIABLE.sub(r'(.+)', s) + '$')

def generalize_variables(s):
    return PATH_VARIABLE.sub('{}', s)

def interpolation_path(s):
    return PATH_VARIABLE.sub(r'%(\1)s', s)
    
def validate_variables(s):
    parts = PATH_VARIABLE.split(s)
    if parts[0] == '':
        parts = parts[1:]
    if parts[-1] == '':
        parts = parts[:-1]
    for part in parts:
        if part == '':
            # XXX also include path info in error
            raise TrajectError(
                "path segment '%s' cannot be parsed, variables cannot be concecutive" %
                s)
    
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

def register_model(registry, base, model, path, variables, model_factory,
                   conflicting=False):
    traject = registry.exact_get(ITraject, (base,))
    if traject is None:
        traject = Traject()
        registry.register(ITraject, (base,), traject)
    traject.register(path, model_factory, conflicting)
    traject.register_inverse(model, path, variables)
    def get_base(model):
        return base() # XXX assume base is an app object
    registry.register(IModelBase, (model,), get_base)

def register_app(registry, base, model, name, app_factory):
    #if model in known_app_models:
    register_model(registry, base, model, name, lambda app: {}, app_factory,
                   conflicting=True)
    
