# Copyright (c) Aaron Gallagher <_@habnab.it>
# See COPYING for details.

from passacre.multibase import MultiBase

import string
import yaml

default_digits = {
    'printable': string.digits + string.letters + string.punctuation,
    'alphanumeric': string.digits + string.letters,
    'digit': string.digits,
    'letter': string.letters,
    'lowercase': string.lowercase,
    'uppercase': string.uppercase,
}

def multibase_of_schema(schema):
    "Convert a password schema from decoded YAML to a ``MultiBase``."
    ret = []
    for item in schema:
        count = 1
        if isinstance(item, list) and isinstance(item[0], int):
            count, item = item
        if not isinstance(item, list):
            item = [item]
        item = ''.join(default_digits.get(i, i) for i in item)
        ret.extend([item] * count)
    return MultiBase(ret)

def load(infile):
    "Load site configuration from a YAML file object."
    parsed = yaml.load(infile)
    defaults = parsed['sites'].get('default', {})
    sites = {}
    for site, additional_config in parsed['sites'].iteritems():
        site_config = defaults.copy()
        site_config.update(additional_config)
        sites[site] = {
            'multibase': multibase_of_schema(site_config['schema']),
            'iterations': site_config.get('iterations', 1000) + site_config.get('increment', 0),
        }

    return sites
