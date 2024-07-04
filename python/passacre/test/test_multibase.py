# Copyright (c) Aaron Gallagher <_@habnab.it>
# See COPYING for details.

import pytest

from passacre.multibase import MultiBase

digits = '0123456789'
hexdigits = '0123456789abcdef'


bases = [
    {
        'mb': MultiBase([digits, digits]),
        'max_encodable_value': [99],
        'decoded_encoded': [
            (5, '05'),
            (9, '09'),
            (36, '36'),
            (94, '94'),
        ],
        'encoding_failure': [100, 105],
        'decoding_failure': ['999', '9', '9a'],
    }, {
        'mb': MultiBase([hexdigits, hexdigits]),
        'max_encodable_value': [0xff],
        'decoded_encoded': [
            (0x5, '05'),
            (0xc, '0c'),
            (0x36, '36'),
            (0xfe, 'fe'),
        ],
        'encoding_failure': [0x100, 0x105],
    }, {
        'mb': MultiBase(['abcd', 'abc', 'ab']),  # 4 * 3 * 2 == 24
        'max_encodable_value': [23],
        'decoded_encoded': [
            (0, 'aaa'),
            (5, 'acb'),
            (9, 'bbb'),
            (11, 'bcb'),
            (17, 'ccb'),
            (23, 'dcb'),
        ],
        'encoding_failure': [24],
    },
]


def pytest_generate_tests(metafunc):
    key = getattr(metafunc.function, '_uses', None)
    if key is None:
        return
    metafunc.parametrize(
        ('mb', key),
        [(base['mb'], value) for base in bases for value in base.get(key, ())])


def uses_each(key):
    def deco(func):
        func._uses = key
        return func
    return deco


@uses_each('max_encodable_value')
def test_max_encodable_value(mb, max_encodable_value):
    assert mb.max_encodable_value == max_encodable_value


@uses_each('decoded_encoded')
def test_encoding(mb, decoded_encoded):
    decoded, encoded = decoded_encoded
    assert mb.encode(decoded) == encoded


@uses_each('decoded_encoded')
def test_decoding(mb, decoded_encoded):
    decoded, encoded = decoded_encoded
    assert mb.decode(encoded) == decoded


@uses_each('encoding_failure')
def test_encoding_failures(mb, encoding_failure):
    with pytest.raises(ValueError):
        mb.encode(encoding_failure)


@uses_each('decoding_failure')
def test_decoding_failures(mb, decoding_failure):
    with pytest.raises(ValueError):
        mb.decode(decoding_failure)
