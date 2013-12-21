.. Morepath documentation master file, created by
   sphinx-quickstart on Tue Aug  6 12:47:25 2013.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Morepath: Super Powered Python Web Framework
============================================

**Morepath is a Python web microframework, with super powers.**

* Does your web framework get in your way?

* Can't easily express what you want?

* Or perhaps it's not extensible enough?

* Do the extension mechanisms that *are* there feel ad-hoc,
  underengineered, incoherent, and then fall apart on you?

* Do you wonder why it doesn't just let you override this *one* thing?

* And why does it need a separate framework on top to develop web
  services?

* **Want a web framework where the difficult is easy instead, even
  obvious?**

**Go on the Morepath!**

Morepath Super Powers
---------------------

* :ref:`Automatic hyperlinks that don't break. <easy-linking>`

* :ref:`Creating generic UIs is as easy as subclassing. <generic-ui>`

* :ref:`Simple, flexible, powerful permissions. <model-driven-permissions>`

* :ref:`Reuse views in views. <composable-views>`

* :ref:`Extensible apps. Nestable apps. Override apps, even override
  Morepath itself! <extensible-apps>`

Morepath Knows About Your Models
--------------------------------

::

  import morepath

  app = morepath.App()

  class Document(object):
      def __init__(self, id):
          self.id = id

  @app.root()
  class Root(object):
      pass

  @app.model(path='documents/{id}', model=Document,
             variables=lambda doc: {'id': doc.id})
  def get_document(id):
      return Document(id)  # query for doc

  @app.html(model=Root)
  def hello_root(request, model):
      return '<a href="%s">Go to doc</a>' % request.link(Document('foo'))

  @app.html(model=Document)
  def hello_doc(request, model):
      return '<p>Hello document: %s!</p>' % model.id

  if __name__ == '__main__':
      config = morepath.setup()
      config.scan()
      config.commit()
      app.run()

Want to know what's going on? Check out the :doc:`Quickstart <quickstart>`!

More documentation, please!
---------------------------

* :doc:`Read the documentation <toc>`

If you have questions, please join the #morepath IRC channel on
freenode. Hope to see you there!
