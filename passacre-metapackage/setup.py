# Copyright (c) Aaron Gallagher <_@habnab.it>
# See COPYING for details.

from setuptools import setup

import versioneer


version = versioneer.get_version()
#with open('../README.rst', 'r') as infile:
long_description = ''#infile.read()


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
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Security',
    ],
    license='ISC',

    install_requires=[
        'passacre-backend==' + version,
        'passacre-nobackend==' + version,
    ],
    version=version,
    cmdclass=versioneer.get_cmdclass(),
)
