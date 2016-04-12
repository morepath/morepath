A Review of the Web
===================

Morepath is a web framework. Here is a quick review of how the web
works, how applications can be built with it, and how Morepath fits.

.. _review-http-protocol:

HTTP protocol
-------------

HTTP_ is a protocol by which clients (such as web browsers) and
servers can communicate. The client sends a HTTP request, and the
server sends back a HTTP response. HTTP is extensible, and can be
extended with content types, new headers, and so on.

Version 1.1 of HTTP is most common on the web today. It is defined by
a bunch of specifications:

* `RFC7230 - HTTP/1.1: Message Syntax and Routing
  <http://tools.ietf.org/html/rfc7230>`_

* `RFC7231 - HTTP/1.1: Semantics and Content <http://tools.ietf.org/html/rfc7231>`_

* `RFC7232 - HTTP/1.1: Conditional Requests <http://tools.ietf.org/html/rfc7232>`_

* `RFC7233 - HTTP/1.1: Range Requests <http://tools.ietf.org/html/rfc7233>`_

* `RFC7234 - HTTP/1.1: Caching <http://tools.ietf.org/html/rfc7234>`_

* `RFC7235 - HTTP/1.1: Authentication
  <http://tools.ietf.org/html/rfc7235>`_

Luckily it's not necessary to understand the full details of these
specifications to develop a web application. We'll go into a basic
overview of relevant concepts in this document.

Morepath handles the HTTP protocol on the server side: creating a
response to incoming HTTP requests.

.. _HTTP: https://en.wikipedia.org/wiki/Hypertext_Transfer_Protocol

.. _review-web-browser:

Web browser
-----------

A web browser such as Firefox, Chrome and Internet Explorer uses the
HTTP protocol to talk to web servers.

A web browser is a type of *HTTP client*.

.. _review-web-server:

Web server
----------

A web server implements the HTTP protocol to respond to requests from
HTTP clients such as web browsers.

There are general web servers such as `Apache
<https://httpd.apache.org/>`_ and `Nginx <http://nginx.org/>`_. These
are programmable in various ways.

There are also more specific web servers that are geared at particular
tasks. Examples of these are `Waitress
<http://waitress.readthedocs.org>`_ and `Gunicorn
<http://gunicorn.org>`_ which are geared towards serving web
applications written in Python.

A web server is programmable in various ways. Morepath can plug into
web servers that implement the Python WSGI_ protocol.

.. _WSGI: https://en.wikipedia.org/wiki/Web_Server_Gateway_Interface

.. _review-web-application:

Web application
---------------

A web application is software that presents a user interface by means
of a web browser. The web browser is usually a visible piece of
software, but may also be embedded in other software, such as in
FirefoxOS.

A web application is loaded from a web server. After it is loaded it
can still interact with the web server (or other web servers). The web
server can implement part of the application logic and maintains the
application data.

The dynamic behavior of a web application used to be implemented
almost entirely by the server, but it is now also possible to
implement a large part of their behavior within the web browser
instead, using the JavaScript language.

Morepath code runs entirely on the server, but supports web
applications that want to implement a large part of their dynamic
behavior within the web browser.

.. _review-web-service:

Web service
-----------

A web service does not present a user interface to the user. A web
service instead presents an application programming interface (API) to
custom HTTP client software. The API is to this software what the UI
is to the user.

You can layer a full web application on top of a web service. Such
layering can result in looser coupling in the implementation, which
tends to increase the quality of the implementation.

Morepath helps developers to implement web services.

.. _review-custom-http-client:

Custom HTTP client
------------------

A web browser is one form of HTTP client, but other HTTP software can
be written in a variety of languages to talk to a web server
programmatically. This uses it as a web service.

JavaScript code in a web browser can also use the browser's facilities
to talk to the web server programmatically (a technique called AJAX),
and can thus serve as a custom HTTP client as well.

.. _review-framework:

Framework
---------

A library is reusable code that your code calls, whereas a framework
is reusable code that calls your code. "Don't call us, we'll call
you".

A framework aims to help you do particular tasks quickly; you only
need to fill in the details, and the framework handles the rest.

There is a gray area between library and framework. Morepath is mostly
a framework.

.. _review-server-web-framework:

Server web framework
--------------------

A framework that helps you program the behavior of a web
server. Morepath is a server web framework written in the Python
programming language.

.. _review-javascript:

JavaScript
----------

JavaScript_ is a programming language that is run in the browser. It
can use the web browser APIs (such as the DOM) to manipulate the web
page, get user input, or access the server programmatically (AJAX).

JavaScript can also be run on the server with Node.JS, but Morepath is
a Python web framework and does not make use of server-side
JavaScript.

Bower is a tool to help manage client-side JavaScript code.

.. _JavaScript: https://en.wikipedia.org/wiki/JavaScript

.. _review-bower:

Bower
-----

A popular way to install client-side JavaScript (and CSS) code is to
use the Bower_ package management tool. By using a package manager
installing and updating a collection of JavaScript libraries becomes
more easy than doing it by hand.

Morepath offers Bower integration, see: :doc:`more.static`.

.. _Bower: http://bower.io

.. _review-ajax:

AJAX
----

AJAX_ is a technique to access resources programmatically from a
browser application in JavaScript. These resources typically have a
JSON representation.

.. _AJAX: https://en.wikipedia.org/wiki/Ajax_%28programming%29

.. _review-client-web-framework:

Client web framework
--------------------

There are also client-side web frameworks that let you program the
behavior of a web browser, typically called "JavaScript MVC
framework". Examples of such are React, Ember and Angular.

Morepath supports client-side code that uses a client web framework,
but does not implement a client web framework itself. You can pick
whichever you want.

.. _review-wsgi:

WSGI
----

WSGI_ is a Python protocol by which Python code can be integrated with
a web server. WSGI can also be used to implement framework components
which are layered between application code and server.

A :class:`morepath.App` instance implements the WSGI protocol and can
therefore be integrated with a WSGI-compliant web server and WSGI
framework component.

.. _review-http-request:

HTTP request
------------

A HTTP request is a message a HTTP client sends to the server. The
server then returns a HTTP response.

The HTTP request contains a *URL path*, a *request method*, possibly a
*request body*, and various *headers* such as the *content type*.

A HTTP request in Morepath is made accessible programmatically as a
Python request object using the WebOb_ library. It is a
`class:`morepath.Request`, which is a subclass of
:class:`webob.request.BaseRequest`.

.. _WebOb: http://webob.org/

.. _review-http-response:

HTTP response
-------------

A HTTP response returns a representation of the resource indicated by
the path of the request as the *response body*. The response has a
*content type* which determines what representation is being sent. The
response also has a *status code* that indicates whether the request
could be handled, or the reason why a detailed response could not be
generated.

A lot of different representations exist. HTML is a very common one,
but for programmatic clients JSON is typically used.

Morepath lets you create a :class:`morepath.Response` object directly,
which is a subclass of :class:`webob.response.Response`, and return it
from a view function.

More conveniently you use a specialized view type
(:meth:`morepath.App.json` or :meth:`morepath.App.html`) and return
the content that should go into the response body, such as a HTML
string or a JSON-serializable object. Morepath then automatically
creates the response with the right content type for you. Should you
wish to set additional information on the response object, you can use
:meth:`morepath.Request.after`.

.. _review-resource:

Resource
--------

A resource_ is anything that can be addressed on the web by a URL_ (or
URI_ or IRI_). Can be a web page presenting a full UI (using HTML +
CSS), or can be a piece of information (typically in JSON), or can
also be an abstract entity that has no representation at all.

Morepath lets you implement resources of all kinds. Normally Morepath
resources have representations, but it is also possible to implement
abstract entities that have just a URL and have no
representation. Morepath can also help you create links to resources
on other web servers.

.. _resource: https://en.wikipedia.org/wiki/Web_resource

.. _URL: https://en.wikipedia.org/wiki/Uniform_resource_locator

.. _URI: https://en.wikipedia.org/wiki/Uniform_resource_identifier

.. _IRI: https://en.wikipedia.org/wiki/Internationalized_resource_identifier

.. _review-url:

URL
---

Here is an example of a URL::

  http://example.com/documents/3

A HTTP client such as a web browser uses URLs to determine:

* What protocol to use to talk to the server (in this case ``http``).

* What *host* to talk to (in this case ``example.com``). This
  identifies the web server, though a complex host may be implemented
  using a combination of web servers.

* What *path* to request from the server (in this case ``/documents/3``).

The server determines how it responds to requests for particular paths.

.. _review-path:

URL parameters
--------------

A URL can have additional parameters::

  http://example.com/documents/3?expand=1&highlight=foo

The list of parameters start with ``?``. Names are connected with
values using ``=``, and name/value pairs are connected with ``&``.

Path
----

A path is a way for a client to address a particular resource on a
server. It is part of the request. The path is also part of URLs, and
thus can be used for linking resources.

Morepath connects paths with Python objects using the path directive
(:meth:`morepath.App.path`): it can resolve a path to a Python object,
and construct a path for a given Python object. This is described in
:doc:`paths_and_linking`.

Example::

  @App.path(path='/documents/{id}', model=Document)
  def get_document(id):
     return query_document(id)

If you declare arguments for ``get_document`` that do not get listed
as variables in the ``path`` these are interpreted as expected URL
parameters.

.. _review-link-generation:

Link generation
---------------

Morepath makes it easy to generate a hyperlink to a Python
object. Morepath uses information on the object itself and its class
to determine what link to generate.

Given the ``path`` directive above, we can generate a link to an instance
of ``Document`` using :meth:`morepath.Request.link`::

  some_document = get_some_document_from_somewhere()
  request.link(some_document)

This makes it easy to create links within Morepath view functions.

Morepath's link generation can generate links that include URL
parameters.

.. _review-headers:

Headers
-------

A HTTP request and a HTTP response have headers. Headers contain
information about the message that are not the body: they are about
the request or the response, or about the body. For example, the
content-type is header named ``Content-Type`` and has a value that is
a `MIME type`_ such as ``text/html``.

Headers are used for a wide variety of purposes, such as to declare
information about how a client may cache a response, or what kind of
responses a client accepts from a server, or to pass cookies along.
Here is an `overview of common headers`_.

In Morepath, the headers are accessible on a request and response
object as the attribute :attr:`webob.request.BaseRequest.headers` and
:attr:`webob.response.Response.headers`.  which behaves like a Python
dictionary. You could therefore access the request content-type using
``request.headers['Content-Type']``. But see below for a more
convenient way to access the content type.

To set the headers (or other information) on a response, you can
create a ``morepath.Response`` instance in a view function. You can
then pass in the headers, or set them afterward.

Often better is to use the :func:`morepath.Request.after` decorator to
declare a function that sets headers the response object once it has
been created for you by the framework.

WebOb_ has APIs that help you deal with many headers at a higher level
of abstraction. For example,
:attr:`webob.request.BaseRequest.content_type` is a more convenient
way to access the content type information of a request than to access
the header directly, as additional charset information is not
there. Before you start to manipulate headers directly it pays off to
consult the WebOb documentation for :class:`webob.request.BaseRequest`
and :class:`webob.response.Response`: there may well be a better way.

Morepath also has special support for dealing with certain
headers. For instance, the Forwarded_ header can be set by a HTTP
proxy. To make Morepath use this header for URL generation, you can
use the `more.forwarded`_ extension.

.. _`MIME type`: https://en.wikipedia.org/wiki/Internet_media_type

.. _`overview of common headers`: https://en.wikipedia.org/wiki/List_of_HTTP_header_fields

.. _`more.forwarded`: https://pypi.python.org/pypi/more.forwarded/

.. _forwarded: http://tools.ietf.org/html/rfc7239

.. _review-cookies:

Cookies
-------

One special set of headers deals with `HTTP cookies`_. A server can set a
cookie on the client by passing back a special header in its
response. A cookie is much like a key/value pair in a Python
dictionary.

Once the cookie has been set, the client sends back the cookie to the
server during each subsequent request, again using a header, until the
cookie expires or cookie is explicitly deleted by the server using a
response header.

Normally in HTTP requests are independent from each other: assuming
the server database is the same, the same request should give the same
response, no matter what other requests have gone before it. This
makes it easier to reason about HTTP, and it makes it easier to scale
it up, for instance by caching responses.

Cookies change this: they can be used to make requests
order-dependent. This can be useful, but it can also make it harder to
reason about what is going on and scale, so be careful with them. In
particular, a REST web service should be able to function without
requiring the client to maintain cookies.

Cookies are commonly used to store login session information on the
client.

WebOb makes management of cookies more convenient: the
:attr:`webob.request.BaseRequest.cookies` attribute on the request
object contains the list of cookies sent by the client, and the
response object has an API incuding
:meth:`webob.response.Response.set_cookie` and
:meth:`webob.response.Response.delete_cookie` to allow you to manage
cookies.

.. _`HTTP cookies`: https://en.wikipedia.org/wiki/HTTP_cookie

.. _review-content-types:

Content types
-------------

A resource may present itself in variety of representations. This is
indicated by the content type set in the HTTP response, using the
``Content-Type`` header.  There are a lot of content types, including
HTML and JSON.  The value is a `MIME type`_ such as ``text/html`` for
HTML and ``application/json`` for JSON. The value can also contain
additional parameters such as character encoding information.

WebOb makes content-type header information conveniently available
with the :attr:`webob.request.BaseRequest.content_type`,
:attr:`webob.response.Response.content_type` and
:attr:`webob.response.Response.content_type_params` attributes.

A request may also have a content type: the request content type
determines what kind of content is sent to the server by the client in
the request body.

While you can create any kind of content type with Morepath, it has
special support for generating HTML and JSON responses (using
:meth:`morepath.App.html` and :meth:`morepath.App.json`), and for
processing a JSON request body (see ``load_json`` in :doc:`json`).

.. _review-view:

View
----

In Morepath, a view is a Python function that takes a Python object to
represent (``self``) and a :class:`morepath.Request` object
(``request``) as arguments and returns something that can be turned
into a HTTP response, or a HTTP response object directly.

Here is an example of a Morepath view, using the most basic
:meth:`morepath.App.view` directive::

  @App.view(model=MyObject)
  def my_object_default(self, request):
      return "some text content"

There are also specific :meth:`morepath.App.json` and
:meth:`morepath.App.html` directives to support those content types.

See :doc:`views` for much more on how to construct Morepath views.

.. _review-http-request-method:

HTTP request method
-------------------

A HTTP request has a *method*, also known as *HTTP verb*. The ``GET``
method is used to retrieve information from the server. The ``POST``
method is used to add new information to the server (for instance a
form submit), and the ``PUT`` method is used to update existing
information. The ``DELETE`` method is used to delete information from
the server.

It is up to the server implementation how to exactly handle the
request method. With Morepath, by default a view responds to the
``GET`` method, but you can also write views to handle the other HTTP
methods, by indicating it with a *view predicate*. Here is a view that
handles the ``POST`` method (and returns a representation of what has
just been POSTed)::

  @App.view(model=MyCollection, request_method='POST')
  def add_to_collection(self, request):
      item = MyItem(request.json)
      self.add(item)
      return request.view(item)

You can access the method on the request using
:attr:`webob.request.BaseRequest.method`, but typically Morepath does
this for you when you use the ``request_method`` predicate.

.. _review-view-predicate:

View predicate
--------------

A *view predicate* in Morepath is used to match a view function with
details of ``self`` and ``request``.

This view directive::

  @App.view(model=MyCollection, request_method='POST')
  def add_to_collection(self, request):
     ...

only matches when ``self`` is an instance of ``MyCollection``
(``model`` predicate) and when ``request.method`` is ``POST``
(``request_method`` predicate). Only in this case will
``add_to_collection`` be called.

You can extend Morepath with additional view predicates. You can also
define a *predicate fallback*, which can be used to specify what HTTP
status code to set when the view cannot be matched.

See `view predicates
<http://morepath.readthedocs.org/en/latest/views.html#predicates>`_

.. _review-http-status-codes:

HTTP status codes
-----------------

HTTP status codes such as ``200 Ok`` and ``404 Not Found`` are part of
the HTTP response. Here is a `list of HTTP status codes
<https://en.wikipedia.org/wiki/List_of_HTTP_status_codes>`_.  The
server can use them to indicate to the client whether it was
successfully able to create a response, or if not, what the problem
was.

Morepath can automatically generate the correct HTTP status codes
for you in many cases:

200 Ok:
  When the path in the request is matched with a path directive, and
  there is a view for the particular model and request method.

404 Not Found:
  When the path does not match, or when the path matches but the path
  function returns ``None``.

  Also when no view is available for the request in combination with
  the object returned by the path function. More specifically, the
  ``model`` view predicate or the ``name`` view predicate do not
  match.

400 Bad Request:
  When information in the path or request parameters could not be
  converted to the required types.

405 Method Not Allowed:
  When no view exists for the given HTTP request method. More
  specifically, the ``request_method`` view predicate does not match.

422 Unprocessable Entity:
  When the request body supplied with a ``POST`` or ``PUT`` request
  can be parsed (as JSON, for instance), but is not the correct type.

  More specifically, the ``body_model`` view predicate does not match.

500 Internal Server Error:
  There is a bug in the server that causes an exception to be
  raised. Morepath does not generate these itself, but a WSGI server
  automatically catches any exceptions not handled by Morepath and
  turns them into 500 errors.

Instead of having to write code that sends back the right status codes
manually, you declare paths and views with Morepath and Morepath can
usually do the right thing for you automatically. This saves you from
writing a lot of custom code when you want to implement HTTP properly.

Sometimes it is still useful to set the status code directly. WebOb
lets you raise `special exceptions`_ for HTTP errors. You can also set
the :attr:`webob.response.Response.status` attribute on the response.

.. _`special exceptions`: http://docs.webob.org/en/latest/modules/exceptions.html

.. _review-json:

JSON
----

A representation of a resource. JSON_ is a language that represents
data, not user interface (like HTML combined with CSS) or logic (like
Python or JavaScript). JSON looks like this::

  {
    "id": "foo_barson",
    "name": "Foo Barson",
    "occupation": "Carpenter",
    "level": 34
    "friends": ["http://example.com/people/qux_quxson",
                "http://example.com/people/one_twonson"]
  }


JSON is the most common data representation language used in REST web
services. The main alternative is XML. While XML does offer more
extensive tooling support, it is a lot more verbose and more difficult
to process than JSON. JSON is already very close to the data
structures of many programming languages, including JavaScript and
Python.

In Python, JSON can be constructed by combining Python dictionaries
and lists with strings, numbers, booleans and ``None``.

With Morepath you can use the :meth:`morepath.App.json` directive to
generate JSON programmatically::

  @App.json(model=MyObject)
  def my_object_default(self, request):
       return {
          "id": self.id,
          "name": self.name,
          "occuptation": self.get_occupation(),
          "level": self.level,
          "friends": [request.link(friend) for friend in self.friends]
       }


This works like the ``view`` directive, but in addition converts the
return value of the function into a JSON response that is sent to the
client.

.. _JSON: https://en.wikipedia.org/wiki/JSON

.. _review-json-ld:

JSON-LD
-------

`JSON-LD`_ is an extension of JSON that helps support linked data in
JSON. Any JSON-LD structure is valid JSON, but not every JSON
structure is valid JSON-LD.

Using a ``@context``, it lets a JSON object describe which parts of it
contain hyperlinks, and also allows JSON property names themselves to
be interpreted as unique hyperlinks. You can also express that
particular property values have a particular data type; this can range
from basic data types like datetime to custom data types like
"person". All of this can help when you want to process JSON coming
from different data sources.

Perhaps more important in practice for REST web services is that it
also offers a standard way for a JSON object to have a unique id and a
type. Both are identified by a hyperlink, as the special ``@id`` and
``@type`` properties. ``@type`` in particular makes it easier to use
JSON data as hypermedia: client behavior can be driven by the type of
data that is retrieved, instead of what URL it happened to be
retrieved from.

Morepath does not mandate the use of JSON-LD, or has any special
support for it, but its link generation facilities make it easier to
use it.

.. _`JSON-LD`: http://json-ld.org/

.. _review-http-api:

HTTP API
--------

A HTTP API is a web service that is built on HTTP; it is based on the
notion of HTTP resources on URLs and has an understanding of HTTP
request methods.

This is to distinguish it from a web service implementation where HTTP
is merely a transport mechanism, such as SOAP.

Because the client needs to understand what URLs exist on the server
and how to interpret their response, the coupling between client and
server code is relatively tight.

This type of web service is commonly called a *REST* web service, but
the original definition of REST goes beyond this and adds hypermedia.
Many HTTP APIs only reach level 2 on the `Richardson Maturity Model`_,
which isn't full REST yet.

A HTTP API is sometimes simply called *API*, which is also confusing,
as the word API has a lot of other uses in development outside of
HTTP.

Morepath is designed to help you build HTTP APIs, but also to go you a
step further to full REST.

.. _`Richardson Maturity Model`: http://martinfowler.com/articles/richardsonMaturityModel.html

.. _review-rest-web-service:

REST web service
----------------

Morepath helps you to create REST_ web service, also known as a
*hypermedia API*.

This is level 3 on the `Richardson Maturity Model`_.

This means that to interact with the content of the web service you
can follow hyperlinks. A client starts at one root URL and to get to
other information it follow links in the content.

Different JSON resources can be distinguished from each other by their
type; this can based on the ``content-type`` of the response, or be
based on information within the content itself, such as a type
property in JSON (``@type`` in `JSON-LD`_).

In other words, the web service represents itself to software much
like a web site presents itself to a human: as content with links.

A REST web service allows for a looser coupling between server and
client than a plain HTTP API allows, as the client does not need to
know more than a single entry point URL into the server, and only
needs an understanding of the response types and how to navigate
links.

.. _REST: https://en.wikipedia.org/wiki/Representational_state_transfer

.. _review-html-and-css:

HTML and CSS
------------

HTML is a markup language used to represent a resource. Augmented by
CSS, a style language, it determines what you see on a web page.

HTML can be loaded from a files on the server; this typically done
with a general web server such as Apache and Nginx. For dynamic
applications HTML can also be generated on the server, often using a
server-side templating language.

HTML may also be manipulated programmatically in the browser using
JavaScript through the DOM API.

In Morepath you can use the :meth:`morepath.App.html` view directive
to generate HTML programmatically::

  @App.view(model=MyObject)
  def my_object_default(self, request):
       return '<html><head></head><body></body></html>'

Morepath at this point does not have support for server-side
templating.

See :doc:`more.static` for information on how you can load static
resources such as CSS and JavaScript automatically to augment a HTML page.

.. _review-web-page:

Web page
--------

The browser displays a user interface to the user in the form of a
*web page*. A web page is usually constructed using HTML_ and CSS_. Other
content such as images, video, audio, SVG, canvas, WebGL may also
be embedded into it.

JavaScript_ code is executed in the browser to make the user interface
more dynamic, and this dynamism can go very far.

A web page is loaded by putting a URL in the address bar of the
browser. The browser then fetches it (and related resources) from the
server. You can do this manually, or by clicking a link, or the URL of
the browser may be changed programmatically with JavaScript code.

In the past, all web applications were implemented as a multiple web
pages that were generated on the server in response to user actions.

It is also possible to change the URL in the address bar without
fetching a complete new web page from the server. This technique is
used to implement single-page web applications.

.. _HTML: https://en.wikipedia.org/wiki/HTML

.. _CSS: https://en.wikipedia.org/wiki/Cascading_Style_Sheets

.. _review-single-page-web-application:

Single-page web application
---------------------------

A single-page web application (SPA) is web application that consists
of a single web page that is updated within the browser without the
need to load a complete need web page. So the web page is loaded from
the server only once, when the user first goes there.

When a user interacts with it, JavaScript code is executed that
updates the user interface and may also interact with a web server
using AJAX.

A single page web application may update the URL in the address bar of
the browser, and respond to URL changes, but it is the same web page
that implements the behavior for all these URLs. It may need a bit of
server-side support to do so.

Morepath supports the creation of single-page web applications. It
also lets you create multi-page applications, but at this point in
time has no special support for server-side templating.
