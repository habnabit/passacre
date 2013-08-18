# Copyright (c) Aaron Gallagher <_@habnab.it>
# See COPYING for details.

import sys
import vcversioner

# may god have mercy on my soul
from setuptools import setup


version = vcversioner.find_version(
    version_module_paths=['passacre/_version.py'],
)


with open('README.rst', 'r') as infile:
    long_description = infile.read()


extras_require = {
    'yaml': ['PyYAML'],
    'clipboard': ['xerox'],
    'keccak_generation': ['cykeccak>=0.13.2'],
    'yubikey': ['ykpers-cffi'],
}

if sys.version_info > (3,):
    extras_require['skein_generation'] = ['pyskein>=0.7']

setup(
    name='passacre',
    description='better repeatable password generation',
    long_description=long_description,
    author='Aaron Gallagher',
    author_email='_@habnab.it',
    url='https://github.com/habnabit/passacre',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: ISC License (ISCL)',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Topic :: Security',
    ],
    license='ISC',

    version=version.version,
    packages=['passacre', 'passacre.test'],
    package_data={
        'passacre': ['schema.sql'],
        'passacre.test': ['data/*.sqlite', 'data/*.yaml', 'data/words',
                          'data/*/words', 'data/*/.passacre.*', 'data/json/*'],
    },
    extras_require=extras_require,
    entry_points={
        'console_scripts': ['passacre = passacre.application:main'],
    },
    zip_safe=False,
)
