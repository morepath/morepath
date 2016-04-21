``morepath.directive`` -- Extension API
=======================================

.. automodule:: morepath.directive

Registry classes
----------------

.. autoclass:: morepath.directive.ConverterRegistry
  :members:

.. autoclass:: morepath.directive.IdentityPolicyRegistry
  :members:

.. autoclass:: morepath.directive.PathRegistry
  :members:

.. autoclass:: morepath.directive.PredicateRegistry
  :members:

.. autoclass:: morepath.directive.RegRegistry
  :members:

.. autoclass:: morepath.directive.SettingRegistry
  :members:

.. autoclass:: morepath.directive.TemplateEngineRegistry
  :members:

.. autoclass:: morepath.directive.TweenRegistry
  :members:

.. autoclass:: morepath.directive.ViewRegistry
  :members:

Action classes
--------------

To instantiate an action you need to give it the same arguments as the
directive it implements. Reading the source of existing actions is
helpful when you want to implement your own actions. See
``morepath/directive.py``.

.. py:class:: SettingAction

  :meth:`morepath.App.setting`

.. py:class:: SettingSectionAction

  :meth:`morepath.App.setting_section`

.. py:class:: PredicateFallbackAction

  :meth:`morepath.App.predicate_fallback`

.. py:class:: PredicateAction

  :meth:`morepath.App.predicate`

.. py:class:: FunctionAction

  :meth:`morepath.App.function`

.. py:class:: ConverterAction

  :meth:`morepath.App.converter`

.. py:class:: PathAction

  Helps to implement :meth:`morepath.App.path`

.. py:class:: PathCompositeAction

  :meth:`morepath.App.path`

.. py:class:: PermissionRuleAction

  :meth:`morepath.App.permission_rule`

.. py:class:: TemplateDirectoryAction

  :meth:`morepath.App.template_directory`

.. py:class:: TemplateLoaderAction

  :meth:`morepath.App.template_loader`

.. py:class:: TemplateRenderAction

  :meth:`morepath.App.template_render`

.. py:class:: ViewAction

  :meth:`morepath.App.view`

.. py:class:: JsonAction

  :meth:`morepath.App.json`

.. py:class:: HtmlAction

  :meth:`morepath.App.html`

.. py:class:: MountAction

  :meth:`morepath.App.mount`

.. py:class:: DeferLinksAction

  :meth:`morepath.App.defer_links`

.. py:class:: DeferClassLinksAction

  :meth:`morepath.App.defer_class_links`

.. py:class:: TweenFactoryAction

  :meth:`morepath.App.tween_factory`

.. py:class:: IdentityPolicyFunctionAction

  Helps to implement :meth:`morepath.App.identity_policy`

.. py:class:: IdentityPolicyAction

  :meth:`morepath.App.identity_policy`

.. py:class:: VerifyIdentityAction

  :meth:`morepath.App.verify_identity`

.. py:class:: DumpJsonAction

  :meth:`morepath.App.dump_json`

.. py:class:: LoadJsonAction

  :meth:`morepath.App.load_json`

.. py:class:: LinkPrefixAction

  :meth:`morepath.App.link_prefix`
