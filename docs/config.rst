Configuration
=============

Configuration can be either in YAML or sqlite format.
The default paths searched for configuration files are,
in order::

  ~/.config/passacre/passacre.sqlite
  ~/.config/passacre/passacre.yaml
  ~/.passacre.sqlite
  ~/.passacre.yaml

sqlite is the recommended configuration format.
A new sqlite config will be initialized by default at ``~/.passacre.sqlite`` with the ``passacre init`` command.

Where sqlite uses dotted names,
YAML uses nested mappings.
For example,
to specify ``z`` for the ``x.y`` key in YAML::

  x:
    y: z


Global options
--------------

All of these options are set either as root keys in the YAML document
or with the ``passacre config`` command for sqlite.


``always-confirm-passwords``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Either ``true`` or ``false`` (the default).
If set to ``true``,
any time the user is prompted to enter their password,
a confirmation prompt will ask for the password a second time.
This helps ensure the correct password was entered.


``method``
~~~~~~~~~~

Either ``keccak`` (the default) or ``skein``.
Controls which hash algorithm is used to generate passwords.
This is just a matter of personal preference and
neither one is better.
Can safely be ignored if you don't understand or
don't care.

Both methods are available by default in passacre on either python 2 or python 3.

Any sites which don't specify their own ``method`` in the configuration file will use the global ``method``.
The global ``method`` is also used for hashing site names.


.. _iterations:

``iterations``
~~~~~~~~~~~~~~

The base number of iterations to use for password generation.
It is safe to leave this alone
if you don't know what to do with it.

One iteration corresponds with adding another 1024 null bytes to the input to be hashed.
The default is 1000, though it can be comfortably be set higher.
As Skein/Threefish is a bit faster than Keccak as a pseudo-random number generator,
this value should probably be set higher if ``skein`` is selected as the default ``method``.


``words-file``
~~~~~~~~~~~~~~

A path to a file containing words,
with one word per line.
This is used for generating passwords using the special ``word`` name in the schema.
By default,
there is no ``words-file`` and generating passwords containing words will fail.


.. _site-hashing:

``site-hashing.enabled``
~~~~~~~~~~~~~~~~~~~~~~~~

Either ``true``, ``false``, or ``'always'``.
When looking up a site's configuration information,
this controls whether or not
passacre should try to
find an entry for the site name or
instead hash the site name and find an entry for the resultant hash.

``true`` means that passacre will first try looking for configuration information on the unhashed site name,
then try on the hashed site name.
If no entry is found for either,
passacre will use the default configuration.
``false`` means that passacre will never try to use the hashed site name.
``'always'`` means that passacre will only try to use the hashed site name
and never try looking up an unhashed site name.

Additionally,
``'always'`` is respected by ``passacre site`` and ``passacre config``
when adding, removing, or modifying site configurations;
passacre will act as if the ``--hashed`` flag is always passed.


``site-hashing.method``
~~~~~~~~~~~~~~~~~~~~~~~

The method to use for hashing site names.
Defaults to the same value as ``method`` and has the same semantics.
Safe to disregard if you either don't understand or don't care.


``site-hashing.iterations``
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The number of iterations to use when hashing the site name.
Defaults to the same value as ``iterations`` and has the same semantics.


Site options
------------

All of these options are set under keys corresponding to the site name in the root ``sites`` mapping in the YAML config
or with ``passacre config`` for sqlite.


``method``
~~~~~~~~~~

The method to use for hashing passwords for this site.
Defaults to the same value as ``method`` and has the same semantics.


``iterations``
~~~~~~~~~~~~~~

The number of iterations to use when hashing passwords for this site.
Defaults to the same value as ``iterations`` and has the same semantics.


.. _increment:

``increment``
~~~~~~~~~~~~~

A value which will be added to ``iterations``
in order to find the number of iterations used for hashing the password for a site.
Defaults to 0.
This can be incremented to generate new passwords for the same site and master passphrase combination
without modifying the global ``iterations``.


``schema``
~~~~~~~~~~

The schema used to generate passwords for this site.
Required;
there is no default.
This is set with ``passacre schema`` for sqlite.
See the section on :ref:`password schemata <schemata>` for details of its format.


.. _yubikey-slot:

``yubikey-slot``
~~~~~~~~~~~~~~~~

The configuration slot used for `YubiKey`_ two-factor password generation.
The specified slot must be configured for HMAC challenge/response.
Generating a password for a site will then issue a challenge of the UUID ``dd34b62f-9ed5-597e-85a2-c15d48ed6832``
and prepend the response to the input password being used for generation.


.. _JSON-mini:

JSON-mini
---------

Passacre uses a small superset of `JSON`_ for specifying configuration on the command line.
Syntax is mostly the same,
but with the following changes:

1. Strings don't require quotes for strings composed of just alphanumeric characters, hyphens, and underscores.
   This works for both object keys and string values.
   For example,
   ``{foo-bar: baz}`` is the same as ``{"foo-bar": "baz"}``.
2. The braces are optional for a top-level object.
   For example,
   ``spam: eggs, eggs: spam`` is the same as ``{"spam": "eggs", "eggs": "spam"}``.
   Objects beyond the top level still require braces.
3. ``null`` can also be written as ``%``.


.. _YubiKey: http://www.yubico.com/
.. _JSON: http://json.org/
