.. image:: https://img.shields.io/travis/habnabit/passacre/master.svg?style=flat-square

.. image:: https://img.shields.io/coveralls/habnabit/passacre/master.svg?style=flat-square

.. image:: https://img.shields.io/coverity/scan/4886.svg?style=flat-square

.. image:: https://img.shields.io/pypi/v/passacre.svg?style=flat-square

.. image:: https://img.shields.io/pypi/l/passacre.svg?style=flat-square


========
passacre
========

passacre = password massacre
(i.e. what happens when you use the same password on every site)

Passacre is a method of repeatably deriving a different secure password for every site you use.

The way this works is that passacre takes the site's name, your username, and your master password
and runs them through a cryptographically secure hash function
(either the Keccak sponge function from SHA-3 or Skein/Threefish)
to produce a password unique to that site.
Given the same inputs
(site name, username, and master password),
this process will always produce the same password.
This means that your site passwords never need to be persisted,
and since they're always ephemeral,
you don't have a file containing your passwords that's vulnerable to theft.

Minimal documentation is available `on readthedocs <https://passacre.readthedocs.org/en/latest/>`_.

Here's how to use it for now::

  # for both keccak and skein generation:
  pip install 'passacre'
  # to be able to copy passwords, add the 'clipboard' extra:
  pip install 'passacre[clipboard]'
  # for YubiKey two-factor authentication, add the 'yubikey' extra:
  pip install 'passacre[yubikey]'
  # then set it up:
  mkdir -p ~/.config/passacre
  passacre init ~/.config/passacre/passacre.sqlite
  # then finally:
  passacre generate somesite.com
