.. image:: https://travis-ci.org/habnabit/passacre.png

.. image:: https://coveralls.io/repos/habnabit/passacre/badge.png?branch=master


========
passacre
========

passacre = password massacre
(i.e. what happens when you use the same password on every site)

hi!!

I really love supergenpass, but the implementation leaves some things to be desired.
feverish (and possibly delirious),
I hacked up a little proof-of-concept thing.

the gist of it is that passacre uses the Keccak sponge function
to repeatably derive a value from your master password and a site name,
and then encodes that value using a password schema
(since different sites have different (and terrible) password requirements).

also, it's ISC-licensed!

every user-facing part of this sucks right now, but it's a work-in-progress.

minimal documentation available `on readthedocs <https://passacre.readthedocs.org/en/latest/>`_.

here's how to use it for now::

  # for keccak generation
  pip install 'passacre[keccak]'
  # for skein generation (python 3 only)
  pip install 'passacre[skein]'
  # to be able to copy passwords, add the 'clipboard' variant too:
  pip install 'passacre[cli,clipboard,keccak]'
  # then set it up:
  mkdir -p ~/.config/passacre
  passacre init ~/.config/passacre/passacre.sqlite
  # then finally:
  passacre generate somesite.com
