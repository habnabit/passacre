# Copyright (c) Aaron Gallagher <_@habnab.it>
# See COPYING for details.

from __future__ import unicode_literals

import math
import string

from passacre.compat import python_3_encode, hexlify
from passacre.multibase import MultiBase
from passacre import features, signing_uuid

_some_nulls = b'\x00' * 1024
_site_multibase = MultiBase([string.ascii_letters + string.digits + '-_'] * 48)
_site_multibase_bits = 288


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


# XXX: get this included in pyskein
def _patch_skein_random(prng):
    def getrandbits(n_bits):
        "Patched in implementation of getrandbits for skein."
        if n_bits <= 0:
            raise ValueError('number of bits must be greater than zero')
        n_bytes = (n_bits + 7) // 8
        val = int.from_bytes(prng.read(n_bytes), 'little')
        return val >> (n_bytes * 8 - n_bits)
    prng.getrandbits = getrandbits
    return prng


@features.yubikey.check
def extend_password_with_yubikey(password, options, YubiKey=None):
    if YubiKey is None:
        from ykpers import YubiKey
    yk = YubiKey.open_first_key()
    response = yk.hmac_challenge_response(
        signing_uuid.bytes, slot=options['yubikey-slot'])
    return hexlify(response) + ':' + password


# XXX: refactor into a class per method?
def build_prng(username, password, site, options):
    if options.get('yubikey-slot'):
        password = extend_password_with_yubikey(password, options)
    method = options['method']
    iterations = options['iterations']
    seed = (
        (python_3_encode(username) + b':' if username else b'')
        + python_3_encode(password) + b':'
        + site.encode('idna')
        + (_some_nulls * iterations))

    if method == 'keccak':
        features.keccak.check()
        import keccak
        sponge = keccak.Sponge(64, 1536)
        sponge.absorb(seed)
        return keccak.SpongeRandom(sponge)

    elif method == 'skein':
        features.skein.check()
        import skein
        return _patch_skein_random(skein.Random(seed))

    else:
        raise ValueError('invalid method: %r' % (method,))

def hash_site(password, site, options):
    prng = build_prng(None, password, site, options)
    return _site_multibase.encode(prng.getrandbits(_site_multibase_bits))
