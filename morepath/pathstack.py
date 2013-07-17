# -*- coding: utf-8 -*-
import re

DEFAULT = u'default'
RESOURCE = u'resource'

def parse_path(path, shortcuts=None):
    """Parses a path /foo/bar/baz to a stack of steps.

    A step is a ns, name tuple.

    Namespaces can be indicated with ++foo++ at the beginning of a step,
    where 'foo' is the namespace.

    If this is left out, the namespace is considered to be DEFAULT.

    A dictionary of shortcuts can be supplied, where each key is a
    a character combination (such as '@@') that should be expanded,
    and the value is the namespace it should be expanded to (such as 'view').
    Shortcuts only exist for namespaces and are applied to the beginning
    of the path.
    """
    if shortcuts is None:
        shortcuts = {}

    if path == '/' or not path:
        return []

    if path.startswith('/'):
        path = path[1:]

    steps = re.split(r'/+', path.rstrip('/'))

    result = []
    for step in steps:
        for key, value in shortcuts.items():
            if step.startswith(key):
                step = (u'++%s++' % value) + step[len(key):]
                break
        if step.startswith(u'++'):
            try:
                ns, name = step[2:].split(u'++', 1)
            except ValueError:
                ns = DEFAULT
                name = step
        else:
            ns = DEFAULT
            name = step
        result.append((ns, name))
    result.reverse()
    return result

def create_path(stack, shortcuts=None):
    """Rebuilds a path from a stack.

    A dictionary of shortcuts can be supplied to minimize namespaces use
    """
    if shortcuts is None:
        shortcuts = {}
    else:
        inversed_shortcuts = {}
        for key, value in shortcuts.items():
            # do not allow multiple shortcuts for the same namespace
            assert value not in inversed_shortcuts
            inversed_shortcuts[value] = key
        shortcuts = inversed_shortcuts
    result = []
    for ns, name in reversed(stack):
        if ns == DEFAULT:
            result.append(name)
            continue
        shortcut = shortcuts.get(ns)
        if shortcut is not None:
            result.append(shortcut + name)
            continue
        result.append(u'++%s++%s' % (ns, name))
    return '/' + u'/'.join(result)
