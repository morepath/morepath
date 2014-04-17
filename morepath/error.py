# -*- coding: utf-8 -*-


class ConfigError(Exception):
    """Raised when configuration is bad
    """


def conflict_keyfunc(action):
    codeinfo = action.codeinfo()
    if codeinfo is None:
        return 0
    filename, lineno, function, sourceline = codeinfo
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
            codeinfo = action.codeinfo()
            if codeinfo is None:
                continue
            filename, lineno, function, sourceline = codeinfo
            result.append('  File "%s", line %s' % (filename, lineno))
            result.append('    %s' % sourceline)
        msg = '\n'.join(result)
        super(ConflictError, self).__init__(msg)


class DirectiveReportError(ConfigError):
    """Raised when there's a problem with a directive.
    """
    def __init__(self, message, action):
        codeinfo = action.codeinfo()
        result = [message]
        if codeinfo is not None:
            filename, lineno, function, sourceline = codeinfo
            result.append('  File "%s", line %s' % (filename, lineno))
            result.append('    %s' % sourceline)
        msg = '\n'.join(result)
        super(DirectiveReportError, self).__init__(msg)


class DirectiveError(ConfigError):
    pass


class ResolveError(Exception):
    """Raised when path cannot be resolved
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


class MountError(Exception):
    pass


class TopologicalSortError(Exception):
    pass
