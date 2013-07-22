# Copyright (c) Aaron Gallagher <_@habnab.it>
# See COPYING for details.

import string

from parsley import makeGrammar, ParseError

from passacre.multibase import MultiBase


character_classes = {
    'printable': string.digits + string.ascii_letters + string.punctuation,
    'alphanumeric': string.digits + string.ascii_letters,
    'digit': string.digits,
    'letter': string.ascii_letters,
    'lowercase': string.ascii_lowercase,
    'uppercase': string.ascii_uppercase,
}

grammar = """

str = anything:x ?(isinstance(x, str)) ^(string) -> x
int = anything:x ?(isinstance(x, int)) ^(number) -> x

character_class = str:x ?(x in character_classes) ^(character class) -> character_classes[x]
character_set = character_class ^(character class) | str ^(character set)
character_set_list = [(character_set ^(character set))+:x] ^(array of character sets) -> ''.join(x)

character_sets = (character_set ^(character set) | character_set_list ^(concatenated character sets)):s -> [(s,)]
word = [(int ^(word count))?:count 'word' (str ^(word delimiter))?:delimiter] ^(word array) -> [(_word, count, delimiter)]
item = ( word ^(word array)
       | character_sets ^(character set)
       | [(int ^(count of items)):count (items ^(series of items)):items] ^(item array with count) -> items * count)

items = (item ^(item))+:items -> [item for subitems in items for item in subitems]

"""

_word = object()
parser = makeGrammar(
    grammar, {'character_classes': character_classes, '_word': _word})


class ListParseError(ParseError):
    def formatError(self):
        """
        Return a pretty string containing error info about string
        parsing failure.
        """
        stringified = str(self.input)
        columnNo = 1
        if self.position <= len(self.input):
            for x in range(self.position - 1):
                columnNo += 2 + len(str(self.input[x]))
            if self.position > 1:
                columnNo += 2
        reason = self.formatReason()
        return ('\n' + stringified + '\n' + (' ' * columnNo + '^') +
                "\nParse error at item %s: %s. trail: [%s]\n"
                % (self.position, reason, ' '.join(self.trail)))

    def __hash__(self):
        return id(self)


def multibase_of_schema(schema, words):
    "Convert a password schema from decoded YAML to a ``MultiBase``."
    try:
        items = parser(schema).items()
    except ParseError as e:
        e.__class__ = ListParseError
        raise
    ret = []
    for item in items:
        if item[0] is _word:
            _, count, delimiter = item
            for x in range(count):
                if x != 0:
                    ret.append([delimiter])
                ret.append(words)
        else:
            ret.append(item[0])
    return MultiBase(ret)

print(multibase_of_schema([
    [2,
        [3,
            [2, ['foo', 'foo', 'baz', 'bar']],
            [1, ['foo']],
        ]
    ],
    ['word', None],
    [2, 'word'],
    [3, 'word', ', '],
    ['word', ';'],
], None))
