# Copyright (c) Aaron Gallagher <_@habnab.it>
# See COPYING for details.

from __future__ import unicode_literals, print_function

from passacre.schema import multibase_of_schema
from passacre.util import nested_set, jloads, jdumps, errormark
from passacre import features, generator

import collections
import json
import os


@errormark('verifying schema: {0!r}')
def verify_multibase_schema(schema):
    multibase_of_schema(schema)


global_config_options = set("""
always-confirm-passwords
method
iterations
words-file
site-hashing.enabled
site-hashing.method
site-hashing.iterations
""".split())

site_config_options = set("""
method
iterations
increment
schema
yubikey-slot
""".split())


class ConfigBase(object):
    is_mutable_config = False

    def __init__(self):
        self.defaults = {
            'method': 'keccak',
            'iterations': 1000,
        }
        self.site_hashing = {
            'enabled': True,
        }
        self.global_config = {}
        self.word_list_path = None

    def load_words_file(self, path):
        if path is None:
            return
        self.word_list_path = os.path.expanduser(path)

    def multibase_of_schema(self, schema):
        ret = multibase_of_schema(schema)
        if self.word_list_path is not None:
            ret['words'] = {'source': {'filePath': self.word_list_path}}
        return ret

    def fill_out_config(self, config):
        config['multibase'] = self.multibase_of_schema(config['schema'])
        config['iterations'] = (
            config.get('iterations', 1000) + config.get('increment', 0))

    def set_defaults(self, defaults):
        self.defaults.update(defaults)
        self.site_hashing.update(
            (k, v) for k, v in self.defaults.items()
            if k in ('method', 'iterations'))
        self.fill_out_config(self.defaults)

    def _get_hashed_site(self, site, password):
        hashed_site = generator.hash_site(password, site, self.site_hashing)
        return self._get_site(hashed_site)

    def get_site(self, site, password=None):
        if self.site_hashing['enabled'] == 'always' and site != 'default':
            config = self._get_hashed_site(site, password)
        else:
            config = self._get_site(site)
        if config is None and password:
            config = self._get_hashed_site(site, password)
        if config is None:
            config = self.defaults
        return config

    def generate_for_site(self, username, password, site, override=()):
        config = self.get_site(site, password)
        if override:
            config.update(override)
            for k, v in list(config.items()):
                if v is None:
                    del config[k]
            self.fill_out_config(config)
        return generator.generate(username, password, site, config)


class YAMLConfig(ConfigBase):
    @features.yaml.check
    def read(self, infile):
        "Load site configuration from a YAML file object."
        import yaml
        parsed = yaml.safe_load(infile)
        sites = parsed.pop('sites', {})
        self.set_defaults(sites.get('default', {}))
        self.load_words_file(parsed.pop('words-file', None))

        self.sites = {}
        for site, additional_config in sites.items():
            site_config = self.sites[site] = self.defaults.copy()
            site_config.update(additional_config)
            self.fill_out_config(site_config)

        self.site_hashing.update(parsed.pop('site-hashing', {}))
        self.global_config = parsed

    def _get_site(self, site, password=None):
        return self.sites.get(site)

    def get_all_sites(self):
        return self.sites

    def _no_config_modification(self, *a, **kw):
        raise NotImplementedError("YAMLConfig doesn't implement configuration modification.")

    add_site = remove_site = set_site_schema = _no_config_modification
    add_schema = remove_schema = set_schema_value = set_schema_name = _no_config_modification

    def get_all_schemata(self, *a, **kw):
        raise NotImplementedError("YAMLConfig doesn't have a way to list schemata.")

    get_schema = get_all_schemata


def jsonmini_dict(pairs):
    return dict((k, jloads(v)) for k, v in pairs)

class SqliteConfig(ConfigBase):
    is_mutable_config = True

    def read(self, infile):
        import sqlite3
        self._db = sqlite3.connect(infile.name)
        curs = self._db.cursor()

        curs.execute(
            'SELECT config_values.name, value FROM config_values WHERE site_name IS NULL')
        config = jsonmini_dict(curs)
        self.load_words_file(config.pop('words-file', None))
        self.set_defaults(self._get_site('default'))
        self.site_hashing.update(config.pop('site-hashing', {}))
        self.global_config = config

    def get_site_config(self, site):
        curs = self._db.cursor()
        curs.execute(
            'SELECT name, value FROM config_values WHERE site_name IS ?',
            (site,))
        return jsonmini_dict(curs)

    def _get_site(self, site):
        site_config = self.get_site_config(site)
        curs = self._db.cursor()
        curs.execute(
            'SELECT value FROM sites JOIN schemata USING (schema_id) WHERE site_name = ?',
            (site,))
        results = curs.fetchall()
        if not (results or site_config):
            return None

        config = self.defaults.copy()
        if results:
            config['schema'] = json.loads(results[0][0])
        config.update(site_config)

        self.fill_out_config(config)
        return config

    def add_site(self, name, schema_id):
        curs = self._db.cursor()
        curs.execute(
            'INSERT INTO sites (site_name, schema_id) VALUES (?, ?)',
            (name, schema_id))
        self._db.commit()

    def set_site_schema(self, name, schema_id):
        curs = self._db.cursor()
        curs.execute(
            'UPDATE sites SET schema_id = ? WHERE site_name = ?',
            (schema_id, name))
        self._db.commit()

    def remove_site(self, name):
        curs = self._db.cursor()
        curs.execute('DELETE FROM sites WHERE site_name = ?', (name,))
        curs.execute('DELETE FROM config_values WHERE site_name = ?', (name,))
        self._db.commit()

    def rename_site(self, name, newname):
        curs = self._db.cursor()
        curs.execute('UPDATE OR REPLACE sites SET site_name = ? WHERE site_name = ?', (newname, name))
        curs.execute('UPDATE OR REPLACE config_values SET site_name = ? WHERE site_name = ?', (newname, name))
        self._db.commit()

    def get_all_sites(self):
        curs = self._db.cursor()
        curs.execute(
            'SELECT site_name, name, value FROM config_values WHERE site_name IS NOT NULL')
        sites = collections.defaultdict(self.defaults.copy)
        for site, k, v in curs:
            sites[site][k] = jloads(v)

        curs.execute(
            'SELECT site_name, name, value FROM sites JOIN schemata USING (schema_id) WHERE site_name IS NOT NULL')
        for site, schema_name, schema in curs:
            sites[site]['schema-name'] = schema_name
            sites[site]['schema'] = json.loads(schema)

        for config in sites.values():
            self.fill_out_config(config)

        return dict(sites)

    def get_all_schemata(self):
        curs = self._db.cursor()
        curs.execute('SELECT name, value FROM schemata')
        return jsonmini_dict(curs)

    def get_schema(self, name):
        curs = self._db.cursor()
        curs.execute('SELECT schema_id, value FROM schemata WHERE name = ?', (name,))
        results = curs.fetchall()
        if not results:
            raise ValueError('there is no schema by the name %r' % (name,))
        return results[0]

    def add_schema(self, name, value):
        verify_multibase_schema(value)
        curs = self._db.cursor()
        curs.execute(
            'INSERT INTO schemata (name, value) VALUES (?, ?)',
            (name, jdumps(value)))
        self._db.commit()

    def remove_schema(self, schema_id):
        curs = self._db.cursor()
        curs.execute('SELECT site_name FROM sites WHERE schema_id = ?', (schema_id,))
        sites = sorted(site for site, in curs)
        if sites:
            raise ValueError(
                "can't delete this schema; at least one site is using it: %r" % (sites,))
        curs.execute('DELETE FROM schemata WHERE schema_id = ?', (schema_id,))
        self._db.commit()

    def set_schema_name(self, schema_id, newname):
        curs = self._db.cursor()
        curs.execute('UPDATE schemata SET name = ? WHERE schema_id = ?', (newname, schema_id))
        self._db.commit()

    def set_schema_value(self, schema_id, value):
        verify_multibase_schema(value)
        curs = self._db.cursor()
        curs.execute(
            'UPDATE schemata SET value = ? WHERE schema_id = ?',
            (jdumps(value), schema_id))
        self._db.commit()

    def get_config(self, site, name):
        curs = self._db.cursor()
        curs.execute(
            'SELECT value FROM config_values WHERE site_name IS ? AND name = ?',
            (site, name))
        results = curs.fetchall()
        if not results:
            raise ValueError('there is no config %r for %r' % (name, site))
        return jloads(results[0][0])

    def set_config(self, site, name, value):
        split_name = name.split('.')
        if len(split_name) > 1:
            try:
                base_value = self.get_config(site, split_name[0])
            except ValueError:
                base_value = {}
            nested_set(base_value, split_name[1:], value)
            name, new_value = split_name[0], base_value
        else:
            new_value = value
        curs = self._db.cursor()
        curs.execute(
            'DELETE FROM config_values WHERE site_name IS ? AND name = ?',
            (site, name,))
        if new_value is not None:
            curs.execute(
                'INSERT INTO config_values (site_name, name, value) VALUES (?, ?, ?)',
                (site, name, jdumps(new_value)))
        self._db.commit()


def load(infile):
    if infile.read(16) == b'SQLite format 3\x00':
        config = SqliteConfig()
    else:
        config = YAMLConfig()
    infile.seek(0)
    config.read(infile)
    return config
