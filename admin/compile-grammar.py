import sys
from ometa.grammar import OMeta
from ometa.builder import writePython


if len(sys.argv) != 3:
    print "Usage: %s grammar-filename python-filename" % (sys.argv[0],)
    sys.exit(1)


with open(sys.argv[1]) as infile:
    grammar = infile.read()
g = OMeta(grammar)
tree = g.parseGrammar("Parser")
source = writePython(tree, grammar) + '\n'
with open(sys.argv[2], 'w') as outfile:
    outfile.write(source)
