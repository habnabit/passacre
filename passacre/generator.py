# Copyright (c) Aaron Gallagher <_@habnab.it>
# See COPYING for details.

import string

from passacre._libpassacre_impl import Generator
from passacre.compat import python_3_encode, hexlify
from passacre.multibase import MultiBase
from passacre import features, signing_uuid


_site_multibase = MultiBase([string.ascii_letters + string.digits + '-_'] * 48)


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
    generator = build_generator(username, password, site, options)
    return generator.squeeze_for_multibase(multibase)


@features.yubikey.check
def extend_password_with_yubikey(password, options, YubiKey=None):
    if YubiKey is None:
        from ykpers import YubiKey
    yk = YubiKey.open_first_key()
    response = yk.hmac_challenge_response(
        signing_uuid.bytes, slot=options['yubikey-slot'])
    return hexlify(response) + ':' + password


def build_generator(username, password, site, options, scrypt_persist=False):
    if options.get('yubikey-slot'):
        password = extend_password_with_yubikey(password, options)
    method = options['method']
    iterations = options['iterations']
    if username is not None:
        username = python_3_encode(username)
    g = Generator(method, scrypt_persist=scrypt_persist)
    if 'scrypt' in options:
        g.use_scrypt(**options['scrypt'])
    g.absorb_username_password_site(
        username, python_3_encode(password), site.encode('idna'))
    g.absorb_null_rounds(iterations)
    return g


def hash_site(password, site, options):
    generator = build_generator(None, password, site, options)
    return generator.squeeze_for_multibase(_site_multibase)
