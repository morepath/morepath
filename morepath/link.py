from interfaces import ITraject, IModelBase, IRoot, LinkError

# XXX introduce ILink interface and make it possible to
# completely override link getting strategy based on model

def link(request, model, name, base, lookup):
    if isinstance(model, IRoot):
        return ''
    if base is None:
        base = get_base(model, lookup)
    if base is None:
        raise LinkError(
            "cannot determine base for model %r" % model)
    # XXX what if path cannot be found?
    result = '%s/%s' % (link(request, base, '', None, lookup),
                        path(model, base, lookup)) 
    if name != '':
        result += '/' + name
    return result

def get_base(model, lookup):
    return IModelBase.adapt(model, lookup=lookup, default=None)

def path(model, base, lookup):
    traject = ITraject.component(base, lookup=lookup, default=None)
    if traject is None:
        raise LinkError(
            "cannot create link to model %r with name %r, "
            "no path information known for base %r" %
            (model, name, base))
    return traject.get_path(model)

# if model is registered with an app as base, IModelBase is registered
# for that model so it returns the app object
# if model is registered with a get_base, then this is called for that model


