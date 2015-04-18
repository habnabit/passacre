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


@pytest.mark.parametrize(('username', 'password', 'site', 'options', 'expected'), [
    (None, '', 'scrypt.example.com',
     {'method': 'keccak', 'iterations': 10, 'scrypt': {'n': 16, 'r': 1, 'p': 1}},
     ('77d6576238657b203b19ca42c18a0497f16b4844e3074ae8dfdffa3fede21442'
      'fcd0069ded0948f8326a753a0fc81f17e8d3e0fb2e0d3628cf35e20c38d18906')),
    ('NaCl', 'password', 'scrypt2.example.com',
     {'method': 'keccak', 'iterations': 10, 'scrypt': {'n': 1024, 'r': 8, 'p': 16}},
     ('fdbabe1c9d3472007856e7190d01e9fe7c6ad7cbc8237830e77376634b373162'
      '2eaf30d92e22a3886ff109279d9830dac727afb94a83ee6d8360cbdfa2cc0640')),
    (None, '', 'scrypt.example.com',
     {'method': 'skein', 'iterations': 10, 'scrypt': {'n': 16, 'r': 1, 'p': 1}},
     ('77d6576238657b203b19ca42c18a0497f16b4844e3074ae8dfdffa3fede21442'
      'fcd0069ded0948f8326a753a0fc81f17e8d3e0fb2e0d3628cf35e20c38d18906')),
    ('NaCl', 'password', 'scrypt2.example.com',
     {'method': 'skein', 'iterations': 10, 'scrypt': {'n': 1024, 'r': 8, 'p': 16}},
     ('fdbabe1c9d3472007856e7190d01e9fe7c6ad7cbc8237830e77376634b373162'
      '2eaf30d92e22a3886ff109279d9830dac727afb94a83ee6d8360cbdfa2cc0640')),
])
def test_scrypt_persistence(username, password, site, options, expected):
    g = generator.build_generator(username, password, site, options, scrypt_persist=True)
    assert compat.hexlify(g.scrypt_persisted) == expected
