# Copyright (c) Aaron Gallagher <_@habnab.it>
# See COPYING for details.

import json
import sqlite3

from passacre import features


def main(yaml_file, sqlite_file):
    features.yaml.check()
    import yaml
    with open(yaml_file) as infile:
        loader = yaml.SafeLoader(infile)
        loader.check_node()
        loader.get_event()
        node = loader.compose_node(None, None)
        schema_names = dict(
            (json.dumps(list(map(loader.construct_sequence, v.value))), k)
            for k, v in loader.anchors.items())
        config = loader.construct_document(node)
    db = sqlite3.connect(sqlite_file)
    sites = config.pop('sites', {})
    config.pop('schemata', None)
    default_schema = sites['default']['schema']
    schemata = {}
    config_rows = [
        (None, k, json.dumps(v)) for k, v in config.items()]
    for site, site_config in sites.items():
        schema = json.dumps(site_config.pop('schema', default_schema))
        schemata.setdefault(schema, []).append(site)
        config_rows.extend(
            (site, k, json.dumps(v)) for k, v in site_config.items())
    for e, schema in enumerate(sorted(schemata)):
        schema_names.setdefault(schema, 'schema_%d' % e)
    curs = db.cursor()
    curs.executemany(
        'INSERT INTO schemata (name, value) VALUES (?, ?)',
        ((name, schema) for schema, name in schema_names.items()))
    curs.executemany(
        'INSERT INTO sites (site_name, schema_id) SELECT ?, schema_id FROM schemata WHERE value = ?',
        ((site, value)
         for value, sites in schemata.items()
         for site in sites))
    curs.executemany('INSERT INTO config_values (site_name, name, value) VALUES (?, ?, ?)', config_rows)
    db.commit()


if __name__ == '__main__':  # pragma: nocover
    import sys
    main(*sys.argv[1:])
