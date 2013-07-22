# Copyright (c) Aaron Gallagher <_@habnab.it>
# See COPYING for details.

import string

from passacre.multibase import MultiBase


_word = object()
character_classes = {
    'printable': string.digits + string.ascii_letters + string.punctuation,
    'alphanumeric': string.digits + string.ascii_letters,
    'digit': string.digits,
    'letter': string.ascii_letters,
    'lowercase': string.ascii_lowercase,
    'uppercase': string.ascii_uppercase,
}


class ParseError(Exception):
    def __init__(self, got, expected):
        super(ParseError, self).__init__(got, expected)
        self.got = got
        self.expected = expected
        self.parse_stack = []

    def __str__(self):
        whats, xs, indices = zip(*reversed(self.parse_stack))
        whats_max_len = max(len(what) for what in whats) + 1
        whats = [(what + ':').ljust(whats_max_len) for what in whats]
        spaced_xs = []
        spaces = 0
        prev = None
        for x, index in zip(xs, indices):
            if index is not None:
                spaces += 1
                for e in range(index):
                    spaces += 2 + len(repr(prev[e]))
            spaced_xs.append(' ' * spaces + repr(x))
            prev = x
        repaired = zip(whats, spaced_xs)

        return '\n%s\nexpected %s; got %r' % (
            '\n'.join('while parsing %s %s' % x for x in repaired),
            self.expected, self.got)

class RetryableParseError(ParseError):
    pass


def trace_parse(what):
    def deco(f):
        def wrap(x, *a, **kw):
            index = kw.pop('_index', None)
            try:
                return f(x, *a)
            except ParseError as e:
                e.parse_stack.append((what, x, index))
                raise
        return wrap
    return deco

def try_each(x, fs, expected):
    for f in fs:
        try:
            return f(x)
        except RetryableParseError:
            pass
    raise ParseError(x, expected)

@trace_parse('the value')
def parse_type(x, type_, expected):
    if not isinstance(x, type_):
        raise ParseError(x, expected)
    return x

@trace_parse('the value')
def parse_value(x, value, expected):
    if x != value:
        raise ParseError(x, expected)
    return x

@trace_parse('a character set')
def parse_character_set(x):
    x = parse_type(x, str, 'a string')
    return character_classes.get(x, x)

@trace_parse('character sets')
def parse_character_sets(x):
    if x == 'word':
        return [_word]
    elif isinstance(x, list):
        return [''.join(parse_character_set(y, _index=e) for e, y in enumerate(x))]
    else:
        return [parse_character_set(x)]

@trace_parse('a count and items array')
def parse_counted_item(x):
    delimiter = ''
    if isinstance(x[0], int):
        count = parse_type(x[0], int, 'a number', _index=0)
        start = 1
    else:
        delimiter = parse_type(x[0], str, 'a string', _index=0)
        count = parse_type(x[1], int, 'a number', _index=1)
        start = 2
    each_item = [z
                 for e, y in enumerate(x[start:], start=start)
                 for z in parse_item(y, _index=e)]
    items = []
    for e in range(count):
        if e != 0 and delimiter:
            items.append(delimiter)
        items.extend(each_item)
    return items

@trace_parse('an item')
def parse_item(x):
    if isinstance(x, list):
        if len(x) < 2:
            raise ParseError(x, 'an array at least two elements')
        if isinstance(x[0], int) or isinstance(x[1], int):
            return parse_counted_item(x)
    return parse_character_sets(x)

@trace_parse('the items')
def parse_items(x):
    items = [parse_item(y, _index=e) for e, y in enumerate(parse_type(x, list, 'an array'))]
    return [y for subitems in items for y in subitems]


def multibase_of_schema(schema, words):
    "Convert a password schema from decoded YAML to a ``MultiBase``."
    items = [words if item is _word else item for item in parse_items(schema)]
    return MultiBase(items)
