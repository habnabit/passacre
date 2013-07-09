# Copyright (c) Aaron Gallagher <_@habnab.it>
# See COPYING for details.

from __future__ import unicode_literals

from passacre.config import load as load_config
from passacre.generator import hash_site

import argparse
import atexit
from getpass import getpass
import math
import os
import pprint
import sys
import time

try:
    import xerox
except ImportError:
    xerox = None

if sys.version_info < (3,):
    input = raw_input
    def perhaps_decode(s):
        return s.decode('utf-8')
else:
    perhaps_decode = lambda x: x

def open_first(paths, mode='r'):
    for path in paths:
        try:
            return open(os.path.expanduser(path), mode)
        except EnvironmentError:
            pass
    raise ValueError('no file in %r could be opened' % (paths,))

def idna_encode(site):
    return perhaps_decode(site).encode('idna').decode()

class Passacre(object):
    _subcommands = {
        'generate': "generate a password",
        'entropy': "display each site's password entropy",
        'sitehash': "hash a site's name",
    }

    def load_config(self):
        "Load the passacre configuration to ``self.config``."
        config_fobj = open_first([
            '~/.config/passacre/passacre.sqlite',
            '~/.config/passacre/passacre.yaml',
            '~/.passacre.sqlite',
            '~/.passacre.yaml',
        ], 'rb')
        with config_fobj:
            self.config = load_config(config_fobj)

    def generate_args(self, subparser):
        subparser.add_argument('site', nargs='?',
                               help='site for which to generate a password')
        subparser.add_argument('-u', '--username',
                               help='username for the site')
        subparser.add_argument('-n', '--no-newline', action='store_true',
                               help="don't write a newline after the password")
        subparser.add_argument('-c', '--confirm', action='store_true',
                               help='confirm prompted password')
        if xerox is not None:
            subparser.add_argument('-C', '--copy', action='store_true',
                                   help='put the generated password on the clipboard')
            subparser.add_argument('-w', '--timeout', type=int, metavar='N',
                                   help='clear the clipboard after N seconds')

    def generate_action(self, args):
        "Generate a password."
        password = getpass()
        if args.confirm and password != getpass('Confirm password: '):
            raise ValueError("passwords don't match")
        if args.site is None:
            sys.stderr.write('Site: ')
            args.site = input()
        password = self.config.generate_for_site(
            args.username, password, idna_encode(args.site))
        if getattr(args, 'copy', False):  # since the argument might not exist
            sys.stderr.write('password copied.\n')
            xerox.copy(password)
            if args.timeout:
                atexit.register(xerox.copy, '')
                try:
                    time.sleep(args.timeout)
                except KeyboardInterrupt:
                    pass
        else:
            sys.stdout.write(password)
            if not args.no_newline:
                sys.stdout.write('\n')

    def entropy_action(self, args):
        """Display each site's potential password entropy in bits.

        This is the same thing as the base 2 logarithm of the number of
        possible passwords for a site.
        """

        entropy = [
            (site, math.log(site_config['multibase'].max_encodable_value + 1, 2))
            for site, site_config in self.config.get_all_sites().items()
        ]
        pprint.pprint(entropy)

    def sitehash_args(self, subparser):
        subparser.add_argument('method', nargs='?',
                               help='which hash method to use')
        subparser.add_argument('-n', '--no-newline', action='store_true',
                               help="don't write a newline after the hash")
        subparser.add_argument('-c', '--confirm', action='store_true',
                               help='confirm prompted password')

    def sitehash_action(self, args):
        """Hash a site.

        This is so that hostnames need not leak from a config file; the hashed
        site name is tried if the unhashed name doesn't exist.
        """

        password = getpass()
        if args.confirm and password != getpass('Confirm password: '):
            raise ValueError("passwords don't match")
        sys.stderr.write('Site: ')
        site = input()
        config = self.config.site_hashing
        if args.method is not None:
            config['method'] = args.method
        sys.stdout.write(hash_site(password, idna_encode(site), config))
        if not args.no_newline:
            sys.stdout.write('\n')

    def build_parser(self):
        "Build an ``ArgumentParser`` from the defined subcommands."
        parser = argparse.ArgumentParser(prog='passacre')
        subparsers = parser.add_subparsers()
        for subcommand, subcommand_help in self._subcommands.items():
            action_method = getattr(self, '%s_action' % (subcommand,))
            subparser = subparsers.add_parser(
                subcommand, help=subcommand_help, description=action_method.__doc__)
            args_method = getattr(self, '%s_args' % (subcommand,), None)
            if args_method is not None:
                args_method(subparser)
            subparser.set_defaults(func=action_method)
        return parser

    def main(self, args=None):
        self.load_config()
        args = self.build_parser().parse_args(args)
        args.func(args)

def main(args=None):
    Passacre().main(args)
