import sys
from copy import copy
import venusian
from .error import (ConflictError, DirectiveError, DirectiveReportError)
from .toposort import topological_sort
from .framehack import caller_package


class Configurable(object):
    """Object to which configuration actions apply.

    Actions can be added to a configurable.

    Once all actions are added, the configurable is executed.
    This checks for any conflicts between configurations and
    the configurable is expanded with any configurations from its
    extends list. Then the configurable is performed, meaning all
    its actions are performed (to it).
    """
    def __init__(self, extends=None, testing_config=None):
        """
        :param extends:
          the configurables that this configurable extends. Optional.
        :type extends: list of configurables, single configurable.
        :param testing_config:
          We can pass a config object used during testing. This causes
          the actions to be issued against the configurable directly
          instead of waiting for Venusian scanning. This allows
          the use of directive decorators in tests where scanning is
          not an option. Optional, default no testing config.
        """
        self.extends = extends or []
        self._testing_config = testing_config
        self.clear()
        if self._testing_config:
            self._testing_config.configurable(self)

    @property
    def testing_config(self):
        return self._testing_config

    @testing_config.setter
    def testing_config(self, config):
        self._testing_config = config
        config.configurable(self)

    def clear(self):
        """Clear any previously registered actions.

        This is normally not invoked directly, instead is called
        indirectly by :meth:`Config.commit`.
        """
        self._grouped_actions = {}
        self._class_to_actions = {}

    def actions(self):
        """Actions the configurable wants to register as it is scanned.

        A configurable may want to register some actions as it is registered
        with the config system.

        Should return a sequence of action, obj tuples.
        """
        return []

    def group_actions(self):
        """Group actions into :class:`Actions` by class.
        """
        # grouped actions by class (in fact deepest base class before
        # Directive)
        d = self._grouped_actions
        # make sure we don't forget about action classes in extends
        for configurable in self.extends:
            for action_class in configurable.action_classes():
                if action_class not in d:
                    d[action_class] = []
        # do the final grouping into Actions objects
        self._class_to_actions = {}
        for action_class, actions in d.items():
            self._class_to_actions[action_class] = Actions(
                actions, self.action_extends(action_class))

    def action_extends(self, action_class):
        """Get actions for action class in extends.
        """
        return [
            configurable._class_to_actions.get(action_class, Actions([], []))
            for configurable in self.extends]

    def action_classes(self):
        """Get action classes sorted in dependency order.
        """
        return sort_action_classes(self._class_to_actions.keys())

    def execute(self):
        """Execute actions for configurable.
        """
        self.group_actions()
        for action_class in self.action_classes():
            actions = self._class_to_actions.get(action_class)
            if actions is None:
                continue
            actions.prepare(self)
            actions.perform(self)

    def action(self, action, obj):
        """Register an action with configurable.

        This is normally not invoked directly, instead is called
        indirectly by :meth:`Config.commit`.

        :param action: The action to register with the configurable.
        :param obj: The object that this action is performed on.
        """
        self._grouped_actions.setdefault(
            action.group_key(), []).append((action, obj))


class Actions(object):
    def __init__(self, actions, extends):
        self._actions = actions
        self._action_map = {}
        self.extends = extends

    def prepare(self, configurable):
        """Prepare.

        Detect any conflicts between actions.
        Merges in configuration of what this action extends.

        Prepare must be called before perform is called.
        """
        # check for conflicts and fill action map
        discriminators = {}
        self._action_map = action_map = {}

        for action, obj in self._actions:
            id = action.identifier(configurable)
            discs = [id]
            discs.extend(action.discriminators(configurable))
            for disc in discs:
                other_action = discriminators.get(disc)
                if other_action is not None:
                    raise ConflictError([action, other_action])
                discriminators[disc] = action
            action_map[id] = action, obj
        # inherit from extends
        for extend in self.extends:
            self.combine(extend)

    def combine(self, actions):
        """Combine another prepared actions with this one.

        Those configuration actions that would conflict are taken to
        have precedence over those being combined with this one. This
        allows the extending actions to override actions in
        extended actions.

        :param actions: the :class:`Actions` to combine with this one.
        """
        to_combine = actions._action_map.copy()
        to_combine.update(self._action_map)
        self._action_map = to_combine

    def perform(self, configurable):
        """Perform actions in this configurable.

        Prepare must be called before calling this.
        """
        values = list(self._action_map.values())
        values.sort(key=lambda value: value[0].order or 0)
        for action, obj in values:
            try:
                action.perform(configurable, obj)
            except DirectiveError as e:
                raise DirectiveReportError(u"{}".format(e), action)


class Action(object):
    """A configuration action.

    A configuration action is performed on an object. Actions can
    conflict with each other based on their identifier and
    discriminators. Actions can override each other based on their
    identifier.

    Can be subclassed to implement concrete configuration actions.

    Action classes can have a ``depends`` attribute, which is a list
    of other action classes that need to be executed before this one
    is. Actions which depend on another will be executed after those
    actions are executed.
    """
    depends = []

    def __init__(self, configurable):
        """Initialize action.

        :param configurable: :class:`morepath.config.Configurable` object
          for which this action was configured.
        """
        self.configurable = configurable
        self.order = None

    def group_key(self):
        """By default we group directives by their class.

        Override this to group a directive with another directive,
        by returning that Directive class. It will create conflicts
        between those directives. Typically you'd do this when you are
        already subclassing from that directive too.
        """
        return self.__class__

    def codeinfo(self):
        """Info about where in the source code the action was invoked.

        By default there is no code info.
        """
        return None

    def identifier(self, configurable):
        """Returns an immutable that uniquely identifies this config.

        :param configurable: :class:`morepath.config.Configurable` object
          for which this action is being executed.

        Used for overrides and conflict detection.
        """
        raise NotImplementedError()  # pragma: nocoverage

    def discriminators(self, configurable):
        """Returns a list of immutables to detect conflicts.

        :param configurable: :class:`morepath.config.Configurable` object
          for which this action is being executed.

        Used for additional configuration conflict detection.
        """
        return []

    def clone(self, **kw):
        """Make a clone of this action.

        Keyword parameters can be used to override attributes in clone.

        Used during preparation to create new fully prepared actions.
        """
        action = copy(self)
        for key, value in kw.items():
            setattr(action, key, value)
        return action

    def prepare(self, obj):
        """Prepare action for configuration.

        :param obj: The object that the action should be performed on.

        Returns an iterable of prepared action, obj tuples.
        """
        return [(self, obj)]

    def perform(self, configurable, obj):
        """Register whatever is being configured with configurable.

        :param configurable: the :class:`morepath.config.Configurable`
          being configured.
        :param obj: the object that the action should be performed on.
        """
        raise NotImplementedError()


class Directive(Action):
    """An :class:`Action` that can be used as a decorator.

    Extends :class:`morepath.config.Action`.

    Base class for concrete Morepath directives such as ``@app.path()``,
    ``@app.view()``, etc.

    Can be used as a Python decorator.

    Can also be used as a context manager for a Python ``with``
    statement. This can be used to provide defaults for the directives
    used within the ``with`` statements context.

    When used as a decorator this tracks where in the source code
    the directive was used for the purposes of error reporting.
    """

    def __init__(self, configurable):
        """Initialize Directive.

        :param configurable: :class:`morepath.config.Configurable` object
          for which this action was configured.
        """
        super(Directive, self).__init__(configurable)
        self.attach_info = None

    def codeinfo(self):
        """Info about where in the source code the directive was invoked.
        """
        if self.attach_info is None:
            return None
        return self.attach_info.codeinfo

    def __enter__(self):
        return DirectiveAbbreviation(self)

    def __exit__(self, type, value, tb):
        if tb is not None:
            return False

    def immediate(self, wrapped):
        # If we are in testing mode, we immediately add the action.
        # Note that this broken for staticmethod and classmethod, unlike
        # the Venusian way, but we can fail hard when we see it.
        # It's broken for methods as well, but we cannot detect it
        # without Venusian, so unfortunately we're going to have to
        # let that pass.
        # XXX could we use something like Venusian's f_locals hack
        # to determine the class scope here and do the right thing?
        if isinstance(wrapped, staticmethod):
            raise DirectiveError(
                "Cannot use staticmethod with testing_config.")
        elif isinstance(wrapped, classmethod):
            raise DirectiveError(
                "Cannot use classmethod with testing_config.")
        self.configurable.testing_config.action(self, wrapped)

    def venusian_callback(self, wrapped, scanner, name, obj):
        if self.attach_info.scope == 'class':
            if isinstance(wrapped, staticmethod):
                func = wrapped.__get__(obj)
            elif isinstance(wrapped, classmethod):
                func = wrapped.__get__(obj, obj)
            else:
                raise DirectiveError(
                    "Cannot use directive on normal method %s of "
                    "class %s. Use staticmethod or classmethod first."
                    % (wrapped, obj))
        else:
            func = wrapped
        scanner.config.action(self, func)

    def __call__(self, wrapped):
        """Call with function to decorate.
        """
        if self.configurable.testing_config:
            self.immediate(wrapped)
        else:
            def callback(scanner, name, obj):
                return self.venusian_callback(wrapped, scanner, name, obj)
            self.attach_info = venusian.attach(wrapped, callback)
        return wrapped


class DirectiveAbbreviation(object):
    def __init__(self, directive):
        self.directive = directive

    def __call__(self, **kw):
        return self.directive.clone(**kw)


def ignore_import_error(pkg):
    # ignore import errors
    if issubclass(sys.exc_info()[0], ImportError):
        return
    raise  # reraise last exception


class Config(object):
    """Contains and executes configuration actions.

    Morepath configuration actions consist of decorator calls on
    :class:`App` instances, i.e. ``@app.view()`` and
    ``@app.path()``. The Config object can scan these configuration
    actions in a package. Once all required configuration is scanned,
    the configuration can be committed. The configuration is then
    processed, associated with :class:`morepath.config.Configurable`
    objects (i.e. :class:`App` objects), conflicts are detected,
    overrides applied, and the configuration becomes final.

    Once the configuration is committed all configured Morepath
    :class:`App` objects are ready to be served using WSGI.

    See :func:`setup`, which creates an instance with standard
    Morepath framework configuration. See also :func:`autoconfig` and
    :func:`autosetup` which help automatically load configuration from
    dependencies.
    """
    def __init__(self):
        self.configurables = []
        self.actions = []
        self.count = 0

    def scan(self, package=None, ignore=None, recursive=True):
        """Scan package for configuration actions (decorators).

        Register any found configuration actions with this
        object. This also includes finding any
        :class:`morepath.config.Configurable` objects.

        If given a package, it scans any modules and sub-packages as
        well recursively.

        :param package: The Python module or package to scan. Optional; if left
          empty case the calling package is scanned.
        :ignore: A Venusian_ style ignore to ignore some modules during
          scanning. Optional.
        :recursive: Scan packages recursively. By default this is ``True``.
          If set to ``False``, only the ``__init__.py`` of a package is
          scanned.
        """
        if package is None:
            package = caller_package()
        scanner = venusian.Scanner(config=self)
        scanner.scan(package, ignore=ignore, onerror=ignore_import_error,
                     recursive=recursive)

    def configurable(self, configurable):
        """Register a configurable with this config.

        This is normally not invoked directly, instead is called
        indirectly by :meth:`scan`.

        A :class:`App` object is a configurable.

        :param: The :class:`morepath.config.Configurable` to register.
        """
        self.configurables.append(configurable)
        for action, obj in configurable.actions():
            self.action(action, obj)

    def action(self, action, obj):
        """Register an action and obj with this config.

        This is normally not invoked directly, instead is called
        indirectly by :meth:`scan`.

        A Morepath directive decorator is an action, and obj is the
        function that was decorated.

        :param: The :class:`Action` to register.
        :obj: The object to perform action on.
        """
        action.order = self.count
        self.count += 1
        self.actions.append((action, obj))

    def prepared(self):
        """Get prepared actions before they are performed.

        The preparation phase happens as the first stage of a commit.
        This allows configuration actions to complete their
        configuration, do error checking, or transform themselves into
        different configuration actions.

        This calls :meth:`Action.prepare` on all registered configuration
        actions.

        :returns: An iterable of prepared action, obj combinations.
        """
        for action, obj in self.actions:
            for prepared, prepared_obj in action.prepare(obj):
                yield (prepared, prepared_obj)

    def commit(self):
        """Commit all configuration.

        * Clears any previous configuration from all registered
          :class:`morepath.config.Configurable` objects.
        * Prepares actions using :meth:`prepared`.
        * Actions are grouped by type of action (action class).
        * The action groups are executed in order of ``depends``
          between their action classes.
        * Per action group, configuration conflicts are detected.
        * Per action group, extending configuration is merged.
        * Finally all configuration actions are performed, completing
          the configuration process.

        This method should be called only once during the lifetime of
        a process, before the configuration is first used. After this
        the configuration is considered to be fixed and cannot be
        further modified. In tests this method can be executed
        multiple times as it automatically clears the
        configuration of its configurables first.
        """
        # clear all previous configuration; commit can only be run
        # once during runtime so it's handy to clear this out for tests
        for configurable in self.configurables:
            configurable.clear()

        for action, obj in self.prepared():
            action.configurable.action(action, obj)

        for configurable in sort_configurables(self.configurables):
            configurable.execute()


def sort_configurables(configurables):
    """Sort configurables topologically by extends.
    """
    return topological_sort(configurables, lambda c: c.extends)


def sort_action_classes(action_classes):
    """Sort action classes topologically by depends.
    """
    return topological_sort(action_classes, lambda c: c.depends)
