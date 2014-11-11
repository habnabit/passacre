import math
import os
import sys

import cffi


ffi = cffi.FFI()
ffi.cdef("""

enum passacre_gen_algorithm {
    PASSACRE_KECCAK,
    PASSACRE_SKEIN,
    ...
};

struct passacre_gen_state;

size_t passacre_gen_size(void);
int passacre_gen_init(struct passacre_gen_state *, enum passacre_gen_algorithm);
int passacre_gen_absorb(struct passacre_gen_state *, unsigned char *, size_t);
int passacre_gen_absorb_null_rounds(struct passacre_gen_state *, size_t);
int passacre_gen_squeeze(struct passacre_gen_state *, unsigned char *, size_t);

""")

preamble = '#include "passacre.h"'
if not os.environ.get('LIBPASSACRE_NO_VERIFY'):
    C = ffi.verify(
        preamble, ext_package='passacre', modulename='_libpassacre_c',
        libraries=['passacre'])

    _ALGORITHMS = {
        'keccak': C.PASSACRE_KECCAK,
        'skein': C.PASSACRE_SKEIN,
    }


if sys.version_info < (3,):  # pragma: nocover
    def int_of_bytes(b):
        ret = 0
        for c in b:
            ret = (ret << 8) | ord(c)
        return ret

else:
    def int_of_bytes(b):
        return int.from_bytes(b, 'big')


class Generator(object):
    def __init__(self, algorithm):
        if algorithm not in _ALGORITHMS:
            raise ValueError('unknown algorithm', algorithm)
        size = C.passacre_gen_size()
        self._algorithm = algorithm
        self._buf = ffi.new('unsigned char []', size)
        self._context = ffi.cast('struct passacre_gen_state *', self._buf)
        C.passacre_gen_init(self._context, _ALGORITHMS[algorithm])

    def absorb(self, b):
        C.passacre_gen_absorb(self._context, b, len(b))

    def absorb_null_rounds(self, rounds):
        C.passacre_gen_absorb_null_rounds(self._context, rounds)

    def squeeze(self, n_bytes):
        output = ffi.new('unsigned char[]', n_bytes)
        C.passacre_gen_squeeze(self._context, output, n_bytes)
        return ffi.buffer(output)[:]

    def squeeze_for_multibase(self, mb):
        required_bytes = int(math.ceil(
            math.log(mb.max_encodable_value + 1, 256)))
        while True:
            value = int_of_bytes(self.squeeze(required_bytes))
            if value <= mb.max_encodable_value:
                break
        return mb.encode(value)
