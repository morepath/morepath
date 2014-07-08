import reg
from .error import LinkError


@reg.generic
def consume(request, model):
    """Consume request.unconsumed to new model, starting with model.

    Returns the new model, or None if no new model could be found.

    Adjusts request.unconsumed with the remaining unconsumed stack.
    """
    return None


@reg.generic
def context(model):
    """Get the context dictionary available for a model.
    """
    raise NotImplementedError  # pragma: nocoverage


@reg.generic
def path(model):
    """Get the path and parameters for a model in its own application.
    """
    raise LinkError()


@reg.generic
def link(request, model, mounted):
    """Create a link (URL) to a model, including any mounted applications.
    """
    raise NotImplementedError  # pragma: nocoverage


@reg.generic
def traject(obj):
    """Get traject for obj.
    """
    raise NotImplementedError  # pragma: nocoverage


@reg.generic
def view(request, model):
    """Get the view that represents the model in the context of a request.

    This view is a representation of the model that be rendered to
    a response. It may also return a Response directly. If a string is
    returned, the string is converted to a Response with the string as
    the response body.
    """
    raise NotImplementedError  # pragma: nocoverage


@reg.generic
def response(request, model):
    """Get a Response for the model in the context of the request.
    """
    raise NotImplementedError  # pragma: nocoverage


@reg.generic
def settings():
    """Return current settings object.

    In it are sections, and inside of the sections are the setting values.
    If there is a ``logging`` section and a ``loglevel`` setting in it,
    this is how you would access it::

      settings().logging.loglevel

    """
    raise NotImplementedError  # pragma: nocoverage


@reg.generic
def identify(request):
    """Returns an Identity or None if no identity can be found.

    Can also return NO_IDENTITY, but None is converted automatically
    to this.
    """
    raise NotImplementedError  # pragma: nocoverage


@reg.generic
def verify_identity(identity):
    """Returns True if the claimed identity can be verified.
    """
    return False


@reg.generic
def remember_identity(response, request, identity):
    """Modify response so that identity is remembered by client.
    """
    raise NotImplementedError  # pragma: nocoverage


@reg.generic
def forget_identity(response, request):
    """Modify response so that identity is forgotten by client.
    """
    raise NotImplementedError  # pragma: nocoverage


@reg.generic
def permits(identity, model, permission):
    """Returns True if identity has permission for model.

    identity can be the special NO_IDENTITY singleton; register for
    NoIdentity to handle this case separately.
    """
    raise NotImplementedError  # pragma: nocoverage


@reg.generic
def linkmaker(request, mounted):
    """Returns a link maker for request and mounted.
    """
    raise NotImplementedError  # pragma: nocoverage
