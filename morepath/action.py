from .config import Action


# XXX I wonder whether we can rephrase directives as actions so
# we can use them at a lower level, and then wrap them as directives
class FunctionAction(Action):
    # XXX depends = [SettingDirective]

    def __init__(self, configurable, func, **key_dict):
        super(FunctionAction, self).__init__(configurable)
        self.func = func
        self.key_dict = key_dict

    def predicate_key(self, registry):
        # XXX would really like to do this once before any function
        # directives get executed but after all predicate directives
        # are executed. configuration ends needs a way to do extra
        # work after a directive's phase ends
        registry.install_predicates(self.func)
        registry.register_dispatch(self.func)
        return registry.key_dict_to_predicate_key(
            self.func.wrapped_func, self.key_dict)

    # def group_key(self):
    #     return FunctionDirective

    def identifier(self, app):
        return (self.func, self.predicate_key(app))

    def perform(self, app, obj):
        app.register_function(self.func, obj, **self.key_dict)
