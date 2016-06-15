Security
========

Introduction
------------

The security infrastructure in Morepath helps you make sure that web
resources published by your application are only accessible by those
persons that are allowed to do so. If a person is not allowed access,
they will get an appropriate HTTP error: HTTP Forbidden 403.

Identity
--------

.. sidebar:: Using settings in the identity policy

  The function decorated by the ``@App.identity_policy`` decorator takes
  an optional settings argument, which provides access to the App settings.
  So if you define some settings for the identity policy you can pass them
  in like this::

    @App.setting_section(section="policy")
    def get_policy_settings():
        return {'encryption_key': 'secret'}

    @App.identity_policy()
    def get_identity_policy(settings):
        policy_settings = settings.policy.__dict__.copy()
        return CustomIdentityPolicy(**policy_settings)

Before we can determine who is allowed to do what, we need to be able
to identify who people are in the first place.

The identity policy in Morepath takes a HTTP request and establishes a
claimed identity for it. These are some extensions that provide
an identity policy:

`more.jwtauth`_
  Token based authentication system using JSON Web Token (JWT).

`more.itsdangerous`_
  Cookie based identity policy using isdangerous.

`more.basicauth`_
  Identity policy based on the HTTP Basic Authentication.

Choose the one of your choice, install it and follow the instructions
in the README. You can also create your own identity policy.

For basic authentication for instance it will
extract the username and password. The claimed identity can be
accessed by looking at the :attr:`morepath.Request.identity` attribute
on the request object.

You use the :meth:`morepath.App.identity_policy` directive to install
an identity policy into a Morepath app::

  from more.basicauth import BasicAuthIdentityPolicy

  @App.identity_policy()
  def get_identity_policy():
      return BasicAuthIdentityPolicy()

If you want to create your own identity policy, see the
:class:`morepath.IdentityPolicy` API documentation to see
what methods you need to implement.

.. _more.jwtauth: https://github.com/morepath/more.jwtauth

.. _more.itsdangerous: https://github.com/morepath/more.itsdangerous

.. _more.basicauth: https://github.com/morepath/more.basicauth

Verify identity
---------------

The identity policy only establishes who someone is *claimed* to
be. It doesn't verify whether that person is actually who they say
they are. For identity policies where the browser repeatedly sends the
username/password combination to the server, such as with basic
authentication, implemented by `more.basicauth`_ and cookie-based
authentication like `more.itsdangerous`_, we need to check each
time whether the claimed identity is actually a real identity.

By default, Morepath will reject any claimed identities. To let your
application verify identities, you need to use
:meth:`morepath.App.verify_identity`::

  @App.verify_identity()
  def verify_identity(identity):
      return user_has_password(identity.username, identity.password)

The ``identity`` object received here is as established by the
identity policy. What the attributes of the identity object are
(besides ``username``) is also determined by the specific identity
policy you install.

Note that ``user_has_password`` stands in for whatever method you use
to check a user's password; it's not part of Morepath.

Session or token based identity verification
--------------------------------------------

If you use an identity policy based on the session (which you've made
secure otherwise), or on a cryptographic token based authentication
system such as the one implemented by `more.jwtauth`_, the claimed
identity is actually enough.

We know that the claimed identity is actually the one given to the
user earlier when they logged in. No database-based identity check is
required to establish that this is a legitimate identity. You can
therefore implement ``verify_identity`` like this::

  @App.verify_identity()
  def verify_identity(identity):
      # trust the identity established by the identity policy
      return True

Login and logout
----------------

So now we know how identity gets established, and how it can be
verified. We haven't discussed yet how a user actually logs in to
establish an identity in the first place.

For this, we need two things:

* Some kind of login form. Could be taken care of by client-side code
  or by a server-side view. We leave this as an exercise for the
  reader.

* The view that the login data is submitted to when the user tries to
  log in.

How this works in detail is up to your application. What's common to
login systems is the action we take when the user logs in, and the
action we take when the user logs in. When the user logs in we need to
*remember* their identity on the response, and when the user logs in
we need to *forget* their identity again.

Here is a sketch of how logging in works. Imagine we're in a Morepath
view where we've already retrieved ``username`` and ``password`` from
the request (coming from a login form)::

    # check whether user has password, using password hash and database
    if not user_has_password(username, password):
        return "Sorry, login failed" # or something more fancy

    # now that we've established the user, remember it on the response
    @request.after
    def remember(response):
        identity = morepath.Identity(username)
        request.app.remember_identity(response, request, identity)

This is enough for session-based or cryptographic token-based
authentication.

For cookie-based authentication where the password is sent as a cookie
to the server for each request, we need to make sure to include the
password the user used to log in, so that ``remember`` can then place
it in the cookie so that it can be sent back to the server::

    @request.after
    def remember(response):
        identity = morepath.Identity(username, password=password)
        request.app.remember_identity(response, request, identity)

When you construct the identity using
:class:`morepath.Identity`, you can include any data you want
in the identity object by using keyword parameters.

Logging out
~~~~~~~~~~~

Logging out is easy to implement and will work for any kind of
authentication except for basic auth. You simply call
:meth:`morepath.App.forget_identity` somewhere in the logout view::

  @request.after
  def forget(response):
      request.app.forget_identity(response, request)

This will cause the login information (in cookie-form) to be removed
from the response.

Permissions
-----------

Now that we have a way to establish identity and a way for the user to
log in, we can move on to permissions. Permissions are per view. You
can define rules for your application that determine when a user has a
permission.

Let's say we want two permissions in our application, view and
edit. We define those as plain Python classes::

  class ViewPermission(object):
      pass

  class EditPermission(object):
      pass

.. sidebar:: Permission Hierarchy

  Since permissions are classes they could inherit from each other and
  form some kind of permission hierarchy, but we'll keep things simple
  here. Often a flat permission hierarchy is just fine.

Now we can protect views with those permissions. Let's say we have a
``Document`` model that we can view and edit::

  @App.html(model=Document, permission=ViewPermission)
  def document_view(request, model):
      return "<p>The title is: %s</p>" % model.title

  @App.html(model=Document, name='edit', permission=EditPermission)
  def document_edit(request, model):
      return "some kind of edit form"

This says:

* Only allow access to ``document_view`` if the identity has
  ``ViewPermission`` on the ``Document`` model.

* Only allow allow access to ``document_edit`` if the identity has
  ``EditPermission`` on the ``Document`` model.

Permission rules
----------------

Now that we give people a claimed identity and we have guarded our
views with permissions, we need to establish who has what permissions
where using some rules. We can use the
:meth:`morepath.App.permission_rule` directive to do that.

This is very flexible. Let's look at some examples.

Let's give absolutely everybody view permission on ``Document``::

  @App.permission_rule(model=Document, permission=ViewPermission)
  def document_view_permission(identity, model, permission)
      return True

Let's give only those users that are in a list ``allowed_users`` on
the ``Document`` the edit permission::

  @App.permission_rule(model=Document, permission=EditPermission)
  def document_edit_permission(identity, model, permission):
      return identity.userid in model.allowed_users

This is just is one hypothetical rule. ``allowed_users`` on
``Document`` objects is totally made up and not part of Morepath. Your
application can have any rule at all, using any data, to determine
whether someone has a permission.

Morepath Super Powers Go!
-------------------------

What if we don't want to have to define permissions on a per-model
basis? In our application, we may have a *generic* way to check for
the edit permission on any kind of model. We can easily do that too,
as Morepath knows about inheritance::

  @App.permission_rule(model=object, permission=EditPermission)
  def has_edit_permission(identity, model, permission):
      ... some generic rule ...

This permission function is registered for model ``object``, so will
be valid for *all* models in our application.

What if we want that policy for all models, except ``Document`` where
we want to do something else? We can do that too::

  @App.permission_rule(model=Document, permission=EditPermission)
  def document_edit_permission(identity, model, permission):
      ... some special rule ...

You can also register special rules that depend on identity. If you
pass ``identity=None``, you can can register a permission policy for
when the user has not logged in yet and has no claimed identity::

  @App.permission_rule(model=object, permission=EditPermission, identity=None)
  def has_edit_permission_not_logged_in(identity, model, permission):
      return False

This permission check works in addition to the ones we specified
above.

If you want to defer to a completely generic permission engine, you
could define a permission check that works for *any* permission::

  @App.permission_rule(model=object, permission=object)
  def generic_permission_check(identity, model, permission):
       ... generic rule ...
