# Copyright (c) Aaron Gallagher <_@habnab.it>
# See COPYING for details.

# may god have mercy on my soul
from setuptools import setup

setup(
    name='passacre',
    packages=['passacre', 'passacre.test'],
    extras_require={
        'config': ['PyYAML'],
        'clipboard': ['xerox'],
        'keccak-generation': ['cykeccak'],
        'skein-generation': ['pyskein'],
    },
    entry_points={
        'console_scripts': ['passacre = passacre.application:main [config]'],
    },
)
