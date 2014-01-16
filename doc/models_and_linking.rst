Models and Linking
==================

Introduction
------------

Morepath lets you publish Python functions to the web as models, and
then allows you to create links to such models. To be able do so
Morepath needs to be told what variables there are in order to find
the model, and how to find these variables in order to construct a
link to the model.

Paths
-----

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
``get_overview`` function takes no arguments.

Let's try a single variable now. We have a class ``Document``::

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

We can also have multiple variables in a path. We have a
``VersionedDocument``::

  class VersionedDocument(object):
      def __init__(self, name, version):
          self.name = name
          self.version = version

We could expose this to the web like this::

  @app.model(model=VersionedDocument,
             path='versioned_document/{name}-{version}')
  def get_versioned_document(name, version):
      return query_versioned_document(name, version)

  @app.view(model=VersionedDocument)
  def versioned_document_default(request, model):
      return "Versioned document: %s %s" % (model.name, model.version)

The rule is that all variables declared in the path can be used as
arguments in the model function.

URL parameters
--------------

What if we want to use URL parameters to expose models? That is
possible too. Let's look at the ``Document`` case first::

  @app.model(model=Document, path='document')
  def get_document(name):
      return query_document_by_name(name)

``get_document`` has an argument ``name``, but it doesn't appear in
the path. This argument is now taken to be a URL parameter. So, this
exposes URLs of the type ``document?name=foo``. That's not as nice as
``document/foo``, so we recommend against parameters in this case: you
should use paths to identify something.

URL parameters are more useful for queries. Let's imagine we have a
collection of documents and we have an API on it that allows us to
search in it for some ``text``::

  class DocumentCollection(object):
      def __init__(self, text):
          self.text = text

      def search(self):
          if self.text is None:
              return []
          return fulltext_search(self.text)

We now publish this collection, making it searchable::

  @app.model(model=DocumentCollection, path='search')
  def document_search(text):
      return DocumentCollection(text)

To be able to see something, we add a view that returns a comma
separated string with the names of all matching documents::

  @app.view(model=DocumentCollection)
  def document_collection_default(request, model):
      return ', '.join([document.name for document in model.search()])

As you can see it uses the ``DocumentCollection.search`` method.

Unlike path variables, URL parameters can be omitted, i.e. we can have
a plain ``search`` path without a ``text`` parameter. In that case
``text`` will be the value ``None``. The ``search`` method has code to
handle this special case: it returns the empty list.

Often it's useful to have a default instead. Let's imagine we have a
default search query, ``all`` that should be used if no ``text``
parameter is supplied (instead of ``None``). We make a default
available by supplying a default value in the ``document_search``
function::

  @app.model(model=DocumentCollection, path='search')
  def document_search(text='all'):
      return DocumentCollection(text)

Note that defaults have no meaning for path variables, because for the
path to be resolved in the first place a variable will be found; path
variables cannot be omitted. They can be used as type hints however;
we'll talk more about those soon.

Like with path variables, you can have as many URL parameters as you
want.

Linking
-------

To create a link to a model, we can call :meth:`morepath.Request.link`
in our view code. At that point the model is examined to retrieve the
variables so that the path can be constructed.

Here is a simple case involving ``Document`` again::

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

The view at ``/document/foo/link`` will produce the link
``/document/foo``. That's the right one!

So, it constructs a link to the document itself. This view is not very
useful, but the principle is the same everywhere in any view: as long
as we have a ``Document`` instance we can create a link to it using
``request.link()``.

You can also give ``link`` a name to link to a named view. Here's a
``link2`` view creates a  link to the ``link`` view::

  @app.view(model=Document, name='link2')
  def document_self_link(request, model):
      return request.link(model, name='link')

So the view ``document/foo/link2`` will produce the link
``document/foo/link``.

Linking with path variables
---------------------------

How does the ``request.link`` code know what the value of the
``{name}`` variable should be so that the link can be constructed?  In
this case this happened automatically: the value of the ``name``
attribute of ``Document`` is assumed to be the one that goes into the
link.

This automatic rule won't work everywhere, however. Perhaps an
attribute with a different name is used, or a more complicated method
is used to construct the name. For those cases we can take over and
supply a custom ``variables`` function that knows how to construct the
variables needed to construct the link from the model.

The variables function gets the model as a single argument and needs
to return a dictionary. The keys should be the variable names used in
the path or URL parameters, and the values should be the values as
extracted from the model.

As an example, here is the ``variables`` function for the ``Document``
case made explicit::

  @app.model(model=Document, path='document/{name}',
             variables=lambda model: dict(name=model.name))
  def get_document(name):
      return query_document_by_name(name)

Or to spell it out without the use of ``lambda``::

  def document_variables(model):
      return dict(name=model.name)

  @app.model(model=Document, path='document/{name}',
             variables=document_variables)
  def get_document(name):
      return query_document_by_name(name)

Let's change ``Document`` so that the name is stored in the ``id``
attribute::

  class DifferentDocument(object):
      def __init__(self, name):
          self.id = name

Our automatic ``variables`` won't cut it anymore, so we have to be explicit::
attribute, we can do this::

  @app.model(model=DifferentDocument, path='document/{name}',
             variables=lambda model: dict(name=model.id))
  def get_document(name):
      return query_document_by_name(name)

All we've done is adjust the ``variables`` function to take
``model.id``.

Getting variables works for multiple variables too of course. Here's
the explicit ``variables`` for the ``VersionedDocument`` case that
takes multiple variables::

  @app.model(model=VersionedDocument,
             path='versioned_document/{name}-{version}',
             variables=lambda model: dict(name=model.name,
                                          version=model.version))
  def get_versioned_document(name, version):
      return query_versioned_document(name, version)

Linking with URL parameters
---------------------------

Linking works the same way for URL parameters as it works for path
variables.

Here's a ``get_model`` that takes the document name as a URL
parameter, using an implicit ``variables``::

  @app.model(model=Document, path='document')
  def get_document(name):
      return query_document_by_name(name)

Now we add back the same ``self_link`` view as we had before::

  @app.view(model=Document, name='link')
  def document_self_link(request, model):
      return request.link(model)

Here's ``get_document`` with an explicit ``variables``::

  @app.model(model=Document, path='document',
             variables=lambda model: dict(name=model.name))
  def get_document(name):
      return query_document_by_name(name)

i.e. exactly the same as for the path variable case.

Let's look at a document exposed on this URL::

  /document?name=foo

Then the view ``document/link?name=foo`` will construct the link::

  /document?name=foo

The ``document/link?name=foo`` is interesting: the ``name=foo``
parameters are added to the end, but they are used by the
``get_document`` function, *not* by its views. Here's ``link2`` again
to further demonstrate this behavior::

  @app.view(model=Document, name='link2')
  def document_self_link(request, model):
      return request.link(model, name='link')

When we now go to ``document/link2?name=foo`` we get the link
``document/link?name=foo``.

Type hints
----------

So far we've only dealt with variables that have string values. But
what if we want to use other types for our variables, such as ``int``
or ``datetime``? What if we have a record that you obtain by an
``int`` id, for instance? Given some ``Record`` class that
has an ``int`` id like this::

  class Record(object):
      def __init__(self, id):
          self.id = id

We could do this to expose it::

  @app.model(model=Record, path='record/{id}')
  def get_record(id):
      try:
          id = int(id)
      except ValueError:
          return None
      return record_by_id(id)

But Morepath offers a better way. We can tell Morepath we expect an
int and only an int, and if something else is supplied, the path
should not match. Here's how::

  @app.model(model=Record, path='record/{id}')
  def get_record(id=0):
      return record_by_id(id)

We've added a default parameter (``id=0``) here that Morepath will use
as an indication that only an int is expected. Morepath will now
automatically convert ``id`` to an int before it enters the
function. It will also give a ``404 Not Found`` response for URLs that
don't have an int. So it will accept ``/record/100`` but give a 404
for ``/record/foo``.

Let's examine the same case for an ``id`` URL parameter::

  @app.model(model=Record, path='record')
  def get_record(id=0):
      return record_by_id(id)

This responds to an URL like this ``/record?id=100``, but will reject
``/record/id=foo`` as ``foo`` cannot be converted to an int. It will
reject a request with the latter path with a ``400 Bad Request``
error.

By supplying a default for a URL parameter we've accomplished two in
one here, as it's a good idea to supply defaults for URL parameters
anyway, as that makes them properly optional.

Conversion
----------

Sometimes simple type hints are not enough. What if multiple possible
string representations for something exist? Let's examine the case of
:class:`datetime.date`.

We could represent it as a string in ISO 8601 format as returned by
the :meth:`datetime.date.isoformat` method, i.e. ``2014-01-15`` for
the 15th of january 2014. But we could also use another
representation, say ``15/01/2014``. (ISO format is the default
interpretation used by Morepath.)

Let's first see how a string with an ISO date can be decoded
(deserialized, loaded) into a ``date`` object::

  from datetime import date
  from time import mktime, strptime

  def date_decode(s):
      return date.fromtimestamp(mktime(strptime(s, '%Y-%m-%d')))

We can try it out::

  >>> date_decode('2014-01-15')
  datetime.date(2014, 1, 15)

Note that this function will raise a ``ValueError`` if we give it a
string that cannot be converted into a date::

  >>> date_decode('blah')
  Traceback (most recent call last):
     ...
  ValueError: time data 'blah' does not match format '%Y-%m-%d'

This is a general principle of decode: a decode function can fail and
if it does it should raise a ``ValueError``.

We also specify how to encode (serialize, dump) a ``date`` object back
into a string::

  def date_encode(d):
      return d.isoformat()

We can try it out too::

  >>> date_encode(date(2014, 1, 15))
  '2014-01-15'

A encode function should never fail, if at least presented with input
of the right type, in this case a ``date`` instance.

.. sidebar:: Inverse

  To help you write these functions, note that they're the inverse each
  other, so these equality are both True. For any string ``s`` that can
  be decoded, this is true::

    encode(decode(s)) == s

  And for any object that can be encoded, this is true::

    decode(encode(o)) == o

  The output of decode should always be input for encode, and the
  output of encode should always be input for decode.

Now that we have our ``date_decode`` and ``date_encode`` functions, we can
wrap them in an :class:`morepath.Converter` object::

  date_converter = morepath.Converter(decode=date_decode, encode=date_encode)

Let's now see how we can use ``date_converter``.

We have some kind of ``Records`` collection that can be parameterized
with ``start`` and ``end`` to select records in a date range::

  class Records(object):
     def __init__(self, start, end):
        self.start = start
        self.end = end

     def query(self):
        return query_records_in_date_range(self.start, self.end)

We expose it to the web::

  @app.model(model=Records, path='records',
             converters=dict(start=date_converter, end=date_converter))
  def get_records(start, end):
      return Records(start, end)

We also add a simple view that gives us comma-separated list of
matching record ids::

  @app.view(model=Records):
  def records_view(request, model):
      return ', '.join([str(record.id) for record in self.query()])

We can now go to URLs like this::

   /records?start=2011-01-10&end=2011-02-15

The ``start`` and ``end`` URL parameters will now be decoded into
``date`` objects, which get passed into ``get_records``. And when you
generate a link to a ``Records`` object, the ``start`` and ``end``
dates are encoded into strings.

What happens when a decode raises a ``ValueError``, i.e. improper
dates were passed in? In that case, the URL parameters cannot be
decoded properly, and Morepath will return a ``400 Bad Request``
response.

You can also use encode and decode for arguments used in a path::

  @app.model(model=Day, path='day/{d}', converters=dict(d=date_converter))
  def get_day(d):
      return Day(d)

This allows URls like this::

  /day/2011-01-10

When you pass in a broken date, like ``/day/foo``, a ``ValueError`` is
raised by the date decoder, and a ``404 not Found`` response is given
by the server: the URL does not resolve to a model.

Default converters
------------------

Before we said Morepath uses ISO format dates as the default. You can
register a default ``Converter`` instance for a type using the
``converter`` decorator::

  @app.converter(type=date)
  class Converter(object):
      @staticmethod
      def decode(s):
          return date.fromtimestamp(mktime(strptime(s, '%Y-%m-%d')))

      @staticmethod
      def encode(d):
          return d.isoformat()

Now Morepath will recognize type hints in default arguments::

  @app.model(model=Day, path='day/{d}')
  def get_day(d=date(2011, 1, 1)):
      return Day(d)

Morepath now knows you want to use the converter registered for
``date`` in to convert the ``d`` variable.

Required
--------

Sometimes you may want a URL parameter to be required: when the URL
parameter is missing, it's an error and a ``400 Bad Request`` should
be returned. You can do this by passing in a ``required`` argument
to the model decorator::

  @app.model(model=Record, path='record', required=['id'])
  def get_record(id):
      return query_record(id)

Normally when the ``id`` URL parameter is missing, the ``None`` value
is passed into ``get_record`` (if there is no default). But since we
made ``id`` required, ``400 Bad Request`` will be issued if ``id`` is
missing now. ``required`` only has meaning for URL parameters; path
variables are always present if the path matches at all.
