.. Morepath documentation master file, created by
   sphinx-quickstart on Tue Aug  6 12:47:25 2013.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Morepath: Super Powered Python Web Framework
============================================

**Morepath is a Python web microframework, with super powers.**

Morepath is an Python WSGI microframework. It uses routing, but the
routing is to models. Morepath is model-driven and **flexible**, which
makes it **expressive**.

* Morepath does not get in your way.

* It lets you express what you want, easily. See :doc:`quickstart`.

* It's extensible, with a simple, coherent and universal extension and
  override mechanism, supporting reusable code. See :doc:`app_reuse`.

* It understands about generating hyperlinks. The web is about
  hyperlinks and Morepath actually *knows* about them. See
  :doc:`paths_and_linking`.

* Views are simple functions. Generic views are just views too. See
  :doc:`views`.

* It has all the tools to develop REST web services in the box. See
  :doc:`rest`.

Sounds interesting?

**Go on the Morepath!**

Morepath Super Powers
---------------------

* :ref:`Automatic hyperlinks that don't break. <easy-linking>`

* :ref:`Creating generic UIs is as easy as subclassing. <generic-ui>`

* :ref:`Simple, flexible, powerful permissions. <model-driven-permissions>`

* :ref:`Reuse views in views. <composable-views>`

* :ref:`Extensible apps. Nestable apps. Override apps, even override
  Morepath itself! <extensible-apps>`

Curious how Morepath compares with other Python web frameworks? See
:doc:`compared`.

Morepath Knows About Your Models
--------------------------------

::

  import morepath

  app = morepath.App()

  class Document(object):
      def __init__(self, id):
          self.id = id

  @app.path(path='')
  class Root(object):
      pass

  @app.path(path='documents/{id}', model=Document)
  def get_document(id):
      return Document(id)  # query for doc

  @app.html(model=Root)
  def hello_root(self, request):
      return '<a href="%s">Go to doc</a>' % request.link(Document('foo'))

  @app.html(model=Document)
  def hello_doc(self, request):
      return '<p>Hello document: %s!</p>' % self.id

  if __name__ == '__main__':
      config = morepath.setup()
      config.scan()
      config.commit()
      morepath.run(app)

Want to know what's going on? Check out the :doc:`Quickstart <quickstart>`!

More documentation, please!
---------------------------

* :doc:`Read the documentation <toc>`

If you have questions, please join the #morepath IRC channel on
freenode. Hope to see you there!
