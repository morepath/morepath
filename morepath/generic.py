import reg


@reg.generic
def consumer(obj):
    """A consumer consumes steps in a stack to find an object.
    """


@reg.generic
def app(obj):
    """Get the application that this object is associated with.
    """


@reg.generic
def base(model):
    """Get the base that this model is associated with.
    """


@reg.generic
def lookup(obj):
    """Get the lookup that this object is associated with.
    """


@reg.generic
def path(request, model):
    """Get the path for a model in the context of a request.
    """


@reg.generic
def link(request, model):
    """Create a link (URL) to model.
    """


@reg.generic
def traject(obj):
    """Get traject for obj.
    """


@reg.generic
def resource(request, model):
    """Get the resource that represents the model in the context of a request.

    This resource is a representation of the model that be rendered to
    a response. It may also return a Response directly. If a string is
    returned, the string is converted to a Response with the string as
    the response body.
    """


@reg.generic
def response(request, model):
    """Get a Response for the model in the context of the request.
    """
