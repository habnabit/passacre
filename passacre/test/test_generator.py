# Copyright (c) Aaron Gallagher <_@habnab.it>
# See COPYING for details.

import pytest

from passacre import generator


@pytest.mark.skipif("sys.version_info < (3,)")
def test_patched_skein():
    import skein
    r1 = generator._patch_skein_random(skein.Random(b'123'))
    s1 = r1.read(2)
    r1.getrandbits(32)
    s2 = r1.read(2)
    r2 = skein.Random(b'123')
    assert s1 + s2 != r2.read(4)
    with pytest.raises(ValueError):
        r1.getrandbits(0)
    with pytest.raises(ValueError):
        r1.getrandbits(-1)

def test_invalid_prng_method():
    options = {'method': 'invalid', 'iterations': 12}
    with pytest.raises(ValueError):
        generator.build_prng(None, 'passacre', 'example.com', options)
