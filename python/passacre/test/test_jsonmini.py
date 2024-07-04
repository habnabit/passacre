# Copyright (c) Aaron Gallagher <_@habnab.it>
# See COPYING for details.

from __future__ import unicode_literals

import io
import json

import pytest
import py.path

from passacre.jsonmini import parse
from passacre._ometa import ParseError


jsondir = py.path.local(__file__).dirpath('data', 'json')


def test_bare_string():
    assert parse('foo') == 'foo'

def test_bare_non_ascii():
    assert parse('\xff') == '\xff'

def test_bare_object():
    assert parse('spam: eggs') == {'spam': 'eggs'}

def test_bare_non_ascii_object():
    assert parse('\xff: eggs') == {'\xff': 'eggs'}

def test_percent():
    assert parse('%') == None

def test_embedded_percent():
    assert parse('{spam: %, eggs: {eggs: %}}') == {'spam': None, 'eggs': {'eggs': None}}

def test_bare_embedded_percent():
    assert parse('spam: %, eggs: {eggs: %}') == {'spam': None, 'eggs': {'eggs': None}}

def test_parse_failures():
    for path in jsondir.visit(lambda p: p.fnmatch('fail*.jtest')):
        with io.open(path.strpath) as infile:
            data = infile.read()
        with pytest.raises(ParseError):
            parse(data)

def test_parse_successes():
    for path in jsondir.visit(lambda p: p.fnmatch('pass*.jtest')):
        with io.open(path.strpath) as infile:
            data = infile.read()
        # can't do much else because of float equality
        assert (json.dumps(parse(data), sort_keys=True)
                == json.dumps(json.loads(data), sort_keys=True))
