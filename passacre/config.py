# Copyright (c) Aaron Gallagher <_@habnab.it>
# See COPYING for details.

from __future__ import unicode_literals

from passacre.multibase import MultiBase

import string
import yaml
import os

default_digits = {
    'printable': string.digits + string.ascii_letters + string.punctuation,
    'alphanumeric': string.digits + string.ascii_letters,
    'digit': string.digits,
    'letter': string.ascii_letters,
    'lowercase': string.ascii_lowercase,
    'uppercase': string.ascii_uppercase,
}

def multibase_of_schema(schema, words):
    "Convert a password schema from decoded YAML to a ``MultiBase``."
    ret = []
    for item in schema:
        if isinstance(item, list) and item[1] == 'word':
            count = item[0]
            delimiter = ' '
            if len(item) == 3:
                delimiter = item[2]
            if not words:
                raise ValueError('no words provided')
            items = []
            for x in xrange(count):
                if x != 0:
                    items.append([delimiter])
                items.append(words)
        else:
            count = 1
            if isinstance(item, list) and isinstance(item[0], int):
                if len(item) == 2:
                    count, item = item
            if not isinstance(item, list):
                item = [item]
            items = [''.join(default_digits.get(i, i) for i in item)] * count
        ret.extend(items)
    return MultiBase(ret)

def load(infile):
    "Load site configuration from a YAML file object."
    parsed = yaml.load(infile)
    defaults = parsed['sites'].get('default', {})
    defaults.setdefault('method', 'keccak')
    defaults.setdefault('iterations', 1000)

    if 'words-file' in parsed:
        with open(os.path.expanduser(parsed['words-file'])) as infile:
            words = [word.strip() for word in infile]
    else:
        words = None

    sites = {}
    for site, additional_config in parsed['sites'].items():
        site_config = sites[site] = defaults.copy()
        site_config.update(additional_config)
        site_config['multibase'] = multibase_of_schema(
            site_config['schema'], words)
        site_config['iterations'] = (
            site_config.get('iterations', 1000) + site_config.get('increment', 0))

    site_hashing = sites['--site-hashing'] = defaults.copy()
    site_hashing.update(parsed.get('site-hashing', {}))
    site_hashing.setdefault('enabled', True)

    return sites
