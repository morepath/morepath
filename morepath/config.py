from copy import copy
import venusian
from .error import ConflictError
from .framehack import caller_package


class Configurable(object):
    def __init__(self):
        self._actions = []

    def action(self, action):
        self._actions.append(action)


class Action(object):
    def discriminator(self):
        """Returns an immutable that uniquely identifies this config.

        Used for configuration conflict detection.
        """
        raise NotImplementedError()

    def extra_discriminator(self):
        """Extra immutable to add to discriminator.

        The framework can use this to add extra information to the
        discriminator, such as the App for directives.
        """
        return None

    # XXX needs docs
    def clone(self):
        return copy(self)

    def prepare(self, obj):
        """Prepare action for configuration.

        obj - the object being registered
        """
        pass

    def perform(self, obj):
        """Register whatever is being configured.

        obj - the object being registered
        """
        raise NotImplementedError()


class Directive(Action):
    def __init__(self, app):
        self.attach_info = None
        self.app = app
        super(Directive, self).__init__()

    def codeinfo(self):
        """Information about how the action was invoked.
        """
        return self.attach_info.codeinfo

    def extra_discriminator(self):
        return self.app

    def __call__(self, wrapped):
        def callback(scanner, name, obj):
            scanner.config.action(self, obj)
        self.attach_info = venusian.attach(wrapped, callback)
        return wrapped


class Config(object):
    def __init__(self):
        self.actions = []

    def scan(self, package=None, ignore=None):
        if package is None:
            package = caller_package()
        scanner = venusian.Scanner(config=self)
        scanner.scan(package, ignore=ignore)

    def action(self, action, obj):
        self.actions.append((action, obj))

    def validate(self, actions):
        discriminators = {}
        for action, obj in actions:
            discs = action.discriminator()
            if discs is None:
                continue
            if not isinstance(discs, list):
                discs = [discs]
            for disc in discs:
                disc = (action.extra_discriminator(), disc)
                other_action = discriminators.get(disc)
                if other_action is not None:
                    raise ConflictError([action, other_action])
                discriminators[disc] = action
        # XXX check that all base of an app is another app,
        # can only do this in the end
        # XXX check that a model registration that has a base that is
        # not an app supplies a get_base

    def prepared(self):
        result = []
        for action, obj in self.actions:
            action = action.clone()  # so that prepare starts fresh
            action.prepare(obj)
            result.append((action, obj))
        return result

    def commit(self):
        actions = self.prepared()
        self.validate(actions)
        for action, obj in actions:
            action.perform(obj)

    # XXX consider a load() that does scan & commit
