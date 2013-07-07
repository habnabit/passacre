# Copyright (c) Aaron Gallagher <_@habnab.it>
# See COPYING for details.

# may god have mercy on my soul
from setuptools import setup


setup(
    name='passacre',
    vcversioner={},
    packages=['passacre', 'passacre.test'],
    setup_requires=['vcversioner'],
    extras_require={
        'config': ['PyYAML'],
        'clipboard': ['xerox'],
        'keccak-generation': ['cykeccak>=0.13.2'],
        'skein-generation': ['pyskein>=0.7'],
    },
    entry_points={
        'console_scripts': ['passacre = passacre.application:main [config]'],
    },
)
