from parsley import makeGrammar
import string

character_classes = {
    'printable': string.digits + string.ascii_letters + string.punctuation,
    'alphanumeric': string.digits + string.ascii_letters,
    'digit': string.digits,
    'letter': string.ascii_letters,
    'lowercase': string.ascii_lowercase,
    'uppercase': string.ascii_uppercase,
}

grammar = """

str = anything:x ?(isinstance(x, str)) -> x
int = anything:x ?(isinstance(x, int)) -> x

character_class = str:x ?(x in character_classes) -> character_classes[x]
character_set = character_class | str
character_set_list = [character_set+:x] -> ''.join(x)

character_sets = (character_set | character_set_list):s -> [(s,)]
word = [int?:count 'word' str?:delimiter] -> [(_word, delimiter)] * (count or 1)
item = ( character_sets
       | word
       | [int:count items:items] -> items * count)

items = item+:items -> [item for subitems in items for item in subitems]

"""

parser = makeGrammar(grammar, {'character_classes': character_classes, '_word': object()})
print parser([
    [2,
        [3,
            [2, ['foo', 'bar', 'baz', 'bar']],
            [3, ['digit', 'uppercase']],
        ]
    ],
    ['word'],
    [2, 'word'],
    [3, 'word', ', '],
    ['word', ';'],
]).items()
