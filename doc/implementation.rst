Implementation Overview
=======================

Introduction
------------

This documentation contains an overview of how the implementation of
Morepath works. This includes a description of the different pieces of
Morepath as well as an overview of the internal APIs.

How it all works
----------------

import-time
~~~~~~~~~~~

When a Morepath-based application starts, the first thing that happens
is that all directives in modules that are imported are registered
with Morepath's configuration engine. This configuration engine is
implemented using the Dectate_ library. Configuration is associated
with :class:`morepath.App` subclasses.

Only the minimum code is executed to register the directives with
their App classes; the directive actions are not performed yet.

Besides normal Python imports, :func:`morepath.scan` and
:func:`morepath.autoscan` can be used to automatically import modules
so that their directives are registered.

commit
~~~~~~

Configuration is then committed using :meth:`morepath.App.commit`, or
the more low-level :func:`morepath.commit`.

This causes :func:`dectate.commit` to be called for a particular App
class. This takes all the configuration as recorded during import-time
and resolves it. This involves:

* detect any conflicts between documentation and reporting it.

* detect any :class:`morepath.error.DirectiveError` errors raised by
  individual directive actions.

* resolve subclassing so that apps inherit from base apps and can override
  as well.

* performing the resulting configuration actions in the correct order.

All this is implemented by Dectate_.

Morepath specific directives are defined in
:mod:`morepath.directive`. Each directly or indirectly cause
:class:`dectate.Action` objects to be created. When the action is
performed various configuration registry objects are affected. These
registries are the end result of configuration.

:class:`morepath.directive.RegRegistry` is the most advanced of
registries used in Morepath and is based on :class:`reg.Registry`. In
this registry generic dispatch functions as defined in
:mod:`morepath.generic` get individual implementations registered for
them. Reg dispatches to specific implementations based on the function
arguments used to call the generic function. Much of the functionality
in Morepath ultimately causes a registration into the Reg registry and
during runtime uses the API in :mod:`morepath.generic`.

A special registry contains the settings; setting functions as
declared by :meth:`morepath.App.setting` and
:meth:`morepath.App.setting_section` are executed and stored in a
:class:`morepath.directive.SettingRegistry` which is accessible through
:attr:`morepath.App.settings`.

.. _Dectate: http://dectate.readthedocs.org

instantiate the app
~~~~~~~~~~~~~~~~~~~

Once configuration has successfully completed, the app can be
instantiated. Apps are also instantiated during run-time when they are
mounted and a path resolves into a mounted app.

The app is now also a WSGI function so can be run with any WSGI
server.

run-time
~~~~~~~~

When a request comes in through WSGI into
:meth:`morepath.App.__call__`, a :class:`morepath.Request` object is
created.

:func:`morepath.publish.publish` defines the core Morepath
publication procedure, which turns requests into responses. This
is done by first resolving the model and then rendering the resulting
model instance as a response.

During the first request, tweens (as declared using
:meth:`morepath.App.tween_factory`) are created and wrapped around
:func:`morepath.publish.publish`. Tweens are request/response based
middleware functions. A standard Morepath tween implemented by
:func:`morepath.core.excview_tween_factory`, renders exceptions
raised by application code as views. The default Morepath tween
factories are declared in :mod:`morepath.core` and tween factories get
registered into :class:`morepath.directive.TweenRegistry`.

resolve the model
~~~~~~~~~~~~~~~~~

:func:`morepath.publish.resolve_model` looks up a model object as
created by the factory functions the user declared with the
:meth:`morepath.App.path` directive and the :meth:`morepath.App.mount`
directives.

:mod:`morepath.path` contains the
:class:`morepath.directive.PathRegistry` that has the API to register
paths.

The route registration and resolution system is implemented by
:mod:`morepath.traject`.

Default converters used during this step are declared in
:mod:`morepath.core`. Converters are declared with the
:meth:`morepath.App.converter` directive and are registered in the
:class:`morepath.directive.ConverterRegistry`.

render the model object
~~~~~~~~~~~~~~~~~~~~~~~

:func:`morepath.publish.resolve_response` then renders the model
object to a response using a view function as declared by user with
the :meth:`morepath.App.view` directive (and :meth:`morepath.App.json`
and :meth:`morepath.App.html`).

This behavior is implemented using the
:class:`morepath.directive.ViewRegistry`. This builds on Reg_ and uses
special predicates declared in :mod:`morepath.core` and registered
into the Reg registry using
:class:`morepath.directive.PredicateRegistry`. The views are
registered in the Reg registry too.

Views can use templates as declared with the
:class:`morepath.App.template_directory`,
:class:`morepath.App.template_loader` and
:class:`morepath.App.template_render` directives. These are registered
into the :class:`morepath.directive.TemplateEngineRegistry`.

Before a view is rendered a permission check is done for a model
object and an identity. This uses the rules defined by
:meth:`morepath.App.permission_rule` are used. These are registered
into the Reg registry.

Permission checks use :attr:`morepath.Request.identity`. When this is
accessed the first time during a request the user's identity is
constructed from information in the request according to the
:meth:`morepath.App.identity_policy`, as implemented by
:mod:`morepath.authentication`.

creating links
~~~~~~~~~~~~~~

During the rendering of the model object to a response a link can be
generated for a model object by user code that invokes
:class:`morepath.Request.link`. :class:`morepath.App` has a bunch of
private functions (``morepath.App._get_path`` etc) that implement
constructing paths. This uses inverse path information
(:class:`morepath.path.Path`) stored into the Reg registry using
:meth:`morepath.directive.PathRegistry.register_inverse_path`.

Dependencies
------------

Morepath uses the following dependencies:

* Webob_: a request and response implementation based on WSGI.

* Reg_: a generic dispatch library. This is used for all functions
  you can register that are aware of subclassing, in particular views.

* Dectate_: the configuration engine. This is used to implement
  directives and how configuration actions are executed during commit.

* importscan_: automatically recursively import all modules in a
  package.

.. _Webob: http://webob.org

.. _Reg: http://reg.readthedocs.org

.. _Dectate: http://dectate.readthedocs.org

.. _importscan: http://importscan.readthedocs.org

Internal APIs
-------------

These are the internal modules used by Morepath. For more information
click on the module headings to see the internal APIs. See also
:mod:`morepath` for the public API and :mod:`morepath.directive` for
the extension API.

.. toctree::
   :maxdepth: 2

   internals/app
   internals/authentication
   internals/autosetup
   internals/cachingreg
   internals/compat
   internals/converter
   internals/core
   internals/generic
   internals/implicit
   internals/path
   internals/predicate
   internals/publish
   internals/reify
   internals/request
   internals/settings
   internals/template
   internals/toposort
   internals/traject
   internals/tween
   internals/view

:mod:`morepath.error` and :mod:`morepath.pdbsupport` are documented as
part of the public API.

