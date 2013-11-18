import os

from nacl import secret
from passacre import generator

from passacre.compat import iterbytes


def pack_bytes(x, pad):
    ret = bytearray()
    while x:
        ret.append(x % 256)
        x //= 256
    return bytes(ret).ljust(pad, b'\x00')


def pack_nonce(nonce, urandom=os.urandom):
    if nonce >= 256 ** 12:
        raise ValueError('nonce too large', nonce)
    return pack_bytes(nonce, 12) + urandom(12)


def unpack_nonce(nonce):
    ret = 0
    for c in iterbytes(reversed(nonce[:12])):
        ret = c | (ret << 8)
    return ret


class EncryptedFile(object):
    def __init__(self, box, path):
        self.box = box
        self.path = path
        self.nonce = 0

    def read(self):
        with open(self.path, 'rb') as infile:
            nonce = infile.read(24)
            rest = infile.read()
        ret = self.box.decrypt(rest, nonce)
        self.nonce = unpack_nonce(nonce)
        return ret

    def write(self, value):
        self.nonce += 1
        out = self.box.encrypt(value, pack_nonce(self.nonce))
        with open(self.path, 'wb') as outfile:
            outfile.write(out.nonce)
            outfile.write(out.ciphertext)


def box_of_config_and_password(config, password, boxtype=secret.SecretBox):
    site_config = config.get_site('pencrypt', password)
    prng = generator.build_prng(None, password, 'pencrypt', site_config)
    return boxtype(pack_bytes(prng.getrandbits(256), 32))
