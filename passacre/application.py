# Copyright (c) Aaron Gallagher <_@habnab.it>
# See COPYING for details.

from __future__ import unicode_literals

from passacre.config import load as load_config
from passacre.generator import generate_from_config

import argparse
from getpass import getpass
import math
import os
import pprint
import sys

def open_first(paths, mode='r'):
    for path in paths:
        try:
            return open(path, mode)
        except EnvironmentError:
            pass
    raise ValueError('no file in %r could be opened' % (paths,))

class Passacre(object):
    _subcommands = {
        'generate': "generate a password",
        'entropy': "display each site's password entropy",
    }

    def load_config(self):
        "Load the passacre configuration to ``self.config``."
        config_fobj = open_first(['passacre.yaml', os.path.expanduser('~/.passacre.yaml')])
        with config_fobj:
            self.config = load_config(config_fobj)

    def generate_args(self, subparser):
        subparser.add_argument('site', nargs='?',
                               help='site for which to generate a password')
        subparser.add_argument('-n', '--no-newline', action='store_true',
                               help="don't write a newline after the password")
        subparser.add_argument('-c', '--confirm', action='store_true',
                               help='confirm prompted password')

    def generate_action(self, args):
        "Generate a password."
        password = getpass()
        if args.confirm and password != getpass('Confirm password: '):
            raise ValueError("passwords don't match")
        if args.site is None:
            sys.stderr.write('Site: ')
            args.site = raw_input()
        sys.stdout.write(generate_from_config(password, args.site, self.config))
        if not args.no_newline:
            sys.stdout.write('\n')

    def entropy_action(self, args):
        """Display each site's potential password entropy in bits.

        This is the same thing as the base 2 logarithm of the number of
        possible passwords for a site.
        """

        entropy = [
            (site, math.log(site_config['multibase'].max_encodable_value + 1, 2))
            for site, site_config in self.config.items()
        ]
        pprint.pprint(entropy)

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
