import keccak
import math

_some_nulls = '\x00' * 1024

def int_of_bytes(s):
    "Convert a string of bytes to its integer representation."
    ret = 0
    for c in s:
        ret = (ret << 8) | ord(c)
    return ret

def generate(password, site, multibase, iterations=1000):
    """Generate a password with the passacre method.

    1. A Keccak sponge is initialized with rate 64 and capacity 1536.
    2. The sponge absorbs ``password:site``.
    3. The sponge absorbs 1024 null bytes for every iteration.
    4. Enough bytes are squeezed out of the sponge to represent any value that
       ``multibase`` can encode.
    5. Those bytes are encoded with ``multibase`` and the encoded value is
       returned.
    """

    sponge = keccak.Sponge(64, 1536)
    sponge.absorb(password)
    sponge.absorb(':')
    sponge.absorb(site)
    for x in xrange(iterations):
        sponge.absorb(_some_nulls)
    required_bytes = int(math.ceil(math.log(multibase.max_encodable_value + 1, 256)))
    while True:
        password_value = int_of_bytes(sponge.squeeze(required_bytes))
        if password_value <= multibase.max_encodable_value:
            break
    return multibase.encode(password_value)

def generate_from_config(password, site, config):
    """Generate a passacre password using a site's specific configuration.

    This works like ``generate``, except taking the ``multibase``,
    ``iterations``, and ``keylen`` parameters from the provided configuration
    dictionary. If ``site`` is not a key in ``config``, this uses the default
    configuration (i.e. ``config['default']``) instead.
    """

    site_config = config.get(site, None)
    if site_config is None:
        site_config = config['default']
    return generate(password, site, **site_config)
