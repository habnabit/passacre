# Copyright (c) Aaron Gallagher <_@habnab.it>
# See COPYING for details.

from __future__ import print_function

from distutils.command.build import build as _build
from distutils.core import Command
import errno
import os
import re
import subprocess
import sys
import traceback

# may god have mercy on my soul
from setuptools.command.build_ext import build_ext as _build_ext
from setuptools import setup

here = os.path.dirname(os.path.abspath(__file__))
libpassacre_build_dir = os.path.join(here, 'libpassacre')


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


class build_ext(_build_ext):
    sub_commands = [
        ('build_libpassacre', lambda self: True),
    ]

    def run(self):
        for cmd_name in self.get_sub_commands():
            self.run_command(cmd_name)
        libraries = _parse_rustc_libraries()
        for ext_module in self.distribution.ext_modules:
            ext_module.libraries.extend(libraries)
        _build_ext.run(self)


_rustc_library_line = re.compile('^note: ((?:static )?library|framework): (.+)$')


def _parse_rustc_libraries():
    try:
        infile = open(os.path.join(libpassacre_build_dir, '_cargo_out.txt'))
    except IOError as e:
        if e.errno != errno.ENOENT:
            raise
        print('** WARNING: no _cargo_out.txt present; importing passacre might fail **', file=sys.stderr)
        return []

    libraries = []
    with infile:
        for line in infile:
            m = _rustc_library_line.match(line)
            if m is None:
                continue
            lib_type, lib_name = m.groups()
            if lib_type == 'library':
                libraries.append(lib_name)
            else:
                warn = '** WARNING: rust wants us to link a %s? %r **' % (
                    lib_type, lib_name)
                print(warn, file=sys.stderr)

    return libraries


class build(_build):
    def finalize_options(self):
        from cffi.verifier import Verifier
        import _libpassacre
        verifier = Verifier(
            _libpassacre.ffi, _libpassacre.preamble, modulename='_libpassacre_c',
            include_dirs=[libpassacre_build_dir],
            extra_objects=[os.path.join(libpassacre_build_dir, 'libpassacre.a')])
        self.distribution.ext_modules = [verifier.get_extension()]
        _build.finalize_options(self)


extras_require = {
    'yaml': ['PyYAML'],
    'clipboard': ['xerox'],
    'keccak': [],
    'skein': [],
    'yubikey': ['ykpers-cffi'],
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
    py_modules=['_libpassacre'],
    packages=['passacre', 'passacre.test'],
    package_data={
        'passacre': ['schema.sql'],
        'passacre.test': ['data/*.sqlite', 'data/*.yaml', 'data/words',
                          'data/*/words', 'data/*/.passacre.*', 'data/json/*'],
    },
    ext_package='passacre',
    setup_requires=['vcversioner', 'cffi'],
    install_requires=['cffi'],
    extras_require=extras_require,
    entry_points={
        'console_scripts': ['passacre = passacre.application:main'],
    },
    cmdclass={
        'build_ext': build_ext,
        'build_libpassacre': build_libpassacre,
        'build': build,
    },
    zip_safe=False,
)
