# Copyright (c) Aaron Gallagher <_@habnab.it>
# See COPYING for details.

import string

from passacre.compat import hexlify
from passacre.schema import multibase_of_schema
from passacre import features, signing_uuid, _pyo3_backend


_site_multibase = multibase_of_schema([string.ascii_letters + string.digits + '-_'] * 48)


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

    if options.get('yubikey-slot'):
        password = extend_password_with_yubikey(password, options)
    kdf = {}
    if 'scrypt' in options:
        kdf['scrypt'] = options['scrypt']
    return _pyo3_backend.derive(
        derivation_method=options['method'],
        derivation_kdf=kdf,
        derivation_increment=options['iterations'],
        schema=options['multibase'],
        username=username or '',
        password=password,
        sitename=site,
    )


@features.yubikey.check
def extend_password_with_yubikey(password, options, YubiKey=None):
    if YubiKey is None:
        from ykpers import YubiKey
    yk = YubiKey.open_first_key()
    response = yk.hmac_challenge_response(
        signing_uuid.bytes, slot=options['yubikey-slot'])
    return hexlify(response) + ':' + password


def hash_site(password, site, options):
    options = dict(options, multibase=_site_multibase)
    return generate(None, password, site, options)
