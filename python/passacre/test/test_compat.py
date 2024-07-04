# Copyright (c) Aaron Gallagher <_@habnab.it>
# See COPYING for details.

from __future__ import unicode_literals

import pytest

from passacre import compat


@pytest.mark.parametrize(['input', 'expected'], [
    (b'spam', [115, 112, 97, 109]),
    (b's', [115]),
    (b'eggs', [101, 103, 103, 115]),
    (b'', []),
])
def test_iterbytes(input, expected):
    assert list(compat.iterbytes(input)) == expected
