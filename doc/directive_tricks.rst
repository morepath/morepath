Directive tricks
================

.. sidebar:: Why not inside the class?

  This in fact works::

    class A(object):
        @classmethod
        @App.json(model=Foo)
        def foo_default(self, request):
            ...

  But it is equivalent to using ``@staticmethod``, so there is no
  point to do this.

  This is **broken code**::

    class A(object):
        @classmethod
        @App.json(model=Foo)
        def foo_default(cls, self, request):
            ...

  This is broken because at the point ``foo_default`` is registered
  with ``App.json`` it isn't a ``classmethod`` yet, but a plain
  function, and it has the wrong signature to work with Morepath.

  This is also **broken code**::

    class A(object):
        @App.json(model=Foo)
        @classmethod
        def foo_default(cls, self, request):
            ...

  This is broken because what gets registered with Morepath is an
  unbound class method, which is not callable.

  But if you do::

    class A(object):
        @classmethod
        def foo_default(cls, self, request):
            ...

    App.json(model=Foo)(A.foo_default)

  it works as ``A.foo_default`` binds the ``cls`` argument first.

You usually use Morepath directives like decorators on functions::

  @App.json(model=Foo)
  def foo_default(self, request):
      ...

You can also use directives with ``@staticmethod``::

  class A(object):
      @staticmethod
      @App.json(model=Foo)
      def foo_default(self, request):
          ...

It is important to apply ``@staticmethod`` directive after the
Morepath directive is applied; it won't work the other away around.

With ``@classmethod`` the situation is slightly more involved. This is the
correct way to do it::

  class A(object):
    @classmethod
    def foo_default(cls, self, request):
        ...

  App.json(model=Foo)(A.foo_default)

So, you apply the directive as a function to ``A.foo_default`` outside
of the class.

This points to a general principle: we can use any Morepath directive
as a plain function, not just as a decorator. This means you can
combine a directive with a lambda, which sometimes leads to shorter
code::

  App.template_directory()(lambda: 'templates')

This means you can also register functions programmatically::

  for i, func in enumerate(functions):
     App.json(model=Foo, name='view_%s' % i)(func)

We recommend caution here though -- stick with the normal decorator
based approach as much as you can as it is more declarative. This
tends to lead to more maintainable code.
