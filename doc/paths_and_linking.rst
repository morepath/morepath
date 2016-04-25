Paths and Linking
=================

Introduction
------------

Morepath lets you publish model classes on paths using Python
functions. It also lets you create links to model instances. To be
able do so Morepath needs to be told what variables there are in the
path in order to find the model object, and how to find these
variables again in the model object in order to construct a link to
it.

Paths
-----

.. sidebar:: Overlapping paths

  Morepath lets you define multiple overlapping paths::

    @App.path(model=Item, path='items/{id}')
    def get_item(id):
       ...

    @App.path(model=ItemDetail, path='items/{id}/details/{detail_id}')
    def get_item_detail(id, detail_id):
       ...

  If you have overlapping paths, you need to name the variable names
  the same in the overlapping part of the paths, otherwise Morepath
  reports a configuration conflict. So you can't have this::

    @App.path(model=Item, path='items/{id}')
    def get_item(id):
       ...

    @App.path(model=ItemDetail, path='items/{item_id}/details/{detail_id}')
    def get_item_detail(item_id, detail_id):
       ...

  Morepath reports an error in this case, as ``{id}`` and
  ``{item_id}`` overlap but are different variable names.

Let's assume we have a model class ``Overview``::

  class Overview(object):
      pass

Here's how we could expose it to the web under the path ``overview``::

  @App.path(model=Overview, path='overview')
  def get_overview():
      return Overview()

And let's give it a default view so we can see it when we go to its
URL::

  @App.view(model=Overview)
  def overview_default(self, request):
      return "Overview"

No variables are involved yet: they aren't in the ``path`` and the
``get_overview`` function takes no arguments.

Let's try a single variable now. We have a class ``Document``::

  class Document(object):
      def __init__(self, name):
          self.name = name

Let's expose it to the web under ``documents/{name}``::

  @App.path(model=Document, path='documents/{name}')
  def get_document(name):
      return query_document_by_name(name)

  @App.view(model=Document)
  def document_default(self, request):
      return "Document: " + self.name

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

  @App.path(model=VersionedDocument,
            path='versioned_documents/{name}-{version}')
  def get_versioned_document(name, version):
      return query_versioned_document(name, version)

  @App.view(model=VersionedDocument)
  def versioned_document_default(self, request):
      return "Versioned document: %s %s" % (self.name, self.version)

The rule is that all variables declared in the path can be used as
arguments in the model function.

URL query parameters
--------------------

What if we want to use URL parameters to expose models? That is
possible too. Let's look at the ``Document`` case first::

  @App.path(model=Document, path='documents')
  def get_document(name):
      return query_document_by_name(name)

``get_document`` has an argument ``name``, but it doesn't appear in
the path. This argument is now taken to be a URL parameter. So, this
exposes URLs of the type ``documents?name=foo``. That's not as nice as
``documents/foo``, so we recommend against parameters in this case:
you should use paths to identify something.

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

  @App.path(model=DocumentCollection, path='search')
  def document_search(text):
      return DocumentCollection(text)

To be able to see something, we add a view that returns a comma
separated string with the names of all matching documents::

  @App.view(model=DocumentCollection)
  def document_collection_default(self, request):
      return ', '.join([document.name for document in self.search()])

As you can see it uses the ``DocumentCollection.search`` method.

Unlike path variables, URL parameters can be omitted, i.e. we can have
a plain ``search`` path without a ``text`` parameter. In that case
``text`` has the value ``None``. The ``search`` method has code to
handle this special case: it returns the empty list.

Often it's useful to have a default instead. Let's imagine we have a
default search query, ``all`` that should be used if no ``text``
parameter is supplied (instead of ``None``). We make a default
available by supplying a default value in the ``document_search``
function::

  @App.path(model=DocumentCollection, path='search')
  def document_search(text='all'):
      return DocumentCollection(text)

Note that defaults have no meaning for path variables, because
whenever a path is resolved, all variables in it have been found. They
can be used as type hints however; we'll talk more about those soon.

Like with path variables, you can have as many URL parameters as you
want.

Extra URL query parameters
--------------------------

URL parameters are matched with function arguments, but it could be
you're interested in an arbitrary amount of extra URL parameters. You
can specify that you're interested in this by adding an
``extra_parameters`` argument::

  @App.path(model=DocumentCollection, path='search')
  def document_search(text='all', extra_parameters):
      return DocumentCollection(text, extra_parameters)

Now any additional URL parameters are put into the
``extra_parameters`` dictionary. So, ``search?text=blah&a=A&b=B`` would
match ``text`` with the ``text`` parameter, and there would be an
``extra_parameters`` containing ``{'a': 'A', 'b': 'B'}``.

``extra_parameters`` can also be useful for the case where the name of
the parameter is not a valid Python name (such as ``@foo``) -- you can
still receive such parameters using ``extra_parameters``.

Linking
-------

To create a link to a model, we can call :meth:`morepath.Request.link`
in our view code. At that point the model object is examined to
retrieve the variables so that the path can be constructed.

Here is a simple case involving ``Document`` again::

  class Document(object):
      def __init__(self, name):
          self.name = name

  @App.path(model=Document, path='documents/{name}')
  def get_document(name):
      return query_document_by_name(name)

We add a named view called ``link`` that links to the document itself::

  @App.view(model=Document, name='link')
  def document_self_link(self, request):
      return request.link(self)

The view at ``/documents/foo/link`` produces the link
``/documents/foo``. That's the right one!

So, it constructs a link to the document itself. This view is not very
useful, but the principle is the same everywhere in any view: as long
as we have a ``Document`` instance we can create a link to it using
``request.link()``.

You can also give ``link`` a name to link to a named view. Here's a
``link2`` view creates a  link to the ``link`` view::

  @App.view(model=Document, name='link2')
  def document_self_link(self, request):
      return request.link(self, name='link')

So the view at ``/documents/foo/link2`` produces the link
``/documents/foo/link``.

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

The variables function gets the model object as a single argument and
needs to return a dictionary. The keys should be the variable names
used in the path or URL parameters, and the values should be the
values as extracted from the model.

As an example, here is the ``variables`` function for the ``Document``
case made explicit::

  @App.path(model=Document, path='documents/{name}',
            variables=lambda obj: dict(name=obj.name))
  def get_document(name):
      return query_document_by_name(name)

Or to spell it out without the use of ``lambda``::

  def document_variables(obj):
      return dict(name=obj.name)

  @App.path(model=Document, path='documents/{name}',
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

  @App.path(model=DifferentDocument, path='documents/{name}',
            variables=lambda obj: dict(name=obj.id))
  def get_document(name):
      return query_document_by_name(name)

All we've done is adjust the ``variables`` function to take
``model.id``.

Getting variables works for multiple variables too of course. Here's
the explicit ``variables`` for the ``VersionedDocument`` case that
takes multiple variables::

  @App.path(model=VersionedDocument,
            path='versioned_documents/{name}-{version}',
            variables=lambda obj: dict(name=obj.name,
                                       version=obj.version))
  def get_versioned_document(name, version):
      return query_versioned_document(name, version)

If you have ``extra_parameters``, the default variables expects that
``extra_parameters`` to exist as an attribute on the object, but you
can write a custom ``variables`` that retrieves this dictionary from
the object in some other way::

  @App.path(model=SearchResults,
            path='search',
            variables=lambda obj: dict(text=obj.search_text,
                                       extra_parameters=obj.get_extra()))
  def get_search_results(text, extra_parameters):
      ...

Linking with URL query parameters
---------------------------------

Linking works the same way for URL parameters as it works for path
variables.

Here's a ``get_model`` that takes the document name as a URL
parameter, using an implicit ``variables``::

  @App.path(model=Document, path='documents')
  def get_document(name):
      return query_document_by_name(name)

Now we add back the same ``self_link`` view as we had before::

  @App.view(model=Document, name='link')
  def document_self_link(self, request):
      return request.link(self)

Here's ``get_document`` with an explicit ``variables``::

  @App.path(model=Document, path='documents',
            variables=lambda obj: dict(name=obj.name))
  def get_document(name):
      return query_document_by_name(name)

i.e. exactly the same as for the path variable case.

Let's look at a document exposed on this URL::

  /documents?name=foo

Then the view ``documents/link?name=foo`` constructs the link::

  /documents?name=foo

The ``documents/link?name=foo`` is interesting: the ``name=foo``
parameters are added to the end, but they are used by the
``get_document`` function, *not* by its views. Here's ``link2`` again
to further demonstrate this behavior::

  @App.view(model=Document, name='link2')
  def document_self_link(self, request):
      return request.link(self, name='link')

When we now go to ``documents/link2?name=foo`` we get the link
``/documents/link?name=foo``.

Prefixing links with a base URL
-------------------------------

By default, :meth:`morepath.Request.link` generates links as fully
qualified URLs using the ``HOST`` header and the given protocol
(``http``, ``https``), for instance::

   http://localhost/document

You can use the :meth:`morepath.App.link_prefix` decorator to override
this behavior. For example, if you *do* not want to add the full
hostname (in fact the behavior of Morepath before version 0.9), you
can write::

  @App.link_prefix()
  def simple_link_prefix(request):
      return ''

The ``link_prefix`` function is only called once per request per app,
during the first call to :meth:`morepath.Request.link` for an
app. After this it is cached for the rest of the duration of that
request.

Linking to external applications
--------------------------------

As a more advanced use case for ``link_prefix``, you can use it to
represent an application that is completely external, just for
the purposes of making it easier to create a link to it.

Let's say we want to be able to link to documents on the external site
``http://example.com``, and that these documents live on URLs like
``http://example.com/documents/{id}``.

We can create a model for such an external document first::

  class ExternalDocument(object):
      def __init__(self, id):
          self.id = id

And declare the path space of the external site::

  @ExternalApp.path(model=ExternalDocument, path='/documents/{id}')
  def get_external_document(id):
      return ExternalDocument(id)

We don't need to declare any views for ``ExternalDocument``;
``ExternalApp`` only exists to let you generate a link to the
``example.com`` external site more easily.

Now we want ``request.link(ExternalDocument('foo'))`` to result in the
link ``http://example.com/documents/foo``. All we need to do is to
declare a special ``link_prefix`` for the external app where we
hardcode ``http://example.com``::

  @ExternalApp.link_prefix()
  def simple_link_prefix(request):
      return 'http://example.com'

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

  @App.path(model=Record, path='records/{id}')
  def get_record(id):
      try:
          id = int(id)
      except ValueError:
          return None
      return record_by_id(id)

But Morepath offers a better way. We can tell Morepath we expect an
int and only an int, and if something else is supplied, the path
should not match. Here's how::

  @App.path(model=Record, path='records/{id}')
  def get_record(id=0):
      return record_by_id(id)

We've added a default parameter (``id=0``) here that Morepath uses as
an indication that only an int is expected. Morepath will now
automatically convert ``id`` to an int before it enters the
function. It also gives a ``404 Not Found`` response for URLs that
don't have an int. So it accepts ``/records/100`` but gives a 404 for
``/records/foo``.

Let's examine the same case for an ``id`` URL parameter::

  @App.path(model=Record, path='records')
  def get_record(id=0):
      return record_by_id(id)

This responds to an URL like ``/records?id=100``, but rejects
``/records/id=foo`` as ``foo`` cannot be converted to an int. It
rejects a request with the latter path with a ``400 Bad Request``
error.

By supplying a default for a URL parameter we've accomplished two in
one here, as it's a good idea to supply defaults for URL parameters
anyway, as that makes them properly optional.

Conversion
----------

Sometimes simple type hints are not enough. What if multiple possible
string representations for something exist in the same application?
Let's examine the case of :class:`datetime.date`.

We could represent it as a string in ISO 8601 format as returned by
the :meth:`datetime.date.isoformat` method, i.e. ``2014-01-15`` for
the 15th of january 2014. We could also use ISO 8601 compact format,
namely ``20140115`` (and this what Morepath defaults to). But we could
also use another representation, say ``15/01/2014``.

Let's first see how a string with an ISO compact date can be decoded
(deserialized, loaded) into a ``date`` object:

.. testcode::

  from datetime import date
  from time import mktime, strptime

  def date_decode(s):
      return date.fromtimestamp(mktime(strptime(s, '%Y%m%d')))

We can try it out:

  >>> date_decode('20140115')
  datetime.date(2014, 1, 15)

Note that this function raises a ``ValueError`` if we give it a string
that cannot be converted into a date:

  >>> date_decode('blah')                # doctest: -IGNORE_EXCEPTION_DETAIL -ELLIPSIS
  Traceback (most recent call last):
     ...
  ValueError: time data 'blah' does not match format '%Y%m%d'

This is a general principle of decode: a decode function can fail and
if it does it should raise a ``ValueError``.

We also specify how to encode (serialize, dump) a ``date`` object back
into a string:

.. testcode::

  def date_encode(d):
      return d.strftime('%Y%m%d')

We can try it out too:

  >>> date_encode(date(2014, 1, 15))
  '20140115'

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

  @App.path(model=Records, path='records',
            converters=dict(start=date_converter, end=date_converter))
  def get_records(start, end):
      return Records(start, end)

We also add a simple view that gives us comma-separated list of
matching record ids::

  @App.view(model=Records)
  def records_view(self, request):
      return ', '.join([str(record.id) for record in self.query()])

We can now go to URLs like this::

   /records?start=20110110&end=20110215

The ``start`` and ``end`` URL parameters now are decoded into ``date``
objects, which get passed into ``get_records``. And when you generate
a link to a ``Records`` object, the ``start`` and ``end`` dates are
encoded into strings.

What happens when a decode raises a ``ValueError``, i.e. improper
dates were passed in? In that case, the URL parameters cannot be
decoded properly, and Morepath returns a ``400 Bad Request`` response.

You can also use encode and decode for arguments used in a path::

  @App.path(model=Day, path='days/{d}', converters=dict(d=date_converter))
  def get_day(d):
      return Day(d)

This publishes the model on a URL like this::

  /days/20110101

When you pass in a broken date, like ``/days/foo``, a ``ValueError`` is
raised by the date decoder, and a ``404 not Found`` response is given
by the server: the URL does not resolve to a model.

Default converters
------------------

Morepath has a number of default converters registered; we already saw
examples for int and strings. Morepath also has a default converter
for ``date`` (compact ISO 8601, i.e. ``20131231``) and ``datetime``
(i.e. ``20131231T23:59:59``).

You can add new default converters for your own classes, or override
existing default behavior, by using the
:meth:`morepath.App.converter` decorator. Let's change the default
behavior for ``date`` in this example to use ISO 8601 *extended* format,
so that dashes are there to separate the year, month and day,
i.e. ``2013-12-31``::

  def extended_date_decode(s):
      return date.fromtimestamp(mktime(strptime(s, '%Y-%m-%d')))

  def extended_date_encode(d):
      return d.strftime('%Y-%m-%d')

  @App.converter(type=date)
  def date_converter():
      return Converter(extended_date_decode, extended_date_encode)

Now Morepath understand type hints for ``date`` differently::

  @App.path(model=Day, path='days/{d}')
  def get_day(d=date(2011, 1, 1)):
      return Day(d)

has models published on a URL like::

  /days/2013-12-31

Type hints and converters
-------------------------

You may have a situation where you don't want to add a default
argument to indicate the type hint, but you know you want to use a
default converter for a particular type. For those cases you
can pass the type into the ``converters`` dictionary as a shortcut::

  @App.path(model=Day, path='days/{d}', converters=dict(d=date))
  def get_day(d):
      return Day(d)

The variable ``d`` is now interpreted as a ``date``. Morepath uses
whatever converter that was registered for that type.

List converters
---------------

What if you want to allow a list of parameters instead of just a single
one? You can do this by wrapping the converter or type in the ``converters``
dictionary in a list::

  @App.path(model=Days, path='days', converters=dict(d=[date]))
  def get_days(d):
      return Days(d)

Now the ``d`` parameter will be interpreted as a list. This means URLs
like this are accepted::

  /days?d=2014-01-01

  /days?d=2014-01-01&d=2014-01-02

  /days

For the first case, ``d`` is a list with one date item, in the second
case, ``d`` has 2 items, and in the third case the list ``d`` is
empty.

get_converters
--------------

Sometimes you only know what converters are available at run-time;
this particularly relevant if you want to supply converters for the
values in ``extra_parameters``. You can supply the converters using
the special ``get_converters`` parameter to ``@app.path``::

  def my_get_converters():
      return { 'something': int }

  @App.path(path='search', model=SearchResults,
            get_converters=my_get_converters)
  ...

Now if there is a parameter (or extra parameter) called ``something``, it
is converted to an ``int``.

You can combine ``converters`` and ``get_converters``. If you use
both, ``get_converters`` will override any converters also defined in
the static ``converters``. This can also be useful for dealing with
URL parameters that are not valid Python names, such as ``@foo`` or
``foo[]``; these can still be converted using ``get_converters``.

Required
--------

Sometimes you may want a URL parameter to be required: when the URL
parameter is missing, it's an error and a ``400 Bad Request`` should
be returned. You can do this by passing in a ``required`` argument
to the model decorator::

  @App.path(model=Record, path='records', required=['id'])
  def get_record(id):
      return query_record(id)

Normally when the ``id`` URL parameter is missing, the ``None`` value
is passed into ``get_record`` (if there is no default). But since we
made ``id`` required, ``400 Bad Request`` will be issued if ``id`` is
missing now. ``required`` only has meaning for URL parameters; path
variables are always present if the path matches at all.

Absorbing
---------

In some special cases you may want a path to match all sub-paths,
absorbing them. This can be useful if you are writing a server backend
to a client side application that does routing on the client using the
HTML 5 history API -- the server needs to handle catch all subpaths in
that case and send them back to the client, where they can be handled
by the client-side router.

You can do this using the special ``absorb`` argument to the path
decorator, like this::

  class Model(object):
      def __init__(self, absorb):
          self.absorb = absorb

  @App.path(model=Model, path='start', absorb=True)
  def get_foo(absorb):
      return Model(absorb)

As you can see, if you use ``absorb`` then a special ``absorb``
argument is passed into the model factory function.

Now the ``start`` path matches all of its sub-paths. So for this
path::

  /start/foo/bar/baz

``model.absorb`` is ``foo/bar/baz``.

It also matches if there is no sub-path::

  /start

``model.absorb`` is the empty string ``''``.

Note that you cannot use view names with a path that absorbs; only a
default view with the empty name. View names are absorbed along with
the rest of the path.

Note also that you cannot define an explicit path under an absorbed
path -- this is ignored. This means that the following additional code
has no effect::

  @App.path(model=Foo, path='start/extra')

You can still generate a link to a model that is under an
absorbed path -- it uses the value of the ``absorb`` variable.

Linking with the model class
----------------------------

Instead of using :meth:`morepath.Request.link` you can also construct
links using :meth:`morepath.Request.class_link`. You can use this for
optimization purposes when creating an instance to link to would be
relatively expensive; if you do have the instance it's generally
easier to just link to that instead using `request.link`.

To use `request.class_link` you give the model *class* instead of an
instance, and also provide a dictionary of variables to use to
construct the link::

  @App.view(model=Document, name='class_link')
  def document_self_link(self, request):
      return request.class_link(Document, variables={'name': 'Document name'})

The variables are used in the same way as for `request.link`, so
additional parameters listed in the path function are interpreted as
URL parameters.

Warning: `request.class_link` does *NOT* obey the `defer_links`
directive, as this relies on the instance of what is being linked to
in order to determine the application to which it defers.

Proxy support
-------------

If you have a Morepath application that sits behind a trusted proxy
that sets the `Forwarded header`_, then you want links generated by
Morepath take this header into account. To do this, you can make your
project depend on the `more.forwarded`_ extension. After you have it
installed, you can subclass your app from
``more.forwarded.ForwardedApp`` to make your app proxy-aware. Note
that you only need to do this for the root app, not for any apps
mounted into it.

You should *only* use this extension if you know you are behind a
trusted proxy that indeed sets the ``Forwarded`` header. This because
otherwise you could expose your application to attacks that affect
link generation through the Forwarded header.

.. _`more.forwarded`: http://pypi.python.org/pypi/more.forwarded

.. _`Forwarded header`: http://tools.ietf.org/html/rfc7239
