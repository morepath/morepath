Templates
=========

Introduction
------------

It is useful in HTML views to use a template language instead of
generating the HTML output by hand from Python. A template language
provides some high-level constructs for generating HTML, which are
handy. It can also help you avoid HTML injection security bugs
because it takes care of escaping HTML. More abstractly it allows you
to separate HTML presentation from Python view code.

This document discusses template rendering on the server. In some
modern web applications template rendering is done on the client
instead of on the server, or on both. To do client-side template
rendering you need to use a :ref:`review-client-web-framework` with
Morepath. See also :doc:`more.static`.

To use a template you need to use the ``template`` argument with the
:meth:`morepath.App.html` view directive.

Example
-------

Here is an example that uses the `Chameleon template engine`_ using
the ``more.chameleon`` extension::

  from more.chameleon import ChameleonApp

  class App(ChameleonApp):
      pass

  @App.html(model=Person, template='person.pt')
  def person_default(self, request):
      return { 'name': self.name }

.. _`Chameleon template engine`: https://chameleon.readthedocs.org

Let's examine this code. First we import ``ChameleonApp`` and subclass
from it in our own app. This enables Chameleon templating for the
``.pt`` file extension.

Next we use ``template='person.pt'`` in the HTML view
directive. ``person.pt`` is a file sitting in the same directory as
the Python module, with this content::

  <html>
  <body>
    <p>Hello ${name}!</p>
  </body>
  </html>

Once we have this set up, given a person with a ``name`` attribute of
``"world"``, the output of the view is the following HTML::

  <html>
  <body>
    <p>Hello world!</p>
  </body>
  </html>

The template is applied on the return value of the view function and
the request. This results in a rendered template that is returned as
the response.

Note that Morepath does not have a single preferred template
language. The example used ``more.chameleon``, but you can use other
template languages instead: ``more.jinja2`` for instance.

Details
-------

Templates are loaded during configuration time at startup. The file
extension of the extension (such as ``.pt``) indicates the template
engine to use.

Morepath itself does not support any template language out of the box,
but lets you register a template language engine for a file
extension. You can reuse a template language integration in the same
way you reuse any Morepath code: by subclassing the app class that
implements it in your app.

The template language integration works like this:

* During startup time, ``person.pt`` is loaded from the same directory
  as the Python module. You can also use paths such as
  ``templates/foo.pt`` to refer to ``foo.pt`` in a ``templates``
  subdirectory.

* When the ``person_default`` view is rendered, its return value is
  passed into the template, along with the request. The template
  language integration code then makes this information available for
  use by the template -- the details are up to the integration (and
  should be documented there).

The ``template`` argument works not just with ``html`` but also with
``view``, ``json``, and any other view functions you may have. It's
most useful for ``html`` views however.

Integrating a new template engine
----------------------------------

A template in Morepath is actually just a convenient way to generate a
``render`` function for a view. That ``render`` function is then used
just like when you write it manually: it's given the return value of
the view function along with a request object, and should return a
WebOb response.

Here is an example of how you can integrate the Chameleon template engine
for ``.pt`` files::

  import chameleon

  @App.template_engine(extension='.pt')
  def get_chameleon_render(path, original_render, settings):
      # construct Chameleon config dict from settings somehow
      config = make_config(settings)
      template = chameleon.PageTemplateFile(template_path, config)
      def render(content, request):
          variables = { 'request': request }
          return original_render(template(options=content, **variables),
                                 request)
      return render

Some details:

* ``extension`` is the file extension. When you refer to a template
  with a particular extension, this template engine is used.

* The decorated function gets three arguments:

  * ``path``: the absolute path to the template file to load.

  * the ``original_render`` function as passed into the view
    decorator, so ``render_html`` for instance. It takes the content
    to render and the request and returns a webob response object.

  * App settings. This can contain useful information to configure the
    template engine.

* The decorated function needs to return a ``render`` function which
  takes the content to render (output from view function) and the
  request as arguments.

  The implementation of this can use the original ``render`` function
  which is passed in as an argument as ``original_render``
  function. It can also create a ``morepath.Response`` object
  directly.
