from copy import copy
import venusian
from .error import ConflictError
from .framehack import caller_package


class Configurable(object):
    """Something configurable.

    The idea is that actions can be added to a configurable. The
    configurable is then prepared. This checks for any conflicts between
    configurations. Then the configurable is expanded with any configurations
    from its extends list. Finally the configurable can be performed,
    meaning all its actions will be applied (to it).
    """
    def __init__(self, extends=None):
        """Initialize configurable.

        extends - the configurables that this configurable extends.
                  can be a single configurable or a list of configurables.
                  optional.
        """
        if extends is None:
            extends = []
        if not isinstance(extends, list):
            extends = [extends]
        self.extends = extends
        self.clear()

    def clear(self):
        """Clear any previously registered actions.
        """
        self._actions = []
        self._action_map = None

    def action(self, action, obj):
        """Register an action to object with configurable.
        """
        self._actions.append((action, obj))

    def prepare(self):
        """Prepare configurable.

        Will detect any conflicts between configurations.

        Prepare must be called before perform is called.
        """
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
        """Combine actions in another prepared configurable with this one.
        """
        to_combine = configurable._action_map.copy()
        to_combine.update(self._action_map)
        self._action_map = to_combine

    def perform(self):
        """Perform actions in this configurable.

        Prepare must be called before calling this.
        """
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

        Returns an iterable of prepared action, obj tuples.
        """
        return [(self, obj)]

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
        """Call with function to decorate.
        """
        def callback(scanner, name, obj):
            scanner.config.action(self, obj)
        self.attach_info = venusian.attach(wrapped, callback)
        return wrapped


class Config(object):
    """Config object holds and executes configuration actions.
    """
    def __init__(self, root_configurable=None):
        """Initialize Config.

        root_configurable - an optional configurable that extends all
           other registered configurables.
        """
        self.root_configurable = root_configurable
        self.configurables = []
        self.actions = []
        self.count = 0

    def scan(self, package=None, ignore=None):
        """Scan package for configuration directives (decorators).

        Register any found directives as actions with this config.

        package - may be None, in which case the calling package
          will be scanned.
        """
        if package is None:
            package = caller_package()
        scanner = venusian.Scanner(config=self)
        scanner.scan(package, ignore=ignore)

    def configurable(self, configurable):
        """Register a configurable with this config.

        Automatically adds root_configurable in extends chain if it
        isn't there yet.
        """
        self.configurables.append(configurable)
        if (self.root_configurable is not None and
            not configurable.extends and
            configurable is not self.root_configurable):
            configurable.extends.append(self.root_configurable)

    def action(self, action, obj):
        """Register an action and obj with this config.

        action - the action to execute
        obj - the object to execute action over.
        """
        action.order = self.count
        self.count += 1
        self.actions.append((action, obj))

    def prepared(self):
        """Prepare configuration actions.

        Returns an iterable of prepared action, obj combinations.
        """
        for action, obj in self.actions:
            for prepared, prepared_obj in action.prepare(obj):
                yield (prepared, prepared_obj)

    def commit(self):
        """Commit all configuration.

        First prepares actions, then looks for configuration conflicts,
        then extends all configuration and executes it.
        """
        for action, obj in self.prepared():
            action.configurable.action(action, obj)
        configurables = sort_configurables(self.configurables)

        for configurable in configurables:
            configurable.prepare()

        for configurable in configurables:
            for extend in configurable.extends:
                configurable.combine(extend)
            configurable.perform()


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

