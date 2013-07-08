# Copyright (c) Aaron Gallagher <_@habnab.it>
# See COPYING for details.

# may god have mercy on my soul
from setuptools import setup


with open('README', 'r') as infile:
    long_description = infile.read()

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

    vcversioner={
        'version_module_paths': ['passacre/_version.py'],
    },
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
