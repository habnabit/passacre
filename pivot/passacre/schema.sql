-- Copyright (c) Aaron Gallagher <_@habnab.it>
-- See COPYING for details.

PRAGMA foreign_keys = ON;

CREATE TABLE schemata (
    schema_id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    value TEXT NOT NULL
);

CREATE TABLE sites (
    site_name TEXT PRIMARY KEY,
    schema_id INTEGER NOT NULL,
    FOREIGN KEY (schema_id) REFERENCES schemata (schema_id)
);

CREATE TABLE config_values (
    site_name TEXT,
    name TEXT NOT NULL,
    value TEXT NOT NULL,
    PRIMARY KEY (site_name, name),
    FOREIGN KEY (site_name) REFERENCES sites (site_name)
);
