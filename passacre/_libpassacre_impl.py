import sys

from passacre._libpassacre_c import lib as C, ffi
from passacre.compat import unicode


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


@ffi.def_extern()
def python_allocator(size, allocator_handle):
    allocator = ffi.from_handle(allocator_handle)
    return allocator.new_buffer(size)


class SimpleAllocator(object):
    def __init__(self):
        self._buf = []

    def new_buffer(self, size):
        self._buf.append(ffi.new('unsigned char []', size))
        return self._buf[-1]

    def buffers(self, count):
        if len(self._buf) != count:
            raise RuntimeError('expected {}; found {}'.format(count, len(self._buf)))
        return [ffi.buffer(b)[:] for b in self._buf]

    def one_buffer(self):
        return self.buffers(count=1)[0]


ERR_BUF_SIZE = 256


class ContextError(Exception):
    pass


class GeneratorError(Exception):
    pass


class NoScryptPersistence(GeneratorError):
    pass


class MultiBaseError(Exception):
    pass


class Context(object):
    _allocator = SimpleAllocator

    def __init__(self, allocator=C.python_allocator):
        size = C.passacre_ctx_size()
        self._buf = ffi.new('unsigned char []', size)
        self._obj = ffi.cast('CPassacreContext *', self._buf)
        self._check(C.passacre_ctx_init, allocator)
        self._obj = ffi.gc(self._obj, C.passacre_ctx_finished)

    def _check(self, func, *args):
        result = func(self._obj, *args)
        if result:
            self._raise_error(result, ContextError)

    def _read_error(self, code):
        if code == C.PASSACRE_PANIC_ERROR:
            alloc = self._allocator()
            self._check(C.passacre_ctx_describe_last_panic, ffi.new_handle(alloc))
            return alloc.one_buffer().decode('utf-8')
        else:
            err_buf = ffi.new('unsigned char []', ERR_BUF_SIZE)
            copied = C.passacre_error(code, err_buf, ERR_BUF_SIZE)
            return ffi.buffer(err_buf)[:copied].decode('utf-8')

    def _raise_error(self, code, exc_type):
        if not code:
            return
        raise exc_type(code, _ERRORS.get(code), self._read_error(code))

    def bind(self, exc_type, obj):
        return BoundContext(self, exc_type, obj)


class BoundContext(object):
    def __init__(self, context, exc_type, obj):
        self._context = context
        self._exc_type = exc_type
        self._obj = obj

    def check(self, func, *args):
        self._context._raise_error(
            func(self._context._obj, self._obj, *args),
            self._exc_type)


default_context = Context()


class Generator(object):
    _allocator = SimpleAllocator

    def __init__(self, algorithm, scrypt_persist=False, context=default_context):
        if algorithm not in _ALGORITHMS:
            raise ValueError('unknown algorithm', algorithm)
        size = C.passacre_gen_size()
        self._algorithm = algorithm
        self._buf = ffi.new('unsigned char []', size)
        self._context = context.bind(
            GeneratorError,
            ffi.gc(ffi.cast('CPassacreGenerator *', self._buf),
                   C.passacre_gen_finished))
        self._check = self._context.check
        self._check(C.passacre_gen_init, _ALGORITHMS[algorithm])
        self._scrypt_persistence = ffi.NULL
        if scrypt_persist:
            self._scrypt_persistence = ffi.new(
                'unsigned char []', C.passacre_gen_scrypt_buffer_size())

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
        alloc = self._allocator()
        self._check(C.passacre_gen_squeeze_password, mb._context._obj, ffi.new_handle(alloc))
        return alloc.one_buffer().decode('utf-8')

    @property
    def scrypt_persisted(self):
        if self._scrypt_persistence == ffi.NULL:
            return NoScryptPersistence()
        return ffi.buffer(self._scrypt_persistence)[:]


class MultiBase(object):
    _allocator = SimpleAllocator

    def __init__(self, context=default_context):
        size = C.passacre_mb_size()
        self._context = context
        self._buf = ffi.new('unsigned char []', size)
        self._context = context.bind(
            MultiBaseError,
            ffi.gc(ffi.cast('CMultiBase *', self._buf),
                   C.passacre_mb_finished))
        self._check = self._context.check
        self._check(C.passacre_mb_init)

    def enable_shuffle(self):
        self._check(C.passacre_mb_enable_shuffle)

    @property
    def required_bytes(self):
        ret = ffi.new('size_t *')
        self._check(C.passacre_mb_required_bytes, ret)
        return ret[0]

    @property
    def entropy_bits(self):
        ret = ffi.new('size_t *')
        self._check(C.passacre_mb_entropy_bits, ret)
        return ret[0]

    def add_separator(self, separator):
        separator = unicode(separator).encode('utf-8')
        self._check(
            C.passacre_mb_add_base, C.PASSACRE_SEPARATOR,
            separator, len(separator))

    def add_characters(self, characters):
        characters = unicode(characters).encode('utf-8')
        self._check(
            C.passacre_mb_add_base, C.PASSACRE_CHARACTERS,
            characters, len(characters))

    def add_words(self):
        self._check(C.passacre_mb_add_base, C.PASSACRE_WORDS, ffi.NULL, 0)

    def add_sub_multibase(self, other):
        self._check(C.passacre_mb_add_sub_mb, other._context)

    def load_words_from_path(self, path):
        path = unicode(path).encode('utf-8')
        self._check(
            C.passacre_mb_load_words_from_path, path, len(path))

    def encode(self, b):
        alloc = self._allocator()
        self._check(C.passacre_mb_encode_from_bytes, b, len(b), ffi.new_handle(alloc))
        return alloc.one_buffer()
