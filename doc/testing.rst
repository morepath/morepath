Automating the tests for your App
=================================

This an introductory guide to writing automated tests for your
Morepath app.  We assume you've already installed Morepath; if not,
see the :doc:`installation` section.

In order to carry out the test we'll use WebTest_, which you'll need
to have installed. You'll want to have a test automation tool like
pytest_ too.  The :ref:`cookiecutter template <cookiecutter>` installs
both for you, alternatively you can install both with pip:

.. code-block:: sh

  $ pip install webtest pytest


Testing a basic app
-------------------

Let’s look at a minimal test of a basic app in Morepath:

.. testcode::

  def test_basic():
      from morepath.tests.fixtures import basic
      from webtest import TestApp as Client

      c = Client(basic.app())

      response = c.get('/foo')

      assert response.body == b'The view for model: foo'

You can save this function into a file and use a test automation tool
like pytest_ to run it, or you can also invoke it as a regular Python
function --- in this case a silent completion signifies success:

  >>> test_basic()

.. _pytest: https://pytest.org

Let's now go through the test, line by line.

1. We import the application that we want to test.  In this case we
   are going to use one of the simple apps that are part of the test
   suite distributed with Morepath:

   >>> from morepath.tests.fixtures import basic

   You can additionally use :func:`morepath.scan` if you are not sure
   whether importing the app imports all the modules that are
   required. In this particular instance, we know that importing
   ``basic`` is sufficient and :func:`morepath.scan` is not needed.

2. WebTest_ provides a class called :class:`webtest.app.TestApp`
   that emulates a client for WSGI apps.  Lest we confuse it with the
   app under test, we'll import it as ``Client``:

   >>> from webtest import TestApp as Client

3. We instantiate the app under test and the client:

   >>> c = Client(basic.app())

4. At this point we can use the client to query the app:

   >>> response = c.get('/foo')

   The returned response is an instance of
   :class:`webtest.response.TestResponse`:

   >>> response                         # doctest: -ELLIPSIS
   <200 OK text/plain body='The view ... foo'/23>

5. We can now verify that the response satisfies our expectations. In
   this case we test the response body in its entirety::

   >>> assert response.body == b'The view for model: foo'

.. _webtest: https://webtest.readthedocs.org
