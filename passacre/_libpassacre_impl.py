import math
import sys

from passacre._libpassacre_c import lib as C, ffi


_ALGORITHMS = {
    'keccak': C.PASSACRE_KECCAK,
    'skein': C.PASSACRE_SKEIN,
}

_ERRORS = {
    C.PASSACRE_PANIC_ERROR: 'panic',
    C.PASSACRE_KECCAK_ERROR: 'keccak',
    C.PASSACRE_SKEIN_ERROR: 'skein',
    C.PASSACRE_SCRYPT_ERROR: 'scrypt',
    C.PASSACRE_USER_ERROR: 'user error',
    C.PASSACRE_INTERNAL_ERROR: 'internal error',
    C.PASSACRE_DOMAIN_ERROR: 'domain error',
    C.PASSACRE_ALLOCATOR_ERROR: 'allocator error',
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


class SimpleAllocator(object):
    def __init__(self):
        self._buf = []

        @ffi.callback('passacre_allocator', error=ffi.NULL)
        def alloc(size, ctx):
            self._buf.append(ffi.new('unsigned char []', size))
            return self._buf[-1]

        self.callback = alloc

    def buffers(self, count):
        if len(self._buf) != count:
            raise RuntimeError('expected {}; found {}'.format(count, len(self._buf)))
        return [ffi.buffer(b)[:] for b in self._buf]

    def one_buffer(self):
        return self.buffers(count=1)[0]


ERR_BUF_SIZE = 256


class GeneratorError(Exception):
    pass


class NoScryptPersistence(GeneratorError):
    pass


class MultiBaseError(Exception):
    pass


def _read_error(code):
    err_buf = ffi.new('unsigned char []', ERR_BUF_SIZE)
    copied = C.passacre_error(code, err_buf, ERR_BUF_SIZE)
    return ffi.buffer(err_buf)[:copied].decode('utf-8')


def _raise_error(code, exc_type):
    raise exc_type(code, _ERRORS.get(code), _read_error(code))


def _gc_generator(gen):
    result = C.passacre_gen_finished(gen)
    if result:
        _raise_error(result, GeneratorError)


class Generator(object):
    _allocator = SimpleAllocator

    def __init__(self, algorithm, scrypt_persist=False):
        if algorithm not in _ALGORITHMS:
            raise ValueError('unknown algorithm', algorithm)
        size = C.passacre_gen_size()
        self._algorithm = algorithm
        self._buf = ffi.new('unsigned char []', size)
        self._context = ffi.cast('struct passacre_gen_state *', self._buf)
        self._check(C.passacre_gen_init, _ALGORITHMS[algorithm])
        self._context = ffi.gc(self._context, _gc_generator)
        self._scrypt_persistence = ffi.NULL
        if scrypt_persist:
            self._scrypt_persistence = ffi.new(
                'unsigned char []', C.passacre_gen_scrypt_buffer_size())

    def _check(self, func, *args):
        result = func(self._context, *args)
        if result:
            _raise_error(result, GeneratorError)

    def use_scrypt(self, n, r, p):
        self._check(
            C.passacre_gen_use_scrypt, n, r, p, self._scrypt_persistence)

    def absorb_username_password_site(self, username, password, site):
        if username is None:
            username = ffi.NULL
            username_length = 0
        else:
            username_length = len(username)
        self._check(
            C.passacre_gen_absorb_username_password_site,
            username, username_length, password, len(password), site, len(site))

    def absorb_null_rounds(self, rounds):
        self._check(C.passacre_gen_absorb_null_rounds, rounds)

    def squeeze(self, n_bytes):
        output = ffi.new('unsigned char []', n_bytes)
        self._check(C.passacre_gen_squeeze, output, n_bytes)
        return ffi.buffer(output)[:]

    def squeeze_for_multibase(self, mb):
        required_bytes = int(math.ceil(
            math.log(mb.max_encodable_value + 1, 256)))
        while True:
            value = int_of_bytes(self.squeeze(required_bytes))
            if value <= mb.max_encodable_value:
                break
        return mb.encode(value)

    def squeeze_password(self, mb):
        alloc = self._allocator()
        self._check(C.passacre_gen_squeeze_password, mb._context, alloc.callback, ffi.NULL)
        return alloc.one_buffer()

    @property
    def scrypt_persisted(self):
        if self._scrypt_persistence == ffi.NULL:
            return NoScryptPersistence()
        return ffi.buffer(self._scrypt_persistence)[:]


def _gc_multibase(mb):
    result = C.passacre_mb_finished(mb)
    if result:
        _raise_error(result, MultiBaseError)


class MultiBase(object):
    _allocator = SimpleAllocator

    def __init__(self):
        size = C.passacre_mb_size()
        self._buf = ffi.new('unsigned char []', size)
        self._context = ffi.cast('struct passacre_mb_state *', self._buf)
        self._check(C.passacre_mb_init)
        self._context = ffi.gc(self._context, _gc_multibase)

    def _check(self, func, *args):
        result = func(self._context, *args)
        if result:
            _raise_error(result, MultiBaseError)

    @property
    def required_bytes(self):
        ret = ffi.new('size_t *')
        self._check(C.passacre_mb_required_bytes, ret)
        return ret[0]

    def add_separator(self, separator):
        self._check(
            C.passacre_mb_add_base, C.PASSACRE_SEPARATOR,
            separator, len(separator))

    def add_characters(self, characters):
        self._check(
            C.passacre_mb_add_base, C.PASSACRE_CHARACTERS,
            characters, len(characters))

    def add_words(self):
        self._check(C.passacre_mb_add_base, C.PASSACRE_WORDS, ffi.NULL, 0)

    def load_words_from_path(self, path):
        self._check(
            C.passacre_mb_load_words_from_path, path, len(path))

    def encode(self, b):
        alloc = self._allocator()
        self._check(C.passacre_mb_encode_from_bytes, b, len(b), alloc.callback, ffi.NULL)
        return alloc.one_buffer()
