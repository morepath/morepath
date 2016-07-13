Writing automated tests
=======================

This an introductory guide to writing automated tests for your
Morepath project. We assume you've already installed Morepath; if not,
see the :doc:`installation` section.

In order to carry out the test we'll use WebTest_, which you'll need
to have installed. You also need a test automation tool; we recommend
pytest_. The :ref:`cookiecutter template <cookiecutter>` installs
both for you, alternatively you can install them with pip:

.. code-block:: console

  $ pip install webtest pytest


Testing "Hello world!"
----------------------

Let’s look at a minimal test of the "Hello world!" application from
the :doc:`quickstart`:

.. testcode::

  from hello import App
  from webtest import TestApp as Client

  def test_hello():
      c = Client(App())

      response = c.get('/')

      assert response.body == b'Hello world!'

You can save this function into a file, say ``test_hello.py`` and use
a test automation tool like pytest_ to run it:

.. code-block:: console

   $ py.test -q test_hello.py
   .
   1 passed in 0.13 seconds

If you invoke it as a regular Python function, a silent completion
signifies success:

  >>> test_hello()

.. _pytest: https://pytest.org

Let's now go through the test, line by line.

1. We import the application that we want to test. In this case we
   assume that you have saved the "Hello world!" application from the
   :doc:`quickstart` in ``hello.py``:

   >>> from hello import App

   You can additionally use :func:`morepath.scan` if you are not sure
   whether importing the app imports all the modules that are
   required. In this particular instance, we know that importing
   ``hello`` is sufficient and :func:`morepath.scan` is not needed.

2. WebTest_ provides a class called :class:`webtest.app.TestApp` that
   emulates a client for WSGI apps. We don't want to confuse it with
   the app under test, so we as a convention we import it as
   ``Client``. This also stops pytest_ from scanning it for tests as
   it has the ``Test`` prefix:

   >>> from webtest import TestApp as Client

3. We instantiate the app under test and the client:

   >>> c = Client(App())

4. At this point we can use the client to query the app:

   >>> response = c.get('/')

   The returned response is an instance of
   :class:`webtest.response.TestResponse`:

   >>> response
   <200 OK text/plain body=b'Hello world!'>

5. We can now verify that the response satisfies our expectations. In
   this case we test the response body in its entirety::

   >>> assert response.body == b'The view for model: foo'

.. _webtest: https://webtest.readthedocs.org
