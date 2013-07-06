# Copyright (c) Aaron Gallagher <_@habnab.it>
# See COPYING for details.

from __future__ import unicode_literals

import random
import math
import sys

_some_nulls = b'\x00' * 1024


if sys.version_info > (3,):
    iter_bytes = iter
    def perhaps_encode(s):
        return s.encode()
else:
    def iter_bytes(s):
        for c in s:
            yield ord(c)
    perhaps_encode = lambda x: x


def int_of_bytes(s):
    "Convert a string of bytes to its integer representation."
    ret = 0
    for c in iter_bytes(s):
        ret = (ret << 8) | c
    return ret

def generate(password, site, options):
    """Generate a password with the passacre method.

    1. A string is generated from ``password:site`` concatentated with 1024
       null bytes for every iteration.
    2. A pseudo-random number generator is initialized using the string as a
       seed.
    3. The PRNG is asked for an integer below the maximum value that
       ``multibase`` can encode.
    4. That integer is encoded with
       ``multibase`` and the encoded value is returned.
    """

    multibase = options['multibase']
    prng = build_prng(password, site, options)

    required_bytes = int(math.ceil(
        math.log(multibase.max_encodable_value + 1, 256)))
    required_bits = required_bytes * 8
    while True:
        password_value = prng.getrandbits(required_bits)
        if password_value <= multibase.max_encodable_value:
            break
    return multibase.encode(password_value)

def generate_from_config(password, site, config):
    """Generate a passacre password using a site's specific configuration.

    This works like ``generate``, except taking the ``multibase``,
    ``iterations``, and ``keylen`` parameters from the provided configuration
    dictionary. If ``site`` is not a key in ``config``, this uses the default
    configuration (i.e. ``config['default']``) instead.
    """

    site_config = config.get(site, None)
    if site_config is None:
        site_config = config['default']
    return generate(password, site, site_config)

class SpongeRandom(random.SystemRandom):
    "A ``random.Random`` subclass which derives its entropy from a sponge."

    def __init__(self, sponge):
        self.sponge = sponge

    def random(self):
        "Get the next sponge-derived number on the range [0.0, 1.0)."
        return self.getrandbits(random.BPF) * random.RECIP_BPF

    def getrandbits(self, n_bits):
        "Generate an integer of ``n_bits`` sponge-squeezed bits."
        if n_bits <= 0:
            raise ValueError('number of bits must be greater than zero')
        n_bytes = (n_bits + 7) // 8
        val = int_of_bytes(self.sponge.squeeze(n_bytes))
        return val >> (n_bytes * 8 - n_bits)

def build_prng(password, site, options):
    method = options.get('method', 'keccak')
    iterations = options.get('iterations', 1000)
    seed = (
        perhaps_encode(password) + b':'
        + perhaps_encode(site)
        + (_some_nulls * iterations))

    if method == 'keccak':
        import keccak
        sponge = keccak.Sponge(64, 1536)
        sponge.absorb(seed)
        return SpongeRandom(sponge)

    elif method == 'skein':
        import skein
        return skein.Random(seed)

    else:
        raise ValueError('invalid method: %r' % (method,))
