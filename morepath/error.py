# -*- coding: utf-8 -*-


class ConfigError(Exception):
    """Raised when configuration is bad
    """


def conflict_keyfunc(action):
    filename, lineno, function, sourceline = action.attach_info.codeinfo
    return (filename, lineno)


class ConflictError(ConfigError):
    """Raised when there is a conflict in configuration.
    """
    def __init__(self, actions):
        actions.sort(key=conflict_keyfunc)
        self.actions = actions
        result = [
            'Conflict between:']
        for action in actions:
            filename, lineno, function, sourceline = action.attach_info.codeinfo
            result.append('  File "%s", line %s' % (filename, lineno))
            result.append('    %s' % sourceline)
        msg = '\n'.join(result)
        super(ConflictError, self).__init__(msg)


class ResolveError(Exception):
    """Raised when path cannot be resolved
    """


class ModelError(ResolveError):
    """Raised when a model cannot be resolved
    """


class ViewError(ResolveError):
    """Raised when a view cannot be resolved
    """


class TrajectError(Exception):
    """Raised when path supplied to traject is not allowed.
    """


class LinkError(Exception):
    """Raised when a link cannot be made.
    """
