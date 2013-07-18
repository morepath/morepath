#

"""

All lookups are in terms of base.

Try to look up step, registered by name

If not there, try to look up variable pattern, i.e. foo/?.

Find a list of matches.

For each match, see whether it matches the variables. If so, stop.

Once steps have been consumed, look up the model.

"""

VARIABLE = '{}'

class Traject(object):
    def __init__(self):
        self._step_matchers = {}
        self._variable_matchers = {}

    def match(self, pattern, step):
        step_pattern = self.match_step(pattern, step)
        if step_pattern is not None:
            return step_pattern, {}
        return self.match_variables(pattern, step)
        
    def match_step(self, pattern, step):
        pattern = pattern + (step,)
        if self._step_matchers.get(pattern):
            return pattern
        else:
            return None
    
    def match_variables(self, pattern, step):
        variable_pattern = pattern + (VARIABLE,)
        for variable_matcher in self._variable_matchers.get(pattern, []):
            matched = variable_matcher.match(step):
            if matched:
                break
        else:
            return None, {}
        return variable_pattern, matched
    
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
    model = traject.get_model(pattern, variables)
    if model is None:
        # put what we tried to consume back on stack
        stack.extend(reversed(consumed))
        return stack, [], base
    return stack, consumed, model
