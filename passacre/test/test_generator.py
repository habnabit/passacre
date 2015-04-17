# Copyright (c) Aaron Gallagher <_@habnab.it>
# See COPYING for details.

import pytest

from passacre import compat, features, generator, signing_uuid


_shush_pyflakes = [features]


def test_invalid_generator_method():
    options = {'method': 'invalid', 'iterations': 12}
    with pytest.raises(ValueError):
        generator.build_generator(None, 'passacre', 'example.com', options)


class FakeYubiKey(object):
    def open_first_key(self):
        return self

    def hmac_challenge_response(self, challenge, slot):
        self.challenge = challenge
        self.slot = slot
        return b'spam ' * 4

skip_without_yubikey = pytest.mark.skipif(
    'not features.yubikey.usable', reason='ykpers not usable')

@skip_without_yubikey
def test_extend_password_with_yubikey():
    yk = FakeYubiKey()
    password = generator.extend_password_with_yubikey('spam', {'yubikey-slot': 1}, YubiKey=yk)
    assert password == '7370616d207370616d207370616d207370616d20:spam'
    assert yk.challenge == signing_uuid.bytes
    assert yk.slot == 1


@pytest.mark.parametrize(('username', 'password', 'site', 'options', 'expected'), [
    (None, '', 'scrypt.example.com',
     {'method': 'keccak', 'iterations': 10, 'scrypt': {'n': 16, 'r': 1, 'p': 1}},
     'c43ca39ad66469184a4023fa7acb64c6263a252318c976ffe7fd1da9cf0ae507'),
    ('NaCl', 'password', 'scrypt2.example.com',
     {'method': 'keccak', 'iterations': 10, 'scrypt': {'n': 1024, 'r': 8, 'p': 16}},
     '7d2b6b44db111e8c302268510c4b7b492e78886d5208cf8dbbcbda56c982eb92'),
    (None, '', 'scrypt.example.com',
     {'method': 'skein', 'iterations': 10, 'scrypt': {'n': 16, 'r': 1, 'p': 1}},
     'aac4c234a392510c20c8379b19fb57583cfc164dae5b714c5067f2d4cbb4aaab'),
    ('NaCl', 'password', 'scrypt2.example.com',
     {'method': 'skein', 'iterations': 10, 'scrypt': {'n': 1024, 'r': 8, 'p': 16}},
     'cff7a6fc473cb6523c413047f8e26d1e23ffc96b9d7b1fe2008b95469ef2eed1'),
])
def test_scrypt_vectors(username, password, site, options, expected):
    g = generator.build_generator(username, password, site, options)
    assert compat.hexlify(g.squeeze(32)) == expected
