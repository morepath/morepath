from .interfaces import IConfigAction
from copy import copy
import venusian


class Action(IConfigAction):
    def discriminator(self):
        raise NotImplementedError()

    def clone(self):
        return copy(self)

    def prepare(self, name, obj):
        pass

    def perform(self, name, obj):
        raise NotImplementedError()


class Directive(Action):
    def __call__(self, wrapped):
        def callback(scanner, name, obj):
            scanner.config.action(self, name, obj)
        venusian.attach(wrapped, callback)
        return wrapped


class Config(object):
    def __init__(self):
        self.actions = []

    def app(self, app):
        self.actions.append((app, app.name, app))
        #XXX
        # self.actions.append((self, name, obj))

    def scan(self, package, ignore=None):
        scanner = venusian.Scanner(config=self)
        scanner.scan(package, ignore=ignore)

    def action(self, directive, name, obj):
        self.actions.append((directive, name, obj))

    def validate(self):
        # XXX check for conflicts
        # XXX check that all base of an app is another app,
        # can only do this in the end
        # XXX a model cannot be registered multiple times in the same
        # registry. same for app
        # XXX check that a model registration that has a base that is
        # not an app supplies a get_base
        pass

    def commit(self):
        actions = []
        for action, name, obj in self.actions:
            action = action.clone()  # so that prepare starts fresh
            action.prepare(name, obj)
            actions.append((action, name, obj))

        for action, name, obj in actions:
            action.perform(name, obj)
