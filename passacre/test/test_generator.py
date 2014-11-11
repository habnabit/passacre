# Copyright (c) Aaron Gallagher <_@habnab.it>
# See COPYING for details.

import pytest

from passacre import features, generator, signing_uuid


_shush_pyflakes = [features]


def test_invalid_prng_method():
    options = {'method': 'invalid', 'iterations': 12}
    with pytest.raises(ValueError):
        generator.build_prng(None, 'passacre', 'example.com', options)


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
