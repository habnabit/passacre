# Copyright (c) Aaron Gallagher <_@habnab.it>
# See COPYING for details.

import os

from setuptools import setup

import versioneer


here = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(here, 'README.rst'), 'r') as infile:
    long_description = infile.read()


extras_require = {
    'yaml': ['PyYAML'],
    'clipboard': ['xerox'],
    'keccak': [],
    'skein': [],
    'yubikey': ['ykpers-cffi'],
    ':python_version < "3.2"': ['subprocess32'],
}

extras_require['all'] = [
    req
    for extra, reqs in extras_require.items() if not extra.startswith(':')
    for req in reqs]

entry_points = {'console_scripts': []}
if os.environ.get('PASSACRE_LIBRARY_TESTING_ONLY') != 'yes':
    entry_points['console_scripts'].append(
        'passacre = passacre.application:main')


setup(
    name='passacre-nobackend',
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
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Security',
    ],
    license='ISC',

    packages=['passacre', 'passacre.test'],
    include_package_data=True,
    extras_require=extras_require,
    entry_points=entry_points,
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
)
