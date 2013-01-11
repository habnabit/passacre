from multibase import MultiBase

from unittest import TestCase

digits = '0123456789'
hexdigits = '0123456789abcdef'

class MultiBaseTestCase(TestCase):
    def assertEncodingAndDecoding(self, mb, decoded, encoded):
        self.assertEqual(mb.encode(decoded), (encoded, 0))
        self.assertEqual(mb.decode(encoded), decoded)

    def test_simple_base10(self):
        mb = MultiBase([digits, digits])

        self.assertEqual(mb.max_encodable_value, 99)

        self.assertEncodingAndDecoding(mb, 5, '05')
        self.assertEncodingAndDecoding(mb, 9, '09')
        self.assertEncodingAndDecoding(mb, 36, '36')
        self.assertEncodingAndDecoding(mb, 94, '94')

        self.assertEqual(mb.encode(105), ('05', 1))
        self.assertEqual(mb.encode(195), ('95', 1))
        self.assertEqual(mb.encode(3305), ('05', 33))
        self.assertEqual(mb.encode(3395), ('95', 33))

    def test_simple_base16(self):
        mb = MultiBase([hexdigits, hexdigits])

        self.assertEqual(mb.max_encodable_value, 0xff)

        self.assertEncodingAndDecoding(mb, 0x5, '05')
        self.assertEncodingAndDecoding(mb, 0xc, '0c')
        self.assertEncodingAndDecoding(mb, 0x36, '36')
        self.assertEncodingAndDecoding(mb, 0xfe, 'fe')

        self.assertEqual(mb.encode(0x105), ('05', 0x1))
        self.assertEqual(mb.encode(0x1f5), ('f5', 0x1))
        self.assertEqual(mb.encode(0x3305), ('05', 0x33))
        self.assertEqual(mb.encode(0x33f5), ('f5', 0x33))

    def test_complex_base(self):
        mb = MultiBase(['abcd', 'abc', 'ab'])  # 4 * 3 * 2 == 24

        self.assertEqual(mb.max_encodable_value, 23)

        self.assertEncodingAndDecoding(mb, 0, 'aaa')
        self.assertEncodingAndDecoding(mb, 5, 'acb')
        self.assertEncodingAndDecoding(mb, 9, 'bbb')
        self.assertEncodingAndDecoding(mb, 11, 'bcb')
        self.assertEncodingAndDecoding(mb, 17, 'ccb')
        self.assertEncodingAndDecoding(mb, 23, 'dcb')

        self.assertEqual(mb.encode(24), ('aaa', 1))
        self.assertEqual(mb.encode(48), ('aaa', 2))
        self.assertEqual(mb.encode(48 + 9), ('bbb', 2))
