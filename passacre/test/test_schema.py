# Copyright (c) Aaron Gallagher <_@habnab.it>
# See COPYING for details.

from __future__ import unicode_literals

import sys

import pytest

from passacre import schema


if sys.version_info < (3,):
    string_prefix, string_padding = 'u', ' '
else:
    string_prefix = string_padding = ''


def test_schema_parse_error_single_item_list():
    with pytest.raises(schema.ParseError) as excinfo:
        schema.parse_items([['word']])
    assert str(excinfo.value) == """
whilst parsing the items: [[{0}'word']]
whilst parsing an item:    [{0}'word']
expected an array with at least two elements; got [{0}'word']""".format(string_prefix)

def test_schema_parse_error_wrong_type_in_items():
    with pytest.raises(schema.ParseError) as excinfo:
        schema.parse_items(None)
    assert str(excinfo.value) == """
whilst parsing the items: None
whilst parsing the value: None
expected an array; got None"""

def test_schema_parse_error_wrong_type_in_item():
    with pytest.raises(schema.ParseError) as excinfo:
        schema.parse_items([None])
    assert str(excinfo.value) == """
whilst parsing the items:       [None]
whilst parsing an item:          None
whilst parsing character sets:   None
whilst parsing a character set:  None
whilst parsing the value:        None
expected a string; got None"""

def test_schema_parse_error_wrong_type_in_delimiter():
    with pytest.raises(schema.ParseError) as excinfo:
        schema.parse_items([[None, 1]])
    assert str(excinfo.value) == """
whilst parsing the items:               [[None, 1]]
whilst parsing an item:                  [None, 1]
whilst parsing a count and items array:  [None, 1]
whilst parsing the value:                 None
expected a string; got None"""

def test_schema_parse_error_in_non_zeroth_item():
    with pytest.raises(schema.ParseError) as excinfo:
        schema.parse_items([[' ', None]])
    assert str(excinfo.value) == """
whilst parsing the items:       [[{0}' ', None]]
whilst parsing an item:          [{0}' ', None]
whilst parsing character sets:   [{0}' ', None]
whilst parsing a character set:   {1}     None
whilst parsing the value:         {1}     None
expected a string; got None""".format(string_prefix, string_padding)
