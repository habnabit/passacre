# Copyright (c) Aaron Gallagher <_@habnab.it>
# See COPYING for details.

import pytest

from passacre import generator, signing_uuid
from passacre.test.test_application import skip_without_skein


@skip_without_skein
def test_patched_skein():
    import skein
    r1 = generator._patch_skein_random(skein.Random(b'123'))
    s1 = r1.read(2)
    r1.getrandbits(32)
    s2 = r1.read(2)
    r2 = skein.Random(b'123')
    assert s1 + s2 != r2.read(4)
    with pytest.raises(ValueError):
        r1.getrandbits(0)
    with pytest.raises(ValueError):
        r1.getrandbits(-1)

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
        return 'spam ' * 4


def test_extend_password_with_yubikey():
    yk = FakeYubiKey()
    password = generator.extend_password_with_yubikey('spam', {'yubikey-slot': 1}, YubiKey=yk)
    assert password == '7370616d207370616d207370616d207370616d20:spam'
    assert yk.challenge == signing_uuid.bytes
    assert yk.slot == 1
