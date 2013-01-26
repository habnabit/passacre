# Copyright (c) Aaron Gallagher <_@habnab.it>
# See COPYING for details.

from passacre.multibase import MultiBase

from unittest import TestCase

digits = '0123456789'
hexdigits = '0123456789abcdef'

class MultiBaseTestCase(TestCase):
    "Tests for the ``passacre.multibase.MultiBase`` class."

    def assertEncodingAndDecoding(self, mb, decoded, encoded):
        "Assert that a ``MultiBase`` encodes and decodes values correspondingly."
        self.assertEqual(mb.encode(decoded), encoded)
        self.assertEqual(mb.decode(encoded), decoded)

    def test_simple_base10(self):
        mb = MultiBase([digits, digits])

        self.assertEqual(mb.max_encodable_value, 99)

        self.assertEncodingAndDecoding(mb, 5, '05')
        self.assertEncodingAndDecoding(mb, 9, '09')
        self.assertEncodingAndDecoding(mb, 36, '36')
        self.assertEncodingAndDecoding(mb, 94, '94')

        self.assertRaises(ValueError, mb.encode, 100)
        self.assertRaises(ValueError, mb.encode, 105)

    def test_simple_base16(self):
        mb = MultiBase([hexdigits, hexdigits])

        self.assertEqual(mb.max_encodable_value, 0xff)

        self.assertEncodingAndDecoding(mb, 0x5, '05')
        self.assertEncodingAndDecoding(mb, 0xc, '0c')
        self.assertEncodingAndDecoding(mb, 0x36, '36')
        self.assertEncodingAndDecoding(mb, 0xfe, 'fe')

        self.assertRaises(ValueError, mb.encode, 0x100)
        self.assertRaises(ValueError, mb.encode, 0x105)

    def test_complex_base(self):
        mb = MultiBase(['abcd', 'abc', 'ab'])  # 4 * 3 * 2 == 24

        self.assertEqual(mb.max_encodable_value, 23)

        self.assertEncodingAndDecoding(mb, 0, 'aaa')
        self.assertEncodingAndDecoding(mb, 5, 'acb')
        self.assertEncodingAndDecoding(mb, 9, 'bbb')
        self.assertEncodingAndDecoding(mb, 11, 'bcb')
        self.assertEncodingAndDecoding(mb, 17, 'ccb')
        self.assertEncodingAndDecoding(mb, 23, 'dcb')

        self.assertRaises(ValueError, mb.encode, 24)

    def test_decoding_exceptions(self):
        mb = MultiBase([digits, digits])

        self.assertRaises(ValueError, mb.decode, '999')
        self.assertRaises(ValueError, mb.decode, '9')
        self.assertRaises(ValueError, mb.decode, '9a')
