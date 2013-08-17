import unicodedata

from passacre._ometa import OMetaBase, ParseError, EOFError
from passacre._jsonmini import createParserClass


try:
    unichr
except NameError:
    unichr = chr


jsonmini_parser = createParserClass(
    OMetaBase, {'unichr': unichr, 'unicodedata': unicodedata})

def parse(s):
    grammar = jsonmini_parser(s)
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
