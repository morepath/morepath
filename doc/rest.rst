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
:meth:`morepath.App.view`. This also lets you pass in a ``render``
function that lets you specify how to render the return value of the
view function as a :class:`morepath.Response`. If you use JSON, for
convenience you can use :meth:`morepath.App.json` has a JSON
render function baked in.

We could for instance have a ``Document`` model in our application:

.. testcode::

  class Document(object):
      def __init__(self, title, author, content):
          self.title = title
          self.author = author
          self.content = content

We can expose it on a URL:

.. testsetup::

  import morepath
  class App(morepath.App):
      pass

.. testcode::

  @App.path(model=Document, path='documents/{id}')
  def get_document(id=0):
     return document_by_id(id)

We assume here that a ``document_by_id()`` function exists that
returns a ``Document`` instance by integer id from some database, or
``None`` if the document cannot be found. Any way to get your model
instance is fine. We use ``id=0`` to tell Morepath that ids should be
converted to integers, and to with a ``BadRequest`` if that is not
possible.

Now we need a view that exposes the resource to JSON:

.. testcode::

  @App.json(model=Document)
  def document_default(self, request):
      return {
        'type': 'document',
        'id': self.id,
        'title': self.title,
        'author': self.author,
        'content': self.content
      }

Modeling as resources
---------------------

Modeling a web service as multiple resources comes pretty naturally to
Morepath. You think carefully about how to place models in the URL
space and then expose them using :meth:`morepath.App.path`. Each model
class can only be exposed on a single URL (per app), which gives them
a canonical URL automatically.

A collection resource could be modelled like this:

.. testcode::

  class DocumentCollection(object):
      def __init__(self):
          self.documents = []
          self.id_counter = 0

      def add(self, doc):
          doc.id = self.id_counter
          self.id_counter += 1
          self.documents.append(doc)
          return doc

We now want to expose this collection to a URL path ``/documents``. We
want:

* when you ``GET`` ``/documents`` we want to get the ids documents in the
  collection.

* when you ``POST`` to ``/documents`` with a JSON body we want to add
  it to the collection.

Here is how we can make ``documents`` available on a URL:

.. testcode::

  documents = DocumentCollection()

  @App.path(model=DocumentCollection, path='documents')
  def get_document_collection():
      return documents

When someone accesses ``/documents`` they should get a JSON structure
which includes ids of all documents in the collection. Here's how to
do that (for ``GET``, the default):

.. testcode::

  @App.json(model=DocumentCollection)
  def document_collection_default(self, request):
      return {
         'type': 'document_collection',
         'ids': [doc.id for doc in self.documents]
      }

We also want to allow people to ``POST`` new documents (as a JSON POST
body):

.. testcode::

  @App.json(model=DocumentCollection, request_method='POST')
  def document_collection_post(self, request):
      json = request.json
      result = self.add(Document(title=json['title'],
                                 author=json['author'],
                                 content=json['content']))
      return request.view(result)

We use :meth:`Request.view` to return the JSON structure for the added
document again. This is handy as it includes the ``id`` field.

HTTP response status codes
--------------------------

When a view function returns normally, Morepath automatically sets the
response HTTP status code to ``200 Ok``.

When you try to access a URL that cannot be routed to a model because
no path exists, or because the function involved returns ``None``, or
because the view cannot be found, a ``404 Not Found`` error is raised.

If you access a URL that does exist but with a request method that is
not supported, a ``405 Method Not Allowed`` error is raised.

What if the user sends the wrong information to a view? Let's consider
the ``POST`` view again:

.. testcode::

  @App.json(model=DocumentCollection, request_method='POST')
  def document_collection_post(self, request):
      json = request.json
      result = self.add(Document(title=json['title'],
                                 author=json['author'],
                                 content=json['content']))
      return request.view(result)

What if the structure of the JSON submitted is not a valid document
but contains some other information, or misses essential information?
We should reject it if so. We can do this by raising a HTTP error
ourselves. WebOb, the request/response library upon which Morepath is
built, defines a set of HTTP exception classes :mod:`webob.exc` that
we can use:

.. testcode::

  @App.json(model=DocumentCollection, request_method='POST')
  def document_collection_post(self, request):
      json = request.json
      if not is_valid_document_json(json):
          raise webob.exc.HTTPUnprocessableEntity()
      result = self.add(Document(title=json['title'],
                                 author=json['author'],
                                 content=json['content']))
      return request.view(result)

.. sidebar:: What status code is right?

  There is some debate over what status code to pick for content that
  is submitted that can be parsed but is incorrect. Some REST
  implementations use ``400 Bad Request``, others use ``422
  Unprocessable Entity``. Morepath uses the latter by default, as
  we'll see in a bit.

Now we raise ``422 Unprocessable Entity`` when the submitted JSON body
is invalid, using a function ``is_valid_document_json`` that does the
checking. ``is_valid_document`` could look this:

.. testcode::

  def is_valid_document_json(json):
     if json['type'] != 'document':
        return False
     for name in ['title', 'author', 'content']:
        if name not in json:
           return False
     return True

``body_model``
--------------

Instead of checking the content for validity in the view, we can use
:meth:`App.load_json`:

.. testcode::

  @App.load_json()
  def load_json(json, request):
     if is_valid_document_json(json):
        return Document(title=json['title'],
                        author=json['author'],
                        content=json['content'])
     # fallback, just return plain JSON
     return json

Now we get a ``Document`` instance in :attr:`Request.body_obj`, so
we can simplify ``document_collection_post``:

.. testcode::

  @App.json(model=DocumentCollection, request_method='POST')
  def document_collection_post(self, request):
      if not isinstance(request.body_obj, Document):
         raise webob.exc.HTTPUnprocessableEntity()
      result = self.add(request.body_obj)
      return request.view(result)

To only match if ``body_obj`` is an instance of ``Document`` we can
use ``body_model`` on the view instead:

.. testcode::

  @App.json(model=DocumentCollection, request_method='POST', body_model=Document)
  def document_collection_post(self, request):
      result = self.add(request.body_obj)
      return request.view(result)

Now you get the ``422`` error for free if no matching ``body_model``
can be found. You can also create additional ``POST`` views for
``DocumentCollection`` that handle other types of JSON content this
way.

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

Morepath makes it easy to create hyperlinks, so we won't have to do
much. Before we had this for the collection view:

.. testcode::

  @App.json(model=DocumentCollection)
  def document_collection_default(self, request):
      return {
         'type': 'document_collection',
         'ids': [doc.id for doc in self.documents]
      }

We can change this so instead of ids, we return a list of document
URLs instead:

.. testcode::

  @App.json(model=DocumentCollection)
  def document_collection_default(self, request):
      return {
         'type': 'document_collection',
         'documents': [request.link(doc) for doc in self.documents],
      }

Now we've got HATEOAS: the collection links to the documents it
contains. The developers looking at the responses your web service
sends get a few clues about where to go next. Coupling is looser.

We have HATEOAS, so at last we got true REST. Why is hyperlinking so
often ignored? Why don't more systems implement HATEOAS? Perhaps
because they make linking to things too hard or too brittle. Morepath
instead makes it easy. Link away!

Compose from reusable apps
--------------------------

If you're going to create a larger RESTful web service, you should
start thinking about composing them from smaller applications. See
:doc:`app_reuse` for more information.
