# Copyright (c) Aaron Gallagher <_@habnab.it>
# See COPYING for details.

from __future__ import unicode_literals

from binascii import hexlify
import math
import string
import sys

from passacre.multibase import MultiBase

_some_nulls = b'\x00' * 1024
_site_multibase = MultiBase([string.ascii_letters + string.digits + '-_'] * 48)
_site_multibase_bits = 288


if sys.version_info > (3,):
    iter_bytes = iter
    def perhaps_encode(s):
        return s.encode()
else:
    def iter_bytes(s):
        for c in s:
            yield ord(c)
    perhaps_encode = lambda x: x


def generate(username, password, site, options):
    """Generate a password with the passacre method.

    1. A string is generated from ``username:`` (if a username is specified),
       contacenated with ``password:site``, concatentated with 1024 null bytes
       for every iteration.
    2. A pseudo-random number generator is initialized using the string as a
       seed.
    3. The PRNG is asked for an integer below the maximum value that
       ``multibase`` can encode.
    4. That integer is encoded with
       ``multibase`` and the encoded value is returned.
    """

    multibase = options['multibase']
    prng = build_prng(username, password, site, options)

    required_bytes = int(math.ceil(
        math.log(multibase.max_encodable_value + 1, 256)))
    required_bits = required_bytes * 8
    while True:
        password_value = prng.getrandbits(required_bits)
        if password_value <= multibase.max_encodable_value:
            break
    return multibase.encode(password_value)

def generate_from_config(username, password, site, config):
    """Generate a passacre password using a site's specific configuration.

    This works like ``generate``, except taking the ``multibase``,
    ``iterations``, and ``keylen`` parameters from the provided configuration
    dictionary. If ``site`` is not a key in ``config``, this uses the default
    configuration (i.e. ``config['default']``) instead.
    """

    site_config = config.get(site, None)
    if site_config is None:
        hashed_site = hash_site(password, site, config['--site-hashing'])
        site_config = config.get(hashed_site, None)
    if site_config is None:
        site_config = config['default']
    if not username:
        username = site_config.get('username')
    return generate(username, password, site, site_config)

# XXX: refactor into a class per method?

def build_prng(username, password, site, options):
    method = options['method']
    iterations = options['iterations']
    seed = (
        (perhaps_encode(username) + b':' if username else b'')
        + perhaps_encode(password) + b':'
        + perhaps_encode(site)
        + (_some_nulls * iterations))

    if method == 'keccak':
        import keccak
        sponge = keccak.Sponge(64, 1536)
        sponge.absorb(seed)
        return keccak.SpongeRandom(sponge)

    elif method == 'skein':
        import skein
        return skein.Random(seed)

    else:
        raise ValueError('invalid method: %r' % (method,))

def hash_site(password, site, options):
    prng = build_prng(None, password, site, options)
    return _site_multibase.encode(prng.getrandbits(_site_multibase_bits))
