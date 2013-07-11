#!/usr/bin/env python
# Copyright (c) Aaron Gallagher <_@habnab.it>
# See COPYING for details.

import json
import sqlite3
import sys
import yaml


def main():
    _, yaml_file, sqlite_file = sys.argv
    with open(yaml_file) as infile:
        config = yaml.safe_load(infile)
    db = sqlite3.connect(sqlite_file)
    sites = config.pop('sites', {})
    config.pop('schemata', None)
    default_schema = sites['default']['schema']
    schemata = {}
    config_rows = [
        (None, k, json.dumps(v)) for k, v in config.iteritems()]
    for site, site_config in sites.iteritems():
        schema = json.dumps(site_config.pop('schema', default_schema))
        schemata.setdefault(schema, []).append(site)
        config_rows.extend(
            (site, k, json.dumps(v)) for k, v in site_config.iteritems())
    curs = db.cursor()
    curs.executemany(
        'INSERT INTO schemata (name, value) VALUES (?, ?)',
        (('schema_%d' % e, schema) for e, schema in enumerate(schemata)))
    curs.executemany(
        'INSERT INTO sites (site_name, schema_id) SELECT ?, schema_id FROM schemata WHERE value = ?',
        ((site, value)
         for value, sites in schemata.items()
         for site in sites))
    curs.executemany('INSERT INTO config_values (site_name, name, value) VALUES (?, ?, ?)', config_rows)
    db.commit()

main()
