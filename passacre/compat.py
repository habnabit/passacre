import sys


if sys.version_info < (3,):  # pragma: nocover
    input = raw_input
    unichr = unichr
    unicode = unicode
    long = long
    def python_2_encode(s):
        return s.encode()
    def python_3_encode(s):
        return s
else:
    unichr = chr
    unicode = str
    long = int
    def python_2_encode(s):
        return s
    def python_3_encode(s):
        return s.encode()

if sys.version_info < (3, 3):  # pragma: nocover
    import passacre._argparse as argparse
else:  # pragma: nocover
    import argparse


__all__ = [
    'input', 'argparse', 'unichr', 'unicode', 'long',
]
