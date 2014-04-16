# Copyright (c) Aaron Gallagher <_@habnab.it>
# See COPYING for details.

import json
import re
import unicodedata

from passacre._ometa import OMetaBase, ParseError, EOFError
from passacre._jsonmini import createParserClass
from passacre.compat import unichr, unicode, long


jsonmini_parser = createParserClass(
    OMetaBase, {'unichr': unichr, 'unicodedata': unicodedata})


def parse(s):
    grammar = jsonmini_parser(unicode(s))
    try:
        ret, err = grammar.apply('top')
    except ParseError as e:
        grammar.considerError(e)
        err = grammar.currentError
    else:
        try:
            extra, _ = grammar.input.head()
        except EOFError:
            return ret
    raise err


_unparsers = {}


def unparser(*types):
    def deco(f):
        for typ in types:
            _unparsers[typ] = f
        return f
    return deco


_unicode_identifier_regexp = re.compile('[^a-zA-Z0-9_-]')


@unparser(unicode)
def _unparse_unicode(u, is_top):
    if _unicode_identifier_regexp.search(u):
        return json.dumps(u)
    else:
        return u


@unparser(dict)
def _unparse_dict(d, is_top):
    ret = [] if is_top else ['{']
    for k, v in sorted(d.items()):
        ret.append(_unparse_unicode(k, False))
        ret.append(': ')
        ret.append(_unparse(v))
        ret.append(', ')
    if is_top:
        ret.pop()
    else:
        ret[-1] = '}'
    return ''.join(ret)


@unparser(list)
def _unparse_list(l, is_top):
    return '[%s]' % ', '.join(_unparse(x) for x in l)


@unparser(int, long, float, bool, type(None))
def _unparse_the_rest(x, is_top):
    return json.dumps(x)


def _unparse(j, _is_top=False):
    return _unparsers[type(j)](j, _is_top)


def unparse(j):
    return _unparse(j, _is_top=True)
