from .config import Action


# XXX I wonder whether we can rephrase directives as actions so
# we can use them at a lower level, and then wrap them as directives
class FunctionAction(Action):
    # XXX depends = [SettingDirective]

    def __init__(self, configurable, func, *predicate_key):
        super(FunctionAction, self).__init__(configurable)
        self.func = func
        self.predicate_key = predicate_key

    # def group_key(self):
    #     return FunctionDirective

    def identifier(self, app):
        return (self.func, self.predicate_key)

    def perform(self, app, obj):
        app.register_dispatch_value(self.func, self.predicate_key, obj)
