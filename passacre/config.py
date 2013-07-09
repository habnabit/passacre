# Copyright (c) Aaron Gallagher <_@habnab.it>
# See COPYING for details.

from __future__ import unicode_literals

from passacre.multibase import MultiBase
from passacre import generator

import collections
import json
import os
import string


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
            for x in range(count):
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



class ConfigBase(object):
    def __init__(self):
        self.defaults = {
            'method': 'keccak',
            'iterations': 1000,
        }
        self.site_hashing = {
            'enabled': True,
        }
        self.words = None

    def load_words_file(self, path):
        if path is None:
            return
        with open(os.path.expanduser(path)) as infile:
            self.words = [word.strip() for word in infile]

    def fill_out_config(self, config):
        config['multibase'] = multibase_of_schema(config['schema'], self.words)
        config['iterations'] = (
            config.get('iterations', 1000) + config.get('increment', 0))

    def set_defaults(self, defaults):
        self.defaults.update(defaults)
        self.site_hashing.update(self.defaults)
        self.fill_out_config(self.defaults)

    def get_site(self, site, password=None):
        config = self._get_site(site)
        if config is None and password is not None:
            hashed_site = generator.hash_site(password, site, self.site_hashing)
            config = self._get_site(hashed_site)
        if config is None:
            config = self.defaults
        return config

    def generate_for_site(self, username, password, site):
        config = self.get_site(site, password)
        return generator.generate(username, password, site, config)


class YAMLConfig(ConfigBase):
    def read(self, infile):
        "Load site configuration from a YAML file object."
        import yaml
        parsed = yaml.load(infile)
        self.set_defaults(parsed['sites'].get('default', {}))
        self.load_words_file(parsed.get('words-file'))

        self.sites = {}
        for site, additional_config in parsed['sites'].items():
            site_config = self.sites[site] = self.defaults.copy()
            site_config.update(additional_config)
            self.fill_out_config(site_config)

        self.site_hashing.update(parsed.get('site-hashing', {}))

    def _get_site(self, site, password=None):
        return self.sites.get(site)

    def get_all_sites(self):
        return self.sites


def maybe_json(val):
    try:
        return json.loads(val)
    except ValueError:
        return val

def maybe_json_dict(pairs):
    return dict((k, maybe_json(v)) for k, v in pairs)

class SqliteConfig(ConfigBase):
    def read(self, infile):
        import sqlite3
        self._db = sqlite3.connect(infile.name)
        curs = self._db.cursor()

        curs.execute(
            'SELECT config_values.name, value FROM config_values WHERE site_name IS NULL')
        config = maybe_json_dict(curs)
        self.load_words_file(config.get('words-file'))
        self.set_defaults(self._get_site('default'))
        self.site_hashing.update(config.get('site-hashing', {}))

    def _get_site(self, site):
        curs = self._db.cursor()
        curs.execute(
            'SELECT value FROM sites JOIN schemata USING (schema_id) WHERE site_name = ?',
            (site,))
        results = curs.fetchall()
        if not results:
            return None

        config = self.defaults.copy()
        config['schema'] = json.loads(results[0][0])
        curs.execute(
            'SELECT name, value FROM config_values WHERE site_name = ?',
            (site,))
        config.update(maybe_json_dict(curs))

        self.fill_out_config(config)
        return config

    def get_all_sites(self):
        curs = self._db.cursor()
        curs.execute(
            'SELECT site_name, name, value FROM config_values WHERE site_name IS NOT NULL')
        sites = collections.defaultdict(self.defaults.copy)
        for site, k, v in curs:
            sites[site][k] = maybe_json(v)

        curs.execute(
            'SELECT site_name, value FROM sites JOIN schemata USING (schema_id) WHERE site_name IS NOT NULL')
        for site, schema in curs:
            sites[site]['schema'] = json.loads(schema)

        for config in sites.values():
            self.fill_out_config(config)

        return dict(sites)


def load(infile):
    if infile.read(16) == b'SQLite format 3\x00':
        config = SqliteConfig()
    else:
        config = YAMLConfig()
    infile.seek(0)
    config.read(infile)
    return config
