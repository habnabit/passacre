from parsley import makeGrammar
import string

builtin_digits = {
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

builtin_digits = str:x ?(x in builtin_digits) -> builtin_digits[x]
digits = builtin_digits | str
digits_list = [digits+:x] -> ''.join(x)
digits_item = digits | digits_list

word_item = [int?:count 'word' str?:delimiter] -> [(_word, delimiter)] * (count or 1)
schema_item = ( digits_item:digits -> [(digits,)]
              | [int:count digits_item:digits] -> [(digits,)] * count)
item = word_item | schema_item

items = (item | counted_items)+:items -> [item for subitems in items for item in subitems]
counted_items = [int:count items:items] -> items * count

"""

parser = makeGrammar(grammar, {'builtin_digits': builtin_digits, '_word': object()})
print parser([
    [2, [3,
     [2, ['foo', 'bar', 'baz', 'bar']],
     [3, ['digit', 'uppercase']]]],
    ['word'],
    [2, 'word'],
    [3, 'word', ', '],
    ['word', ';'],
]).items()
