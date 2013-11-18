from __future__ import unicode_literals

from collections import namedtuple

import pytest

from passacre.agent import pencrypt
from passacre.compat import iterbytes


Ciphertext = namedtuple('Ciphertext', 'nonce ciphertext')


def jiggle_bytes(s):
    return bytes(bytearray(c ^ 0x42 for c in iterbytes(s)))


class FakeBox(object):
    nonce = None

    def encrypt(self, s, nonce):
        return Ciphertext(nonce, jiggle_bytes(s))

    def decrypt(self, s, nonce):
        self.nonce = nonce
        return jiggle_bytes(s)


def test_fakebox_encryption():
    box = FakeBox()
    assert box.encrypt(b'12#/', b'nonce') == (b'nonce', b'spam')

def test_fakebox_decryption():
    box = FakeBox()
    assert box.decrypt(b'12#/', b'nonce') == b'spam'
    assert box.nonce == b'nonce'


@pytest.mark.parametrize(['x', 'pad', 'expected'], [
    (0, 2, b'\x00\x00'),
    (1, 1, b'\x01'),
    (255, 1, b'\xff'),
    (256, 1, b'\x00\x01'),
    (256, 2, b'\x00\x01'),
    (256, 3, b'\x00\x01\x00'),
    (256, 4, b'\x00\x01\x00\x00'),
    (0xffff, 4, b'\xff\xff\x00\x00'),
])
def test_pack_bytes(x, pad, expected):
    assert pencrypt.pack_bytes(x, pad) == expected


def test_pack_nonce_uses_urandom():
    assert pencrypt.pack_nonce(0, lambda n: b'\xff' * n) == b'\x00' * 12 + b'\xff' * 12

@pytest.mark.parametrize(['nonce', 'expected'], [
    (0, b'\x00' * 24),
    (1, b'\x01' + b'\x00' * 23),
    (256, b'\x00\x01' + b'\x00' * 22),
    (256 ** 12 - 1, b'\xff' * 12 + b'\x00' * 12),
])
def test_pack_nonce(nonce, expected):
    assert pencrypt.pack_nonce(nonce, lambda n: b'\x00' * n) == expected

@pytest.mark.parametrize(['nonce'], [(256 ** 12,), (256 ** 13,)])
def test_pack_nonce_overflow(nonce):
    pytest.raises(ValueError, pencrypt.pack_nonce, nonce)


@pytest.mark.parametrize(['nonce', 'expected'], [
    (b'\x00' * 24, 0),
    (b'\x01' + b'\x00' * 23, 1),
    (b'\x00\x01' + b'\x00' * 22, 256),
    (b'\xff' * 12 + b'\x00' * 12, 256 ** 12 - 1),
    (b'\xff' * 24, 256 ** 12 - 1),
])
def test_unpack_nonce(nonce, expected):
    assert pencrypt.unpack_nonce(nonce) == expected


def test_encrypted_file_read(tmpdir):
    test_file = tmpdir.join('test.txt')
    with test_file.open('wb') as outfile:
        outfile.write(b'\xff' * 24)
        outfile.write(b'12#/')
    box = FakeBox()
    ef = pencrypt.EncryptedFile(box, test_file.strpath)
    assert ef.read() == b'spam'
    assert box.nonce == b'\xff' * 24
    assert ef.nonce == 256 ** 12 - 1

def test_encrypted_file_write(tmpdir):
    test_file = tmpdir.join('test.txt')
    box = FakeBox()
    ef = pencrypt.EncryptedFile(box, test_file.strpath)
    ef.write(b'spam')
    with test_file.open('rb') as infile:
        assert infile.read(12) == b'\x01' + b'\x00' * 11
        infile.read(12)
        assert infile.read() == b'12#/'
