import pbkdf2

def unpack_bytes(s):
    ret = 0
    for c in s:
        ret = (ret << 8) | ord(c)
    return ret

def generate(password, site, multibase, iterations=1000, keylen=32):
    password_value = unpack_bytes(pbkdf2.pbkdf2_bin(password, site, iterations=iterations, keylen=keylen))
    return multibase.encode(password_value)[0]

def generate_from_config(password, site, config):
    site_config = config.get(site, None)
    if site_config is None:
        site_config = config['default']
    return generate(password, site, **site_config)
