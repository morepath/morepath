from copy import copy
import venusian
from .error import ConflictError
from .framehack import caller_package


class Configurable(object):
    def __init__(self, extends=None):
        if extends is None:
            extends = []
        if not isinstance(extends, list):
            extends = [extends]
        self.extends = extends
        self.clear()

    def clear(self):
        self._actions = []
        self._action_map = None

    def action(self, action, obj):
        self._actions.append((action, obj))

    def prepare(self):
        discriminators = {}
        self._action_map = action_map = {}
        for action, obj in self._actions:
            id = action.identifier()
            discs = [id]
            discs.extend(action.discriminators())
            for disc in discs:
                other_action = discriminators.get(disc)
                if other_action is not None:
                    raise ConflictError([action, other_action])
                discriminators[disc] = action
            action_map[id] = action, obj

    def combine(self, configurable):
        to_combine = configurable._action_map.copy()
        to_combine.update(self._action_map)
        self._action_map = to_combine

    def perform(self):
        values = self._action_map.values()
        values.sort(key=lambda (action, obj): action.order)
        for action, obj in values:
            action.perform(self, obj)

class Action(object):
    """A configuration action.
    """
    def __init__(self, configurable):
        self.configurable = configurable
        self.order = None

    def identifier(self):
        """Returns an immutable that uniquely identifies this config.

        Used for overrides and conflict detection.
        """
        raise NotImplementedError()

    def clone(self, **kw):
        """Make a clone of this action.

        Keyword parameters can be used to override attributes in clone.
        """
        action = copy(self)
        for key, value in kw.items():
            setattr(action, key, value)
        return action

    def discriminators(self):
        """Returns a list of immutables to detect conflicts.

        Used for additional configuration conflict detection.
        """
        return []

    def prepare(self, obj):
        """Prepare action for configuration.

        obj - the object being registered

        Returns an iterable of prepared actions.
        """
        return [self]

    def perform(self, configurable, obj):
        """Register whatever is being configured with configurable.

        configurable - whatever is being configured
        obj - the object being registered
        """
        raise NotImplementedError()

class Directive(Action):
    """An action that can be used as a decorator.
    """

    def __init__(self, configurable):
        super(Directive, self).__init__(configurable)
        self.attach_info = None

    def codeinfo(self):
        """Information about how the action was invoked.
        """
        return self.attach_info.codeinfo

    def __call__(self, wrapped):
        def callback(scanner, name, obj):
            scanner.config.action(self, obj)
        self.attach_info = venusian.attach(wrapped, callback)
        return wrapped


class Config(object):
    def __init__(self, root_configurable=None):
        self.root_configurable = root_configurable
        self.configurables = []
        self.actions = []
        self.count = 0

    def scan(self, package=None, ignore=None):
        if package is None:
            package = caller_package()
        scanner = venusian.Scanner(config=self)
        scanner.scan(package, ignore=ignore)

    def configurable(self, configurable):
        self.configurables.append(configurable)
        if self.root_configurable is not None:
            if (configurable is not self.root_configurable and
                self.root_configurable not in configurable.extends):
                configurable.extends.append(self.root_configurable)

    def action(self, action, obj):
        action.order = self.count
        self.count += 1
        self.actions.append((action, obj))

    def prepared(self):
        for action, obj in self.actions:
            for prepared in action.prepare(obj):
                yield (prepared, obj)

    def commit(self):
        for action, obj in self.prepared():
            action.configurable.action(action, obj)
        configurables = sort_configurables(self.configurables)

        for configurable in configurables:
            configurable.prepare()

        for configurable in configurables:
            for extend in configurable.extends:
                configurable.combine(extend)
            configurable.perform()


def setup():
    config = Config()
    import morepath
    config.scan(morepath, ignore=['.tests'])
    return config


def sort_configurables(configurables):
    """Sort configurables topologically by extends.
    """
    result = []
    marked = set()
    def visit(n):
        if n in marked:
            return
        for m in n.extends:
            visit(m)
        marked.add(n)
        result.append(n)
    for n in configurables:
        visit(n)
    return result

