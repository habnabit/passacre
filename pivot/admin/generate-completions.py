import sys

from passacre.application import Passacre
from passacre import completion


completion_for = getattr(completion, sys.argv[1] + '_completion_for')
completion_for(Passacre().build_parser())
