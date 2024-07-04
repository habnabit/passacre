.. _schemata:

Password schemata
=================

Schemata are represented as nested lists with the following grammar.
``items`` is the root production.

.. raw:: html

   <link rel="stylesheet" href="_static/railroad-diagrams.css">

   <h4>items</h4>
   <svg class="railroad-diagram" width="269" height="71" ><g transform="translate(.5 .5)" ><path d="M 20 21 v 20 m 10 -20 v 20 m -10 -10 h 20.5" ></path><g ><path d="M40 31h0" ></path><path d="M228 31h0" ></path><path d="M40 31h10" ></path><g ><path d="M50 31h0" ></path><path d="M78 31h0" ></path><rect x="50" y="20" width="28" height="22" rx="10" ry="10" ></rect><text x="64" y="35" >[</text></g><path d="M78 31h10" ></path><path d="M88 31h10" ></path><g ><path d="M98 31h0" ></path><path d="M170 31h0" ></path><path d="M98 31h10" ></path><g ><path d="M108 31h0" ></path><path d="M160 31h0" ></path><rect x="108" y="20" width="52" height="22" ></rect><text x="134" y="35" >item</text></g><path d="M160 31h10" ></path><path d="M108 31a10 10 0 0 0 -10 10v0a10 10 0 0 0 10 10" ></path><g ><path d="M108 51h52" ></path></g><path d="M160 51a10 10 0 0 0 10 -10v0a10 10 0 0 0 -10 -10" ></path></g><path d="M170 31h10" ></path><path d="M180 31h10" ></path><g ><path d="M190 31h0" ></path><path d="M218 31h0" ></path><rect x="190" y="20" width="28" height="22" rx="10" ry="10" ></rect><text x="204" y="35" >]</text></g><path d="M218 31h10" ></path></g><path d="M 228 31 h 20 m -10 -10 v 20 m 10 -20 v 20" ></path></g></svg>

   <h4>item</h4>
   <svg class="railroad-diagram" width="521" height="151" ><g transform="translate(.5 .5)" ><path d="M 20 21 v 20 m 10 -20 v 20 m -10 -10 h 20.5" ></path><g ><path d="M40 31h0" ></path><path d="M480 31h0" ></path><path d="M40 31h20" ></path><g ><path d="M60 31h166" ></path><path d="M294 31h166" ></path><rect x="226" y="20" width="68" height="22" rx="10" ry="10" ></rect><text x="260" y="35" >"word"</text></g><path d="M460 31h20" ></path><path d="M40 31a10 10 0 0 1 10 10v10a10 10 0 0 0 10 10" ></path><g ><path d="M60 61h134" ></path><path d="M326 61h134" ></path><rect x="194" y="50" width="132" height="22" ></rect><text x="260" y="65" >character-sets</text></g><path d="M460 61a10 10 0 0 0 10 -10v-10a10 10 0 0 1 10 -10" ></path><path d="M40 31a10 10 0 0 1 10 10v40a10 10 0 0 0 10 10" ></path><g ><path d="M60 91h0" ></path><path d="M460 91h0" ></path><path d="M60 91h10" ></path><g ><path d="M70 91h0" ></path><path d="M98 91h0" ></path><rect x="70" y="80" width="28" height="22" rx="10" ry="10" ></rect><text x="84" y="95" >[</text></g><path d="M98 91h10" ></path><g ><path d="M108 91h0" ></path><path d="M240 91h0" ></path><path d="M108 91h20" ></path><g ><path d="M128 91h92" ></path></g><path d="M220 91h20" ></path><path d="M108 91a10 10 0 0 1 10 10v0a10 10 0 0 0 10 10" ></path><g ><path d="M128 111h0" ></path><path d="M220 111h0" ></path><rect x="128" y="100" width="92" height="22" rx="10" ry="10" ></rect><text x="174" y="115" >delimiter</text></g><path d="M220 111a10 10 0 0 0 10 -10v0a10 10 0 0 1 10 -10" ></path></g><path d="M240 91h10" ></path><g ><path d="M250 91h0" ></path><path d="M310 91h0" ></path><rect x="250" y="80" width="60" height="22" rx="10" ry="10" ></rect><text x="280" y="95" >count</text></g><path d="M310 91h10" ></path><path d="M320 91h10" ></path><g ><path d="M330 91h0" ></path><path d="M402 91h0" ></path><path d="M330 91h10" ></path><g ><path d="M340 91h0" ></path><path d="M392 91h0" ></path><rect x="340" y="80" width="52" height="22" ></rect><text x="366" y="95" >item</text></g><path d="M392 91h10" ></path><path d="M340 91a10 10 0 0 0 -10 10v0a10 10 0 0 0 10 10" ></path><g ><path d="M340 111h52" ></path></g><path d="M392 111a10 10 0 0 0 10 -10v0a10 10 0 0 0 -10 -10" ></path></g><path d="M402 91h10" ></path><path d="M412 91h10" ></path><g ><path d="M422 91h0" ></path><path d="M450 91h0" ></path><rect x="422" y="80" width="28" height="22" rx="10" ry="10" ></rect><text x="436" y="95" >]</text></g><path d="M450 91h10" ></path></g><path d="M460 91a10 10 0 0 0 10 -10v-40a10 10 0 0 1 10 -10" ></path></g><path d="M 480 31 h 20 m -10 -10 v 20 m 10 -20 v 20" ></path></g></svg>

   <h4>character-sets</h4>
   <svg class="railroad-diagram" width="381" height="101" ><g transform="translate(.5 .5)" ><path d="M 20 21 v 20 m 10 -20 v 20 m -10 -10 h 20.5" ></path><g ><path d="M40 31h0" ></path><path d="M340 31h0" ></path><path d="M40 31h20" ></path><g ><path d="M60 31h68" ></path><path d="M252 31h68" ></path><rect x="128" y="20" width="124" height="22" ></rect><text x="190" y="35" >character-set</text></g><path d="M320 31h20" ></path><path d="M40 31a10 10 0 0 1 10 10v10a10 10 0 0 0 10 10" ></path><g ><path d="M60 61h0" ></path><path d="M320 61h0" ></path><path d="M60 61h10" ></path><g ><path d="M70 61h0" ></path><path d="M98 61h0" ></path><rect x="70" y="50" width="28" height="22" rx="10" ry="10" ></rect><text x="84" y="65" >[</text></g><path d="M98 61h10" ></path><path d="M108 61h10" ></path><g ><path d="M118 61h0" ></path><path d="M262 61h0" ></path><path d="M118 61h10" ></path><g ><path d="M128 61h0" ></path><path d="M252 61h0" ></path><rect x="128" y="50" width="124" height="22" ></rect><text x="190" y="65" >character-set</text></g><path d="M252 61h10" ></path><path d="M128 61a10 10 0 0 0 -10 10v0a10 10 0 0 0 10 10" ></path><g ><path d="M128 81h124" ></path></g><path d="M252 81a10 10 0 0 0 10 -10v0a10 10 0 0 0 -10 -10" ></path></g><path d="M262 61h10" ></path><path d="M272 61h10" ></path><g ><path d="M282 61h0" ></path><path d="M310 61h0" ></path><rect x="282" y="50" width="28" height="22" rx="10" ry="10" ></rect><text x="296" y="65" >]</text></g><path d="M310 61h10" ></path></g><path d="M320 61a10 10 0 0 0 10 -10v-10a10 10 0 0 1 10 -10" ></path></g><path d="M 340 31 h 20 m -10 -10 v 20 m 10 -20 v 20" ></path></g></svg>

   <h4>character-set</h4>
   <svg class="railroad-diagram" width="261" height="92" ><g transform="translate(.5 .5)" ><path d="M 20 21 v 20 m 10 -20 v 20 m -10 -10 h 20.5" ></path><g ><path d="M40 31h0" ></path><path d="M220 31h0" ></path><path d="M40 31h20" ></path><g ><path d="M60 31h0" ></path><path d="M200 31h0" ></path><rect x="60" y="20" width="140" height="22" rx="10" ry="10" ></rect><text x="130" y="35" >character class</text></g><path d="M200 31h20" ></path><path d="M40 31a10 10 0 0 1 10 10v10a10 10 0 0 0 10 10" ></path><g ><path d="M60 61h20" ></path><path d="M180 61h20" ></path><rect x="80" y="50" width="100" height="22" rx="10" ry="10" ></rect><text x="130" y="65" >characters</text></g><path d="M200 61a10 10 0 0 0 10 -10v-10a10 10 0 0 1 10 -10" ></path></g><path d="M 220 31 h 20 m -10 -10 v 20 m 10 -20 v 20" ></path></g></svg>

Definitions
-----------

+----------------+------------------------------------------------------------+
|Name            |Meaning                                                     |
+================+============================================================+
|"word"          |the literal string ``"word"``                               |
+----------------+------------------------------------------------------------+
|delimiter       |a string which will be used between every item in this      |
|                |counted group                                               |
+----------------+------------------------------------------------------------+
|count           |an integer of the number of times to repeat the items in    |
|                |this group                                                  |
+----------------+------------------------------------------------------------+
|character class |one of ``printable``, ``alphanumeric``, ``digit``,          |
|                |``letter``, ``uppercase``, ``lowercase``, or ``symbols``    |
|                |corresponding to different ranges of ASCII characters       |
+----------------+------------------------------------------------------------+
|characters      |a string representing a set of characters                   |
+----------------+------------------------------------------------------------+


Examples
--------

All examples are given in :ref:`JSON-mini` format.

A basic password of 12 alphanumeric characters would be represented like so::

  [[12, alphanumeric]]

In this example, there is one ``item`` in the ``items`` list,
and that item is ``[12, alphanumeric]``.
The string ``"alphanumeric"`` is a character class.

Another simple example is four space-delimited words::

  [[" ", 4, word]]

Again, there is one ``item``.
Normally there is no delimiter between repeated elements,
but an ``item`` where the first element is a string indicates that its contents should be delimited with the first element as a delimiter.
The string ``word`` is itself a special ``item`` which indicates that something should be selected from the word list.

A slightly more complex example is 12 hexadecimal digits::

  [[12, [digit, "abcdef"]]]

And again, there is one ``item``.
The list ``[digit, "abcdef"]`` is a ``character-sets`` with two ``character-set``\ s in it:
``digit`` is a character class ``character-set``,
and ``"abcdef"``,
since it does not match any character class name,
matches the literal characters.

Another more complex example is a series of four words,
separated by spaces,
and with each word followed by a single digit::

  [[" ", 4, word, digit]]

Here,
there are multiple nested ``item``\ s in the ``item`` ``[" ", 4, word, digit]``:
``word`` and ``digit``.
These two items will be concatenated together before being delimited by spaces.
For example,
this might produce the string ``spam1 spam2 eggs3 spam4``.

One way of expressing a 12-character password that requires at least one letter and one digit is::

  [[uppercase, lowercase], digit, [10, alphanumeric]]

This series of ``items`` has three ``item``\ s in it:
``[uppercase, lowercase]``, ``digit``, and ``[10, alphanumeric]``.
For example, this might produce the string ``a1spam9EGGS9``.
