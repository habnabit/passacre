.. _features:

Features
========


``keccak``
----------

Generation of passwords using the Keccak sponge function.
This is the default password generation method,
and either this feature or ``skein`` must be usable for password generation.

This feature requires the |cykeccak|_ module.


``skein``
---------

Generation of passwords using the Skein hash function.
Either this feature or ``keccak`` must be usable for password generation.

This feature requires the |pyskein|_ module.


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


``agent``
---------

An agent for caching credentials for generating passwords.
The idea is that a running passacre-agent will hold in memory the password used for generating other passwords,
and passacre can communicate with it to request generation of a password.

This feature requires the `AMP`_ module from `Twisted`_
(i.e. ``twisted.protocols.amp``)
and the |crochet|_ module.


``site_list``
-------------

A cached list of sites.
passacre can persist an encrypted list of the sites for which a password has been generated.
This is useful for keeping track of what the hashed sites in a config file are.
If specified to ``passacre-generate``,
passacre-agent will save a site name to the site list after generating a password.

This feature requires the |pynacl|_ module.


.. |cykeccak| replace:: ``cykeccak``
.. _cykeccak: https://pypi.python.org/pypi/cykeccak
.. |pyskein| replace:: ``pyskein``
.. _pyskein: https://pypi.python.org/pypi/pyskein
.. |pyyaml| replace:: ``pyyaml``
.. _pyyaml: https://pypi.python.org/pypi/pyyaml
.. |xerox| replace:: ``xerox``
.. _xerox: https://pypi.python.org/pypi/xerox
.. |ykpers-cffi| replace:: ``ykpers-cffi``
.. _ykpers-cffi: https://pypi.python.org/pypi/ykpers-cffi
.. _AMP: http://amp-protocol.net
.. _Twisted: http://twistedmatrix.net
.. |crochet| replace:: ``crochet``
.. _crochet: https://pypi.python.org/pypi/crochet
.. |pynacl| replace:: ``pynacl``
.. _pynacl: https://pypi.python.org/pypi/pynacl
