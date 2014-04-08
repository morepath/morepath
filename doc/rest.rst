REST
====

Introduction
------------

.. sidebar:: How to think RESTful thoughts

  So what does it mean for a web service to be RESTful? It might help to
  remember this when thinking about REST:

    **client :: RESTful web service**

  is like:

    **human with browser :: well-designed multi-page web application**

  So if you have experience with developing good multi-page web
  applications, then you can apply this experience to REST web service
  design and you're off to a good start.

In this section we'll look at how you could go about implementing a
RESTful_ web service with Morepath.

REST stands for Representational State Transfer, and is a particular
way to design web services. We won't try to explain here *why* this
can be a good thing for you to do, just explain what is involved.

REST is not only useful for pure web services, but is also highly
relevant for web application development, especially when you are
building a single-page rich client application in JavaScript in the
web browser. It can be beneficial to organize the server-side
application as a RESTful web service.

Elements of REST
----------------

That's all rather abstract. Let's get more concrete. It's useful to
refer to the `Richardson Maturity Model for REST`_ in this context. In
REST we do the following:

* We uses HTTP as a transport system. What you use to communicate is
  typically JSON or XML, but it could be anything.

* We don't just use HTTP to tunnel method calls to a single
  URL. Instead, we model our web service as resources, each with their
  own URL, that we can interact with.

* We use HTTP methods meaningfully. Most importantly we use ``GET`` to
  retrieve information, and ``POST`` when we want to change
  information. Along with this we also use HTTP response status codes
  meaningfully.

* We have links between the resources. So, one resource points to
  another. A container resource could point to a link that you can
  ``POST`` to create a new sub resource in it, for instance, and may
  have a list of links to the resources in the container. See also
  HATEOAS_.

.. _RESTful: https://en.wikipedia.org/wiki/Representational_state_transfer

.. _`Richardson Maturity Model for REST`: http://martinfowler.com/articles/richardsonMaturityModel.html

.. _HATEOAS: https://en.wikipedia.org/wiki/HATEOAS

Morepath has features that help you create RESTful applications.

HTTP as a transport system
--------------------------

We don't really need to say much here, as Morepath is of course all
about HTTP in the end. Morepath lets you write a bare-bones view using
:meth:`morepath.AppBase.view`. This also lets you pass in a ``render``
function that lets you specify how to render the return value of the
view function as a :class:`morepath.Response`. If you use JSON, for
convenience you can use :meth:`morepath.AppBase.json` has a JSON
render function baked in.

We could for instance have a ``Document`` model in our application::

  class Document(object):
      def __init__(self, id, title, author, content):
          self.id = id
          self.title = title
          self.author = author
          self.content = content

We can expose it on a URL::

  @app.path(model=Document, path='documents/{id}')
  def get_document(id):
     return document_by_id(id)

We assume here that a ``document_by_id()`` function exists that
returns a ``Document`` instance by id from some database, or ``None``
if the document cannot be found. Any way to get your model instance is
fine.

Now we want a ``metadata`` resource that exposes its metadata as
JSON::

  @app.json(model=Document, name='metadata')
  def document_metadata(self, request):
      return {
        'id': self.id,
        'title': self.title,
        'author': self.author
      }

Modeling as resources
---------------------

Modeling a web service as multiple resources comes pretty naturally to
Morepath, as it's model-oriented in the first place. You can think
carefully about how to place models in the URL space and expose them
using :meth:`morepath.AppBase.path`. In Morepath each model class can
only be exposed on a single URL (per app), which gives them a
canonical URL automatically.

A collection resource could be modelled like this::

  class DocumentCollection(object):
      def __init__(self):
          self.documents = []

      def add(self, doc):
          self.documents.append(doc)

We now want to expose this collection to a URL path ``/documents``. We
want:

* a resource ``/documents`` to GET the ids of all documents in the
  collection.

* a resource ``/documents/add`` that lets you POST an ``id`` to it so that
  this document is added to the collection.

Here is how we could make ``documents`` available on a URL::

  documents = DocumentCollection()

  @app.path(model=DocumentCollection, path='documents')
  def documents_collection():
     return documents

When someone accesses ``/documents`` they should get a JSON structure which
includes ids of all documents in the collection. Here's how to do
that::

  @app.json(model=DocumentCollection)
  def collection_default(self, request):
      return {
         'type': 'document_collection',
         'ids': [doc.id for doc in self.documents]
      }

Then we want to allow people to POST the document id (as a URL
parameter) to the ``/documents/add`` resource::

  @app.json(model=DocumentCollection, name='add', request_method='POST')
  def collection_add_document(self, request):
      doc = document_by_id(request.args['id'])
      self.add(doc)
      return {}

We again use the ``document_by_id`` function. We also return an empty
JSON object in the response; not very useful, but in this simple view
we don't have anything more interesting to report when the POST
succeeds.

Note the use of ``request_method``, which we'll talk about
more next.

Note also that there are some things still missing: giving back a
proper response with status codes, and error handling when things go
wrong.

HTTP methods
------------

As you saw above, we've used ``request_method`` to make sure that
``/documents/add`` only works for ``POST`` requests.

By default, ``request_method`` is ``GET``, meaning that ``/documents``
only responds to a ``GET`` request, which is what we want. Let's
make it explicit::

  @app.json(model=DocumentCollection, request_method='GET')
  def collection_default(self, request):
      ...

What if we had defined our web service differently, and instead of
having a ``/documents/add`` we wanted to allow the POSTing of document
ids on ``/documents`` directly? Here's how you rewrite
``collection_add_document`` to be the view directly on
``/documents```::

  @app.json(model=DocumentCollection, request_method='POST')
  def collection_add_document(self, request):
      ...

It's just a matter of removing the ``name`` parameter so that it becomes
the default view on ``DocumentCollection``.

HTTP response status codes
--------------------------

When a view did its thing with success, Morepath automatically returns
the HTTP status code ``200``. When you try to access a URL that cannot
be routed to a model or a view, a ``404`` error is raised.

But what if the view did not manage to do something successfully? Let's
get back to this view::

  @app.json(model=DocumentCollection, name='add', request_method='POST')
  def collection_add_document(self, request):
      doc = document_by_id(request.args['id'])
      self.add(doc)
      return {}

What if there is no ``id`` parameter in the request? That's something
our application cannot handle: a bad request, status code 400.

.. sidebar:: What status code is right?

  There is some debate over what status code to pick for particular
  errors. Sometimes the HTTP specification is pretty clear, but in the
  case of a missing parameter, it's not. Status code 400 (Bad Request)
  while according to the HTTP specd more about the syntax of a request
  than its content, is still chosen by many implementers in case of
  errors like this.

  But no matter what kind of HTTP error you pick, how you cause them
  to happen is the same: just raise the appropriate exception.

WebOb, the request/response library upon which Morepath is built,
defines a set of HTTP exception classes :mod:`webob.exc` that we can
use. In this case we need :exc:`webob.exc.HTTPBadRequest`. We modify
our view so it is raised if there was no id::

  from webob.exc import HTTPBadRequest

  @app.json(model=DocumentCollection, name='add', request_method='POST')
  def collection_add_document(self, request):
      id = request.args.get('id')
      if id is None:
          raise HTTPBadRequest()
      doc = document_by_id(id)
      self.add(doc)
      return {}

We also want to deal with the situation where an id was given, but no
document with that id exists. Let's handle that with 400 Bad Request
too::

  @app.json(model=DocumentCollection, name='add', request_method='POST')
  def collection_add_document(self, request):
      id = request.args.get('id')
      if id is None:
          raise BadRequest()
      doc = document_by_id(id)
      if doc is None:
          raise BadRequest()
      self.add(doc)
      return {}

Linking: HATEOAS
----------------

We've now reached the point where many would say that this is a
RESTful web service. But in fact a vital ingredient is still missing:
hyperlinks. That ugly acronym HATEOAS_ thing.

.. sidebar:: Hyperlinks!

  Since hyperlinks are so commonly missing from web services that claim
  to be RESTful, we'll break our promise here not to motivate why REST
  is good, and have a brief discussion on why hyperlinking is a good
  idea.

  Without hyperlinks, a client is coupled to the server in two ways:

  * URLs: it needs to know what URLs the server exposes.

  * Data: it needs to know how to interpret the data coming from the
    server, and what data to send to the server.

  Now add HATEOAS and get true REST. Now the client is coupled to the
  server in only one way: data. It gets the URLs it needs from the
  data. We gain looser coupling between server and client: the server
  can change all its URLs and the client will continue to work.

  You may quibble and say the client still needs to know the original
  URL of the server to get started, and dig up all the other URLs from
  the data afterward. That's true -- but that's all that's
  needed. It's normal. Think again like how a human interacts with the
  web through the browser: you may use a search engine or bookmarks to
  get the initial URL of a site, and then you go to pages in that site
  by clicking links.

Morepath makes it very easy to create hyperlinks, so we won't
have to do much. Let's first modify our default ``GET`` view for
the collection so it also has a link to the ``add`` resource::

  @app.json(model=DocumentCollection)
  def collection_default(self, request):
      return {
         'type': 'document_collection',
         'ids': [doc.id for doc in self.documents],
         'add': request.link(documents, 'add')
      }

``documents``, if you can remember, is the instance of
``DocumentCollection`` we were working with, and we want
to link to its ``add`` view.

Let's make things more interesting though. Before we had the default
view for the collection return a list of document ids. We can change
this so we return a list of document URLs instead::

  @app.json(model=DocumentCollection)
  def collection_default(self, request):
      return {
         'type': 'document_collection',
         'documents': [request.link(doc) for doc in self.documents],
         'add': request.link(documents, 'add')
      }

Or perhaps better, include the id *and* the URL::

  @app.json(model=DocumentCollection)
  def collection_default(self, request):
      return {
         'type': 'document_collection',
         'documents': [dict(id=doc.id, link=request.link(doc))
                       for doc in self.documents],
         'add': request.link(documents, 'add')
      }

Now we've got HATEOAS: the collection links to the documents it
contains, and also to the ``add`` URL that can be used to add a new
document. The developers looking at the responses your web service
sends get a few clues about where to go next. Coupling is looser.

We got HATEOAS, so at last we got true REST. Why is hyperlinking so
often ignored? Why don't more systems implement HATEOAS? Perhaps
because they make linking to things too hard or too brittle. Morepath
instead makes it easy. Link away!

Compose from reusable apps
--------------------------

If you're going to create a larger RESTful web service, you should
start thinking about composing them from smaller applications. See
:doc:`app_reuse` for more information.
