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

VARIABLE = '{}'

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
    
#variable_re = re.compile(PATH_VARIABLE)

class VariableMatcher(object):
    def __init__(self, ns, pattern):
        self.ns = ns
        self.pattern = pattern
        self.variables_re = create_variables_re(pattern)
        names = parse_variables(pattern)
        names = [name.strip() for name in names]
        for name in names:
            if not is_identifier(name):
                raise TrajectError(
                    "path '%s' cannot be parsed, illegal identifier: %s" %
                    (pattern, name))
        self.names = names

    def __call__(self, step):
        ns, name = step
        if ns != self.ns:
            return {}
        matched = self.variables_re.match(name)
        if matched is None:
            return {}
        result = {}
        for name, match in zip(self.names, matched.groups()): 
            result[name] = match
        return result
        
def consume(lookup, base, stack):
    traject = ITraject.component(base, lookup=lookup)
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
        return stack, [], base
    return stack, consumed, model
