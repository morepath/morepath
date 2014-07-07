from .config import Action


# XXX I wonder whether we can rephrase directives as actions so
# we can use them at a lower level, and then wrap them as directives
class FunctionAction(Action):
    # XXX depends = [SettingDirective]

    def __init__(self, configurable, target, *sources):
        super(FunctionAction, self).__init__(configurable)
        self.target = target
        self.sources = tuple(sources)

    # def group_key(self):
    #     return FunctionDirective

    def identifier(self, app):
        return (self.target, self.sources)

    def perform(self, app, obj):
        app.register(self.target, self.sources, obj)
