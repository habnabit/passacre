# Copyright (c) Aaron Gallagher <_@habnab.it>
# See COPYING for details.

import os

from setuptools import setup
from wheel.bdist_wheel import bdist_wheel as _bdist_wheel


class bdist_wheel(_bdist_wheel):

    def finalize_options(self):
        _bdist_wheel.finalize_options(self)
        self.root_is_pure = False

    def get_tag(self):
        impl, abi, plat = _bdist_wheel.get_tag(self)
        return 'py2.py3', 'none', plat


backend = 'passacre-backend-{0}-{4}'.format(*os.uname())


setup(
    name='passacre-backend',
    description='better repeatable password generation',
    long_description='',
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
