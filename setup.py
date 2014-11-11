# Copyright (c) Aaron Gallagher <_@habnab.it>
# See COPYING for details.

from __future__ import print_function

from distutils.command.build import build as _build
from distutils.core import Command
import os
import subprocess
import sys
import traceback

# may god have mercy on my soul
from setuptools import setup

os.environ.setdefault('LIBPASSACRE_NO_VERIFY', '1')
here = os.path.dirname(os.path.abspath(__file__))
libpassacre_build_dir = os.path.join(here, 'libpassacre')
ext_modules = []
try:
    from cffi.verifier import Verifier
    import _libpassacre
except ImportError:
    print('** WARNING: not building libpassacre extension: **', file=sys.stderr)
    traceback.print_exc()
    print('** END WARNING **', file=sys.stderr)
else:
    verifier = Verifier(
        _libpassacre.ffi, _libpassacre.preamble, modulename='_libpassacre_c',
        include_dirs=[libpassacre_build_dir],
        extra_objects=[os.path.join(libpassacre_build_dir, 'libpassacre.a')])
    ext_modules.append(verifier.get_extension())


with open('README.rst', 'r') as infile:
    long_description = infile.read()


class build_libpassacre(Command):
    description = 'build libpassacre'

    user_options = []
    boolean_options = []
    help_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        try:
            if not os.path.exists(os.path.join(libpassacre_build_dir, 'CMakeCache.txt')):
                subprocess.check_call(['cmake', '.'], cwd=libpassacre_build_dir)
            subprocess.check_call(['make'], cwd=libpassacre_build_dir)
        except Exception:
            print('** WARNING: building libpassacre failed: **', file=sys.stderr)
            traceback.print_exc()
            print('** END WARNING **', file=sys.stderr)


class build(_build):
    sub_commands = [
        ('build_libpassacre', lambda self: True),
    ] + _build.sub_commands


extras_require = {
    'yaml': ['PyYAML'],
    'clipboard': ['xerox'],
    'keccak': [],
    'skein': [],
    'yubikey': ['ykpers-cffi'],
    'agent': ['Twisted', 'crochet'],
    'site_list': ['pynacl'],
}

extras_require['all'] = [req for reqs in extras_require.values() for req in reqs]


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
        'Programming Language :: Python :: 3.4',
        'Topic :: Security',
    ],
    license='ISC',

    vcversioner={
        'version_module_paths': ['passacre/_version.py'],
    },
    packages=['passacre', 'passacre.agent', 'passacre.test', 'passacre.agent.test'],
    package_data={
        'passacre': ['schema.sql'],
        'passacre.test': ['data/*.sqlite', 'data/*.yaml', 'data/words',
                          'data/*/words', 'data/*/.passacre.*', 'data/json/*'],
    },
    ext_modules=ext_modules,
    ext_package='passacre',
    setup_requires=['vcversioner'],
    install_requires=['cffi', 'pycparser'],
    extras_require=extras_require,
    entry_points={
        'console_scripts': ['passacre = passacre.application:main'],
    },
    cmdclass={'build': build, 'build_libpassacre': build_libpassacre},
    zip_safe=False,
)
