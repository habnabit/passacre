# Copyright (c) Aaron Gallagher <_@habnab.it>
# See COPYING for details.

# may god have mercy on my soul
from setuptools import setup

setup(
    name='passacre',
    packages=['passacre', 'passacre.test'],
    install_requires=[
        'cykeccak',
    ],
    extras_require={
        'config': ['PyYAML'],
    },
    entry_points={
        'console_scripts': ['passacre = passacre.application:main [config]'],
    },
)
