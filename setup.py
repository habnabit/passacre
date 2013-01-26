# Copyright (c) Aaron Gallagher <_@habnab.it>
# See COPYING for details.

from distutils.core import setup

setup(
    name='passacre',
    packages=['passacre', 'passacre.test'],
    entry_points={
        'console_scripts': ['passacre = passacre.application:main'],
    },
)
