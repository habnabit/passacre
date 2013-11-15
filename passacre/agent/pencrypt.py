import os

from nacl import secret
from passacre import generator


def pack_bytes(x, pad):
    ret = []
    while x:
        ret.append(chr(x % 256))
        x //= 256
    return ''.join(ret).ljust(pad, '\x00')


def pack_nonce(nonce):
    return pack_bytes(nonce, 12) + os.urandom(12)


def unpack_nonce(nonce):
    ret = 0
    for c in reversed(nonce[:12]):
        ret = ord(c) | (ret << 8)
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


def box_of_config_and_password(config, password):
    site_config = config.get_site('pencrypt', password)
    prng = generator.build_prng(None, password, 'pencrypt', site_config)
    box = secret.SecretBox(pack_bytes(prng.getrandbits(256), 32))
    return box
