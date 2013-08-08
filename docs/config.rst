Passacre configuration
======================

Configuration can be either in YAML or sqlite format. The default paths
searched for configuration files are, in order::

  ~/.config/passacre/passacre.sqlite
  ~/.config/passacre/passacre.yaml
  ~/.passacre.sqlite
  ~/.passacre.yaml

sqlite is the recommended configuration format. A new sqlite config will be
initialized by default at ``~/.passacre.sqlite`` with the ``passacre init``
command.

Dotted names are specified in YAML as nested mappings. For example, for
specifing ``z`` for the ``x.y`` key::

  x:
    y: z


Global options
--------------

All of these options are set either as root keys in the YAML document of with
the ``passacre config`` command for sqlite.


``method``
~~~~~~~~~~

Either ``keccak`` (the default) or ``skein``. Controls which hash algorithm is
used to generate passwords. The ``keccak`` method is available on python 2 and
python 3 and requires the `cykeccak`_ package. The ``skein`` method is only
available on python 3 and requires the `pyskein`_ package.

Any sites which don't specify their own ``method`` will use the global
``method``. The global ``method`` is also used for hashing site names.


``iterations``
~~~~~~~~~~~~~~

The base number of iterations to use for password generation. One iteration
corresponds with adding another 1024 null bytes to the input to be hashed. The
default is 1000, though it can be comfortably be set higher. As `pyskein`_ is a
bit faster than `cykeccak`_ as a pseudo-random number generator, this value
should probably be set higher if ``skein`` is selected as the default
``method``.


``words-file``
~~~~~~~~~~~~~~

A path to a file containing words, with one word per line. This is used for
generating passwords using the special ``word`` name in the schema. By default,
there is no ``words-file`` and generating passwords containing words will fail.


``site-hashing.enabled``
~~~~~~~~~~~~~~~~~~~~~~~~

Either ``true``, ``false``, or ``'always'``. This controls whether passacre
will try to hash the site name to look up site-specific configuration. ``true``
means that passacre will first try looking for configuration keyed on the
unhashed site name, then try keyed on the hashed site name before falling back
on the default. ``false`` means that passacre will never try hashing the site
name. ``'always'`` means that passacre will only hash the site name and never
try looking up an unhashed site name.

Additionally, ``'always'`` is respected by ``passacre site`` and ``passacre
config`` when adding, removing, or modifying site configuration: passacre will
act as if the ``--hashed`` flag was always passed.


``site-hashing.method``
~~~~~~~~~~~~~~~~~~~~~~~

The method to use for hashing site names. Defaults to the same value as
``method`` and has the same semantics.


``site-hashing.iterations``
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The number of iterations to use when hashing the site name. Defaults to the
same value as ``iterations`` and has the same semantics.


Site options
------------

All of these options are set under keys corresponding to the site name in the
root ``sites`` mapping in the YAML config or with ``passacre config`` for
sqlite.


``method``
~~~~~~~~~~

The method to use for hashing passwords for this site. Defaults to the same
value as ``method`` and has the same semantics.


``iterations``
~~~~~~~~~~~~~~

The number of iterations to use when hashing passwords for this site. Defaults
to the same value as ``iterations`` and has the same semantics.


``increment``
~~~~~~~~~~~~~

A value which will be added to ``iterations`` in order to find the number of
iterations used for hashing the password for a site. Defaults to 0. This can be
incremented to generate new passwords for the same site and master passphrase
combination without modifying the global ``iterations``.


``schema``
~~~~~~~~~~

The schema used to generate passwords for this site. Required; there is no
default. This is set with ``passacre schema`` for sqlite. See the section on
:ref:`password schemata <schemata>` for details of its format.


.. _cykeccak: https://crate.io/packages/cykeccak/
.. _pyskein: https://crate.io/packages/pyskein/