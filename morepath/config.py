from copy import copy
import venusian
from .error import ConflictError
from .framehack import caller_package


class Action(object):
    attach_info = None

    def discriminator(self):
        """Returns an immutable that uniquely identifies this config.

        Used for configuration conflict detection.
        """
        raise NotImplementedError()

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
            disc = action.discriminator()
            if disc is None:
                continue
            other_attach_info = discriminators.get(disc)
            if other_attach_info is not None:
                raise ConflictError([action.attach_info, other_attach_info])
            discriminators[disc] = action.attach_info
        # XXX check that all base of an app is another app,
        # can only do this in the end
        # XXX a model cannot be registered multiple times in the same
        # registry. same for app
        # XXX check that a model registration that has a base that is
        # not an app supplies a get_base

    def commit(self):
        actions = []
        for action, obj in self.actions:
            action = action.clone()  # so that prepare starts fresh
            action.prepare(obj)
            actions.append((action, obj))
        self.validate(actions)

        for action, obj in actions:
            action.perform(obj)

    # XXX consider a load() that does scan & commit
