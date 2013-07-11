# Copyright (c) Aaron Gallagher <_@habnab.it>
# See COPYING for details.

import sys


if sys.version_info < (2, 7):
    def excinfo_arg_0(excinfo):
        return excinfo.value
else:
    def excinfo_arg_0(excinfo):
        return excinfo.value.args[0]
