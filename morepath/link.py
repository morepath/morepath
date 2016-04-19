from .app import RegRegistry
from . import generic
from .converter import ConverterRegistry, IDENTITY_CONVERTER
from .error import LinkError
from .traject import Path as TrajectPath


class PathInfo(object):
    def __init__(self, path, parameters):
        self.path = path
        self.parameters = parameters


class Path(object):
    def __init__(self, path, factory_args, converters, absorb):
        traject_path = TrajectPath(path)
        self.interpolation_path = traject_path.interpolation_str()
        self.factory_args = factory_args
        path_variables = traject_path.variables()
        self.parameter_names = {name for name in factory_args if
                                name not in path_variables}
        self.converters = converters
        self.absorb = absorb

    def get_variables_and_parameters(self, variables, extra_parameters):
        converters = self.converters
        parameter_names = self.parameter_names
        path_variables = {}
        parameters = {}

        for name, value in variables.items():
            if name not in parameter_names:
                if value is None:
                    raise LinkError(
                        "Path variable %s for path %s is None" % (
                            name, self.path))
                path_variables[name] = converters.get(
                    name, IDENTITY_CONVERTER).encode(value)[0]
            else:
                if value is None or value == []:
                    continue
                parameters[name] = converters.get(
                    name, IDENTITY_CONVERTER).encode(value)
        if extra_parameters:
            for name, value in extra_parameters.items():
                parameters[name] = converters.get(
                    name, IDENTITY_CONVERTER).encode(value)
        return path_variables, parameters

    def __call__(self, model, variables):
        extra_parameters = variables.pop('extra_parameters', None)
        if self.absorb:
            absorbed_path = variables.pop('absorb')
        else:
            absorbed_path = None

        path_variables, url_parameters = self.get_variables_and_parameters(
            variables, extra_parameters)

        path = self.interpolation_path % path_variables

        if absorbed_path is not None:
            if path:
                path += '/' + absorbed_path
            else:
                # when there is no path yet we are absorbing from
                # the root and we don't want an additional /
                path = absorbed_path
        return PathInfo(path, url_parameters)


class LinkRegistry(object):
    factory_arguments = {
        'reg_registry': RegRegistry,
        'converter_registry': ConverterRegistry
    }

    def __init__(self, reg_registry, converter_registry):
        self.reg_registry = reg_registry
        self.converter_registry = converter_registry

    def register_path_variables(self, model, func):
        self.reg_registry.register_function(generic.path_variables,
                                            func,
                                            obj=model)

    def register_path(self, model, path, factory_args,
                      converters=None, absorb=False):
        converters = converters or {}
        get_path = Path(path, factory_args, converters, absorb)
        self.reg_registry.register_function(generic.class_path, get_path,
                                            model=model)

        def default_path_variables(obj):
            return {name: getattr(obj, name) for name in factory_args}

        self.reg_registry.register_function(generic.default_path_variables,
                                            default_path_variables,
                                            obj=model)

    def get_class_link(self, obj):
        pass

    def get_link(self, obj):
        pass

    def get_class_path(self, model, variables):
        return generic.class_path(model, variables,
                                  lookup=self.reg_registry.lookup)

    def get_path(self, obj):
        return self.get_class_path(
            obj.__class__,
            generic.path_variables(obj, lookup=self.reg_registry.lookup))
