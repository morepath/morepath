Models and Linking
==================

Introduction
------------

Morepath lets you publish Python functions to the web as models, and
then allows you to create links to such models. To be able do so
Morepath needs to be told what variables there are in order to find
the model, and how to find these variables in order to construct a
link to the model.

Variables in paths
------------------

Let's assume we have a model class ``Overview``::

  class Overview(object):
      pass

Here's how we could expose it to the web under the path ``overview``::

  @app.model(model=Overview, path='overview')
  def get_overview():
      return Overview()

And let's give it a default view so we can see it when we go to its
URL::

  @app.view(model=Overview)
  def overview_default(request, model):
      return "Overview"

No variables are involved yet: they aren't in the ``path`` and the
function takes no arguments.

Let's try a single variable now. We assume we have a class ``Document``::

  class Document(object):
      def __init__(self, name):
          self.name = name

Let's expose it to the web under ``document/{name}``::

  @app.model(model=Document, path='document/{name}')
  def get_document(name):
      return query_document_by_name(name)

  @app.view(model=Document)
  def document_default(request, model):
      return "Document: " + model.name

Here we declare a variable in the path (``{name}``), and it gets
passed into the ``get_document`` function. The function does some kind
of query to look for a ``Document`` instance by name. We then have a
view that knows how to display a ``Document`` instance.

We can also have multiple variables. Perhaps we have a ``VersionedDocument``::

  class VersionedDocument(object):
      def __init__(self, name, version):
          self.name = name
          self.version = version

We could expose this to the web too::

  @app.model(model=VersionedDocument,
             path='versioned_document/{name}-{version}')
  def get_versioned_document(name, version):
      return query_versioned_document(name, version)

  @app.view(model=VersionedDocument)
  def versioned_document_default(request, model):
      return "Versioned document: %s %s" % (model.name, model.version)

The rule is that all variables declared in the path can be used as
arguments in the model function.

Variables in URL parameters
---------------------------

What if we want to use URL parameters to expose models? That is
possible too. Let's look at the ``Document`` case first::

  @app.model(model=Document, path='document?name={name}')
  def get_document(name):
      return query_document_by_name(name)

This exposes URLs of the type ``document?name=foo``. That's not as
nice as ``document/foo``, so we recommend against using it in this
case: you should use paths to identify something. URL parameters are
more useful for queries. Let's imagine we have a collection of
documents that we can search in for some ``text``::

  class DocumentCollection(object):
      def __init__(self, text):
          self.text = text

      def search(self):
          if self.text is None:
              return []
          return fulltext_search(self.text)

We now publish this collection, making it searchable::

  @app.model(model=DocumentCollection, path='search?text={text}')
  def document_search(text):
      return DocumentCollection(text)

Here is a view that returns a comma separated string with the names of
all matching documents::

  @app.view(model=DocumentCollection)
  def document_collection_default(request, model):
      return ', '.join([document.name for document in model.search()])

As you can see it uses the ``search`` method we created on the model.

Unlike path variables, URL parameters can be omitted, i.e. a plain
``search`` path without a ``text`` parameter. In that case ``text``
will be the value ``None``, and the ``search`` method has code to
handle this case: it returns the empty list.

Often it's useful to have a default instead. Let's imagine we have a
default search query, ``all`` that should be used if no ``text``
parameter is supplied (instead of ``None``). We can easily do this by
supplying a default value in the ``document_search`` function::

  @app.model(model=DocumentCollection, path='search?text={text}')
  def document_search(text='all'):
      return DocumentCollection(text)

Note that defaults have no meaning for path variables, because for the
path to be resolved in the first place a variable will be found: they
cannot be omitted.

Like with path variables, you can declare as many URL parameters as
you want.

Linking
-------

To create a link to a model, we can call :meth:`morepath.Request.link`
in our view code. At that point the model is examined to retrieve the
variables so that the path can be constructed.

Let's look at this simple case involving ``Document`` again::

  class Document(object):
      def __init__(self, name):
          self.name = name

  @app.model(model=Document, path='document/{name}')
  def get_document(name):
      return query_document_by_name(name)

We add a named view called ``link`` that links to the document itself::

  @app.view(model=Document, name='link')
  def document_self_link(request, model):
      return request.link(model)

Not very useful perhaps, but the principle is the same everywhere in
any view: as long as we have a ``Document`` instance we can create a
link to it using ``request.link()``.

But the link code needs to fill in the ``{name}`` variable, so the
link code needs to know, given an instance of ``Document``, how to get
its name. In this case this happened automatically: the ``name``
attribute is assumed to be the same as what should go into the link.

This may not always be the case, however: perhaps a different
attribute is used, or perhaps a more complicated method is used to
obtain the name. For those cases we can take over and supply a custom
``variables`` function that knows how to take variables from the
model. It needs to return a dictionary; the key is the variable name
as it is used in the path (including URL parameters), and the value is
the variable value.

As an example, here is the ``variables`` function for the ``Document``
case made explicit::

  @app.model(model=Document, path='document/{name}',
             variables=lambda model: dict(name=model.name))
  def get_document(name):
      return query_document_by_name(name)

The same principle applies when URL parameters are in use::

  @app.model(model=Document, path='document?name={name}',
             variables=lambda model: dict(name=model.name))
  def get_document(name):
      return query_document_by_name(name)

And let's look at the ``VersionedDocument`` case to look at multiple
variables::

  @app.model(model=VersionedDocument,
             path='versioned_document/{name}-{version}',
             variables=lambda model: dict(name=model.name,
                                          version=model.version))
  def get_versioned_document(name, version):
      return query_versioned_document(name, version)

Type hints
----------

So far we've only dealt with variables that have string values. But
what if we want to use other types for our variables, such as ``int``
or ``datetime``? Since the native format in URLs is strings we need to
have a way to convert a string into the type we want when a path is
resolved to a model, and back again from our variable to string when a
link is generated.

A common case is to use ``int`` values, for instance for database ids. Let's
take a look at this.

We consider this example::

  @app.model(model=Record, path='record?id={id}')
  def get_record(id):
      return query_record(id)

What now if we expect ``id`` to be an int? The example is wrong, as
without any indication otherwise, ``id`` is assumed to be a string.

We can easily fix this by supplying a default for ``id`` in the
``get_record`` function::

  @app.model(model=Record, path='record?id={id}')
  def get_record(id=0):
      return query_record(id)

Morepath will now introspect ``get_record``, see the default is an int
and will now assume that it's an integer. By supplying a default we've
accomplished two in one here, as it's a good idea to supply defaults
for URL parameters anyway, as that makes them properly optional.

What happens now when you pass an ``id`` that cannot be converted to
an int, say, ``record?id=foo``? The server will be unable to interpret
the request, and return a ``400 Bad Request`` response, as the URL
could not be interpreted.

But, you may say, before we said to use paths to identify things, but
here we used a URL parameter! Let's fix that::

  @app.model(model=Record, path='record/{id}')
  def get_record(id=0):
      return query_record(id)

Again, Morepath will introspect ``get_record`` and use the default
value to assume ``id`` is an int. That's in fact the *only* use for
the default value at all in this case -- a real default can never be
passed as ``id`` will always be there in a successfully resolved path.

What happens now if you pass in a string that cannot be converted to
an id, say ``record/foo``? The server simply won't be able to find a
model in that case, and will give a ``404 Not Found`` response.

Conversion
----------

Sometimes simple type hints are not enough. What if multiple possible
string representations for something exist? Let's examine the case of
:class:`datetime.date`.

We could represent it as a string in ISO 8601 format as returned by
the :meth:`datetime.date.isoformat` method, i.e. ``2014-01-15`` (and
this is in fact the default used by Morepath) but we could also use
another representation, say ``2014/15/01``.

Morepath lets us specify how an object is to be dumped (serialized,
encoded) to a string, and how a string is to be load (deserialized,
decoded) into an object. Here's how::

  from datetime import date
  from time import strptime, mktime

  @app.dump(type=date)
  def date_dump(d):
      return d.isoformat()

  @app.load(type=date)
  def date_load(s):
      return date.fromtimestamp(mktime(strptime(s, '%Y-%m-%d')))

Loading may fail due to the wrong string being supplied, for instance
a date in the wrong format. In that case the load function should
raise a ``ValueError`` (``strptime`` does this for instance when the
string doesn't match the format). When a ``ValueError`` is detected in
case of path variables, the path won't match, and if nothing else
matches, a ``404 Not Found`` response is returned. When it is detected
for URL parameters, a ``400 Bad Request`` response is returned.

Dumping is supposed to always succeed: any failure is a programming
error and an exception will be raised.

To help you write these functions, note that they're the inverse each
other: the output of load should always be successful input for dump,
and the output of dump should always be successful input for load.

Explicit types and required
---------------------------

You may also be explicit about what type should be used for a
parameter by supplying a ``types`` dictionary::

  @app.model(model=Record, path='record/{id}', types=dict(id=int))
  def get_record(id):
      return query_record(id)

If a type for a variable is omitted from the types dictionary the type
is still deduced from the decorated ``get_record`` function.

You can also be explicit about whether a URL parameter is required::

  @app.model(model=Record, path='record?id={id}', required=dict(id=True))
  def get_record(id):
      return query_record(id)

Normally if ``id`` is not supplied, ``None`` will be passed into
``get_record``, but in this case, if ``id`` is missing, you will get a
``400 Bad Request`` response. ``required`` has no effect on path
variables, as they are always required.
