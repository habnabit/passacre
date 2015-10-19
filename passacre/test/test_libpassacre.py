# Copyright (c) Aaron Gallagher <_@habnab.it>
# See COPYING for details.

from functools import partial

import pytest

from passacre._libpassacre_impl import (
    _ALGORITHMS, GeneratorError, Generator, MultiBaseError, MultiBase,
    _read_error, ffi)


class AlwaysFailsAllocator(object):
    def __init__(self):
        @ffi.callback('passacre_allocator')
        def alloc(size, ctx):
            return ffi.NULL

        self.callback = alloc

    def buffers(self, count):
        raise NotImplementedError('should be unreachable')

    def one_buffer(self):
        raise NotImplementedError('should be unreachable')


def assert_error_type(cls, errtype, f, *a, **kw):
    with pytest.raises(cls) as excinfo:
        f(*a, **kw)
    assert excinfo.value.args[1] == errtype
    return excinfo.value


def assert_panics(cls, f, *a, **kw):
    value = assert_error_type(cls, 'panic', f, *a, **kw)
    assert 'testing panic' in value.args[2]


assert_multibase_error_type = partial(assert_error_type, MultiBaseError)
assert_multibase_panics = partial(assert_panics, MultiBaseError)
assert_generator_error_type = partial(assert_error_type, GeneratorError)
assert_generator_panics = partial(assert_panics, GeneratorError)


def test_unknown_error_type():
    assert _read_error(-98) == b'unknown error'


def test_passacre_error_panic():
    assert _read_error(-99) == b'passacre_error: panic'


def test_multibase_error_on_failing_allocator():
    mb = MultiBase()
    mb._allocator = AlwaysFailsAllocator
    assert_multibase_error_type('allocator error', mb.encode, '')


def test_generator_error_on_invalid_algorithm(monkeypatch):
    monkeypatch.setitem(_ALGORITHMS, 'invalid', 98)
    assert_generator_error_type('user error', Generator, 'invalid')


def test_generator_panic_on_init(monkeypatch):
    monkeypatch.setitem(_ALGORITHMS, 'panic', 99)
    assert_generator_panics(Generator, 'panic')


def test_generator_error_on_using_scrypt_twice():
    g = Generator('keccak')
    g.use_scrypt(1, 2, 3)
    assert_generator_error_type('user error', g.use_scrypt, 1, 2, 3)


def test_generator_error_on_scrypt_derivation():
    g = Generator('keccak')
    g.use_scrypt(99, 99, 99)
    assert_generator_error_type('scrypt', g.absorb_username_password_site, b'', b'', b'')


def test_generator_error_on_absorbing_data_twice():
    g = Generator('keccak')
    g.absorb_username_password_site(b'', b'', b'')
    assert_generator_error_type('user error', g.absorb_username_password_site, b'', b'', b'')


def test_generator_error_on_absorbing_nulls_too_early():
    g = Generator('keccak')
    assert_generator_error_type('user error', g.absorb_null_rounds, 10)


def test_generator_error_on_squeeze_after_init():
    g = Generator('keccak')
    assert_generator_error_type('user error', g.squeeze, 10)


def test_generator_error_on_squeeze_after_kdf_selection():
    g = Generator('keccak')
    g.use_scrypt(1, 2, 3)
    assert_generator_error_type('user error', g.squeeze, 10)


def test_generator_panic_on_squeeze():
    g = Generator('keccak')
    g.absorb_username_password_site(b'', b'', b'')
    assert_generator_panics(g.squeeze, 99999)
