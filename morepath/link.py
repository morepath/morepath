from interfaces import LinkError

def link(request, model, name, base, lookup):
    if base is None:
        base = get_base(model)
    if base is None:
        raise LinkError(
            "cannot create link to model %r with name %r, "
            "no base can be determined for model" % (model, name))
    traject = ITraject.component(base, lookup=lookup, default=None)
    if traject is None:
        raise LinkError(
            "cannot create link to model %r with name %r, "
            "no path information known for base %r" %
            (model, name, base))
    path = traject.get_path(model)
    # XXX what if path cannot be found?
    path = link(request, base, '', None) + '/' + path 
    if name != '':
        path = path + '/' + name
    return path

def get_base(model, lookup):
    return IModelBase.adapt(model, lookup=self.lookup, default=None)

# if model is registered with an app as base, IModelBase is registered
# for that model so it returns the app object
# if model is registered with a get_base, then this is called for that model


