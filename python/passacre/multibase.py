# Copyright (c) Aaron Gallagher <_@habnab.it>
# See COPYING for details.

from __future__ import unicode_literals

class MultiBase(object):
    """Represents a base where not every digit has the same possible values.

    The ``bases`` parameter must be a sequence of strings, where each item in
    the sequence represents one digit, in order from most significant digit to
    least significant digit. Each character in each string represents one
    possible value for the corresponding digit, in order from the lowest to
    highest value for that digit.

    The ``max_encodable_value`` attribute is the largest integer that can be
    encoded with this base.
    """

    def __init__(self, bases):
        self.bases = bases

    def encode(self, n):
        """Encode an integer to a string, using this base.

        The ``n`` parameter must be an integer. Returns the encoded string, or
        raises ``ValueError`` if ``n`` is greater than the largest encodable
        integer.
        """

        if n > self.max_encodable_value:
            raise ValueError(
                '%d is greater than the largest encodable integer (%d)' % (
                    n, self.max_encodable_value))
        ret = []
        for base in reversed(self.bases):
            n, d = divmod(n, len(base))
            ret.append(base[d])
        ret.reverse()
        return ''.join(ret)

    def decode(self, x):
        """Decode a string to an integer, using this base.

        The ``x`` parameter must be a string as long as the ``bases`` sequence.
        Returns the decoded integer or raises ``ValueError`` if the length of
        ``x`` is not equal to the length of ``bases`` or any of the characters
        in ``x`` aren't valid digits for their position.
        """

        if len(x) != len(self.bases):
            raise ValueError(
                "the length of %r (%d) doesn't match the number of bases (%d)" % (
                    x, len(x), len(self.bases)))
        ret = 0
        for base, d in zip(self.bases, x):
            ret = (ret * len(base)) + base.index(d)
        return ret

    @property
    def max_encodable_value(self):
        ret = 1
        for base in self.bases:
            ret *= len(base)
        return ret - 1
