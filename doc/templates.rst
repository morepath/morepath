Templates
=========

Introduction
------------

When you generate HTML from the server (using HTML views) it can be
very handy to have a template language available. A template language
provides some high-level constructs for generating HTML, which are
handy. It can also help you avoid HTML injection security bugs because
it takes care of escaping HTML. It may also be useful to separate HTML
presentation from code.

This document discusses template rendering on the server. In some
modern web applications template rendering is done in the browser
instead of on the server. To do client-side template rendering you
need to use a :ref:`review-client-web-framework` with Morepath. See
also :doc:`more.static`.

Morepath does not have a template language built in. The example in
this document uses `more.chameleon`_. `more.chameleon`_ integrates the
Chameleon template engine, which implements the ZPT template
language. If you prefer Jinja2_, you can use the `more.jinja2`_
extension instead. You can also integrate other template languages.

To use a template you need to use the ``template`` argument with the
:meth:`morepath.App.html` view directive.

Example
-------

This example presupposes that `more.chameleon`_ and its dependencies
have been installed. Here is how we use it::

  from more.chameleon import ChameleonApp

  class App(ChameleonApp):
      pass

  @App.template_directory()
  def get_template_directory():
      return 'templates'

  @App.html(model=Person, template='person.pt')
  def person_default(self, request):
      return { 'name': self.name }

Let's examine this code. First we import ``ChameleonApp`` and subclass
from it in our own app. This enables Chameleon templating for the
``.pt`` file extension.

We then need to specify the directory that contains our templates
using the :meth:`morepath.App.template_directory` directive. The
directive should return either an absolute or a relative path to this
template directory. If a relative path is returned, it is
automatically made relative to the directory the Python module is in.

Next we use ``template='person.pt'`` in the HTML view
directive. ``person.pt`` is a file sitting in the ``templates``
directory, with this content::

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

Overrides
---------

When you subclass an app you may want to override some of the
templates it uses, or add new templates. You can do this by using the
``template_directory`` directive in your subclassed app::

  class SubApp(App):
      pass

  @SubApp.template_directory()
  def get_override_template_directory():
     return 'templates_override'

Morepath's template integration searches for templates in the template
directories in application order, so for ``SubApp`` here, first
``templates_override``, and then ``templates`` as defined by the base
``App``. So for ``SubApp``, you can override a template defined in the
directory ``templates`` by placing a file with the same name in the
directory ``templates_override``. This only affects ``SubApp``, not
``App`` itself.

You can also use the ``before`` argument with the
:meth:`morepath.App.template_directory` directive to specify more
exactly how you want template directories to be searched. This can be
useful if you want to organize your templates in multiple directories
in the same application. If ``get_override_template_directory`` should
come before ``get_template_directory`` in the directory search path,
you should use ``before=get_template_directory``::

  @SubApp.template_directory(before=get_template_directory)
  def get_override_template_directory():
     return 'templates_override'

but it is usually simpler not to be this explicit and to rely on
application inheritance instead.

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

* During startup time, ``person.pt`` is loaded from the configured
  template directories as a template object.

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
for ``.pt`` files (taken from `more.chameleon`_)::

  import chameleon

  @App.template_loader(extension='.pt')
  def get_template_loader(template_directories, settings):
      settings = settings.chameleon.__dict__.copy()
      # we control the search_path entirely by what we pass here as
      # template_directories, so we never want the template itself
      # to prepend its own path
      settings['prepend_relative_search_path'] = False
      return chameleon.PageTemplateLoader(
          template_directories,
          default_extension='.pt',
          **settings)

  @App.template_render(extension='.pt')
  def get_chameleon_render(loader, name, original_render):
      template = loader.load(name)

      def render(content, request):
          variables = {'request': request}
          variables.update(content)
          return original_render(template.render(**variables), request)
      return render

  @App.setting_section(section='chameleon')
  def get_setting_section():
      return {'auto_reload': False}

Some details:

* ``extension`` is the file extension. When you refer to a template
  with a particular extension, this template engine is used.

* The function decorated by :meth:`morepath.App.template_loader` gets
  two arguments: directories to look in for templates (earliest in the
  list first), and Morepath settings from which template engine
  settings can be extracted.

* The function decorated by :meth:`morepath.App.template_render`
  gets three arguments:

  * ``loader``: the loader constructed by the ``template_loader``
    directive.

  * ``name``: the name of the template to create a render function for.

  * The ``original_render`` function as passed into the view
    decorator, so ``render_html`` for instance. It takes the content
    to render and the request and returns a webob response object.
    then passed along to Chameleon.

  The decorated function needs to return a ``render`` function which
  takes the content to render (output from view function) and the
  request as arguments.

  The implementation of this can use the original ``render`` function
  which is passed in as an argument as ``original_render``
  function. It can also create a ``morepath.Response`` object
  directly.

.. _`more.chameleon`: http://pypi.python.org/pypi/more.chameleon

.. _`more.jinja2`: http://pypi.python.org/pypi/more.jinja2

.. _`ZPT`: http://chameleon.readthedocs.org/en/latest/reference.html

.. _`Jinja2`: http://jinja.pocoo.org
