# Copyright (c) Aaron Gallagher <_@habnab.it>
# See COPYING for details.

from __future__ import unicode_literals, print_function

from passacre.config import load as load_config
from passacre.generator import hash_site

import argparse
import atexit
from getpass import getpass
import math
import operator
import os
import sys
import time

try:
    import xerox
except ImportError:
    xerox = None


if sys.version_info < (3,):
    input = raw_input


def open_first(paths, mode='r', expanduser=None, open=open):
    if expanduser is None:
        expanduser = os.path.expanduser
    for path in paths:
        try:
            return open(expanduser(path), mode)
        except EnvironmentError:
            pass
    raise ValueError('no file in %r could be opened' % (paths,))

def prompt(query, input=input):
    sys.stderr.write(query)
    return input()

def prompt_password(confirm=False, getpass=getpass):
    password = getpass()
    if confirm and password != getpass('Confirm password: '):
        raise ValueError("passwords don't match")
    return password


class Passacre(object):
    atexit = atexit
    xerox = xerox
    prompt = staticmethod(prompt)
    prompt_password = staticmethod(prompt_password)
    sleep = staticmethod(time.sleep)
    _load_config = staticmethod(load_config)

    _subcommands = {
        'generate': "generate a password",
        'entropy': "display each site's password entropy",
        'site': ("actions on sites", {
            'add': "add a site to a config file",
            'remove': "remove a site from a config file",
            'set-schema': "change a site's schema",
            'hash': "hash a site's name",
        }),
        'schema': ("actions on schemata", {
            'add': "add a schema",
            'remove': "remove a schema",
            'set': "change a schema",
        }),
    }

    def load_config(self, expanduser=None):
        "Load the passacre configuration to ``self.config``."
        config_fobj = open_first([
            '~/.config/passacre/passacre.sqlite',
            '~/.config/passacre/passacre.yaml',
            '~/.passacre.sqlite',
            '~/.passacre.yaml',
        ], 'rb', expanduser)
        with config_fobj:
            self.config = self._load_config(config_fobj)

    def generate_args(self, subparser):
        subparser.add_argument('site', nargs='?',
                               help='site for which to generate a password')
        subparser.add_argument('-u', '--username',
                               help='username for the site')
        subparser.add_argument('-n', '--no-newline', action='store_true',
                               help="don't write a newline after the password")
        subparser.add_argument('-c', '--confirm', action='store_true',
                               help='confirm prompted password')
        if self.xerox is not None:
            subparser.add_argument('-C', '--copy', action='store_true',
                                   help='put the generated password on the clipboard')
            subparser.add_argument('-w', '--timeout', type=int, metavar='N',
                                   help='clear the clipboard after N seconds')

    def generate_action(self, args):
        "Generate a password."
        password = self.prompt_password(args.confirm)
        if args.site is None:
            args.site = self.prompt('Site: ')
        password = self.config.generate_for_site(
            args.username, password, args.site)
        if getattr(args, 'copy', False):  # since the argument might not exist
            sys.stderr.write('password copied.\n')
            self.xerox.copy(password)
            if args.timeout:
                self.atexit.register(self.xerox.copy, '')
                try:
                    self.sleep(args.timeout)
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

        entropy = [('site', 'entropy', '(bits)'), ('', '', '')]
        default_site = self.config.get_site('default')
        pre_entropy = [
            (site, math.log(site_config['multibase'].max_encodable_value + 1, 2))
            for site, site_config in self.config.get_all_sites().items()
            if site_config['schema'] != default_site['schema'] or site == 'default'
        ]
        pre_entropy.sort(key=operator.itemgetter(1, 0), reverse=True)
        entropy.extend([site] + ('%0.2f' % bits).split('.')
                       for site, bits in pre_entropy)
        max_site_len, max_ibits_len, max_fbits_len = [
            len(max(x, key=len)) for x in zip(*entropy)]
        print()
        for e, (site, ibits, fbits) in enumerate(entropy):
            if e == 0:
                site = site.center(max_site_len)
            print('%*s   %*s%s%*s' % (
                -max_site_len, site, max_ibits_len, ibits,
                '.' if ibits.isdigit() else ' ', -max_fbits_len, fbits))

    def site_action(self, args):
        "Perform an action on a site in a config file."

    def site_hash_args(self, subparser):
        subparser.add_argument('site', nargs='?',
                               help='the site to hash')
        subparser.add_argument('-m', '--method',
                               help='which hash method to use')
        subparser.add_argument('-n', '--no-newline', action='store_true',
                               help="don't write a newline after the hash")
        subparser.add_argument('-c', '--confirm', action='store_true',
                               help='confirm prompted password')

    def site_hash_action(self, args):
        """Hash a site.

        This is so that hostnames need not leak from a config file; the hashed
        site name is tried if the unhashed name doesn't exist.
        """

        password = self.prompt_password(args.confirm)
        if args.site is None:
            args.site = self.prompt('Site: ')
        config = self.config.site_hashing
        if args.method is not None:
            config['method'] = args.method
        sys.stdout.write(hash_site(password, args.site, config))
        if not args.no_newline:
            sys.stdout.write('\n')

    def site_add_action(self, args):
        pass

    def site_remove_action(self, args):
        pass

    def site_set_schema_action(self, args):
        pass

    def schema_action(self, args):
        "Perform an action on a schema in a config file."

    def schema_add_action(self, args):
        pass

    def schema_remove_action(self, args):
        pass

    def schema_set_action(self, args):
        pass

    def build_subcommands(self, action_prefix, subparsers, subcommands):
        for subcommand, subcommand_help in subcommands.items():
            subsubcommand = False
            if isinstance(subcommand_help, tuple):
                subcommand_help, subsubcommands = subcommand_help
                subsubcommand = True
            subcommand_method = action_prefix + subcommand.replace('-', '_')
            action_method = getattr(self, '%s_action' % (subcommand_method,))
            subparser = subparsers.add_parser(
                subcommand, help=subcommand_help, description=action_method.__doc__)
            args_method = getattr(self, '%s_args' % (subcommand_method,), None)
            if args_method is not None:
                args_method(subparser)

            if subsubcommand:
                subaction_prefix = subcommand_method + '_'
                subsubparsers = subparser.add_subparsers(dest=subaction_prefix + 'command')
                self.build_subcommands(subaction_prefix, subsubparsers, subsubcommands)

    def build_parser(self):
        "Build an ``ArgumentParser`` from the defined subcommands."
        parser = argparse.ArgumentParser(prog='passacre')
        subparsers = parser.add_subparsers(dest='command')
        self.build_subcommands('', subparsers, self._subcommands)
        return parser

    def find_action(self, args):
        if not args.command:
            return None
        command = ret = args.command.replace('-', '_')
        while True:
            next_command = command + '_command'
            subcommand = getattr(args, next_command, None)
            if subcommand is None:
                break
            command, ret = next_command, '%s_%s' % (ret, subcommand.replace('-', '_'))
        return ret

    def main(self, args=None):
        self.load_config()
        parser = self.build_parser()
        args = parser.parse_args(args)
        action = self.find_action(args)
        if not action:
            parser.print_help()
            sys.exit(2)
        action_method = getattr(self, action + '_action')
        action_method(args)

def main(args=None):
    Passacre().main(args)
