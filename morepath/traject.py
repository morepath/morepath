from .interfaces import TrajectError
#

"""

All lookups are in terms of base.

Try to look up step, registered by name

If not there, try to look up variable pattern, i.e. foo/?.

Find a list of matches.

For each match, see whether it matches the variables. If so, stop.

Once steps have been consumed, look up the model.

"""
import re
from .interfaces import ITraject

VARIABLE = '{}'

def parse(pattern_str):
    """Parse an URL pattern.

    Takes a URL pattern string and parses it into a tuple. Pattern
    strings look like this: foo/:bar/baz

    pattern_str - the pattern

    returns the pattern tuple.
    """
    pattern_str = normalize(pattern_str)
    result = []
    pattern = tuple(pattern_str.split('/'))
    known_variables = set()
    for step in pattern:
        if step[0] == ':':
            if step in known_variables:
                raise ParseError(
                    'URL pattern contains multiple variables with name: %s' %
                    step[1:])
            known_variables.add(step)
    return pattern

def subpatterns(pattern):
    """Decompose a pattern into sub patterns.

    A pattern can be decomposed into a number of sub patterns.
    ('a', 'b', 'c') for instance has the sub patterns ('a',),
    ('a', 'b') and ('a', 'b', 'c').

    pattern - the pattern tuple to decompose.

    returns the sub pattern tuples of this pattern.
    """
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
        
    def register(self, pattern, model_factory):
        sp = subpatterns(pattern)
        for p in sp:
            if has_variables(pattern[-1]):
                variable_pattern = pattern[:-1] + (VARIABLE,)
                variable_matchers = self._variable_matchers.setdefault(
                    variable_pattern, [])
                variable_matchers.append(VariableMatcher(pattern[-1]))
            else:
                self._step_matchers.add(pattern)
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
        # the next step cannot be matched, so try to get model
        # XXX pattern should be the full pattern, not the generalized one
        model = traject.get_model(pattern, variables)
        if model is None:
            # put what we tried to consume back on stack
            stack.extend(reversed(consumed))
            return False, base, stack
        return True, base, stack

