import pbkdf2

def int_of_bytes(s):
    "Convert a string of bytes to its integer representation."
    ret = 0
    for c in s:
        ret = (ret << 8) | ord(c)
    return ret

def generate(password, site, multibase, iterations=1000, keylen=32):
    """Generate a password with the passacre method.

    This derives a value from running PBKDF2 on ``password`` with ``site`` as
    the salt using the specified number of iterations and key length, then
    encodes that value with the specified ``MultiBase``.
    """

    password_value = int_of_bytes(
        pbkdf2.pbkdf2_bin(password, site, iterations=iterations, keylen=keylen))
    return multibase.encode(password_value)[0]

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
