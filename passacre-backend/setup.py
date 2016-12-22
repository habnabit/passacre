# Copyright (c) Aaron Gallagher <_@habnab.it>
# See COPYING for details.

import os
import tokenize

from setuptools import setup
from wheel.bdist_wheel import bdist_wheel as _bdist_wheel


backend = 'passacre-backend-{0}-{4}'.format(*os.uname())
with open('README.rst', 'r') as infile:
    long_description = infile.read()


try:
    _detect_encoding = tokenize.detect_encoding
except AttributeError:
    pass
else:
    def detect_encoding(readline):
        try:
            return _detect_encoding(readline)
        except SyntaxError:
            return 'latin-1', []

    tokenize.detect_encoding = detect_encoding


class bdist_wheel(_bdist_wheel):

    def finalize_options(self):
        _bdist_wheel.finalize_options(self)
        self.root_is_pure = False

    def get_tag(self):
        impl, abi, plat = _bdist_wheel.get_tag(self)
        return 'py2.py3', 'none', plat


setup(
    name='passacre-backend',
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
        'Topic :: Security',
    ],
    license='ISC',

    version=os.environ['PASSACRE_VERSION'],
    scripts=[backend],
    cmdclass={
        'bdist_wheel': bdist_wheel,
    },
    zip_safe=False,
)
