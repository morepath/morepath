Morepath: Super Powered Python Web Framework
============================================

**Morepath is a Python web microframework, with super powers.**

Morepath is a Python WSGI microframework. It uses routing, but the
routing is to models. Morepath is model-driven and **flexible**, which
makes it **expressive**.

* Morepath does not get in your way.

* It lets you express what you want with ease. See :doc:`quickstart`.

* It's extensible, with a simple, coherent and universal extension and
  override mechanism, supporting reusable code. See :doc:`app_reuse`.

* It understands about generating hyperlinks. The web is about
  hyperlinks and Morepath actually *knows* about them. See
  :doc:`paths_and_linking`.

* Views are simple functions. All views are generic. See :doc:`views`.

* It has all the tools to develop REST web services in the box. See
  :doc:`rest`.

* Documentation is important. Morepath has a lot of :doc:`toc`.

Sounds interesting?

**Walk the Morepath with us!**

Video intro
-----------

Here is a 25 minute introduction to Morepath, originally given at
EuroPython 2014:

.. raw:: html

  <iframe id="ytplayer" type="text/html" width="640" height="390"
    src="http://www.youtube.com/embed/gyDKMAWPyuY?autoplay=0&origin=http://morepath.readthedocs.org"
    frameborder="0"></iframe>

Morepath Super Powers
---------------------

* :ref:`Automatic hyperlinks that don't break. <easy-linking>`

* :ref:`Creating generic UIs is as easy as subclassing. <generic-ui>`

* :ref:`Simple, flexible, powerful permissions. <model-driven-permissions>`

* :ref:`Reuse views in views. <composable-views>`

* :ref:`Extensible apps. Nestable apps. Override apps, even override
  Morepath itself! <extensible-apps>`

* :ref:`Extensible framework. Morepath itself can be extended, and
  your extensions behave exactly like core
  extensions. <extensible-framework>`

Curious how Morepath compares with other Python web frameworks? See
:doc:`compared`.

Morepath Knows About Your Models
--------------------------------

::

  import morepath

  class App(morepath.App):
      pass

  class Document(object):
      def __init__(self, id):
          self.id = id

  @App.path(path='')
  class Root(object):
      pass

  @App.path(path='documents/{id}', model=Document)
  def get_document(id):
      return Document(id)  # query for doc

  @App.html(model=Root)
  def hello_root(self, request):
      return '<a href="%s">Go to doc</a>' % request.link(Document('foo'))

  @App.html(model=Document)
  def hello_doc(self, request):
      return '<p>Hello document: %s!</p>' % self.id

  if __name__ == '__main__':
      morepath.run(App())

Want to know what's going on? Check out the :doc:`Quickstart <quickstart>`!

More documentation, please!
---------------------------

* :doc:`Read the documentation <toc>`

If you have questions, please join the #morepath IRC channel on
freenode. Hope to see you there!

I just want to try it!
----------------------

* `Get started using the Morepath cookiecutter template <https://github.com/morepath/morepath-cookiecutter>`_

You will have your own application to fiddle with in no time!
