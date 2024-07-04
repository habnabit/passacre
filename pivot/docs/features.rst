.. _features:

Features
========


``yaml``
--------

Reading of YAML files for configuration.
It is preferred to use sqlite configuration over YAML configuration,
but this option is still available for use.

This feature requires the |pyyaml|_ module.


``clipboard``
-------------

Copying of generated passwords.
``passacre generate`` has options for configuring whether and for how long generated passwords are copied.

This feature requires the |xerox|_ module.


``yubikey``
-----------

Two-factor password generation via a YubiKey.
The :ref:`yubikey-slot` site configuration option can be specified to involve a YubiKey in generating a password for a particular site.

This feature requires the |ykpers-cffi|_ module.


.. |pyyaml| replace:: ``pyyaml``
.. _pyyaml: https://pypi.python.org/pypi/pyyaml
.. |xerox| replace:: ``xerox``
.. _xerox: https://pypi.python.org/pypi/xerox
.. |ykpers-cffi| replace:: ``ykpers-cffi``
.. _ykpers-cffi: https://pypi.python.org/pypi/ykpers-cffi
