# Copyright (c) Aaron Gallagher <_@habnab.it>
# See COPYING for details.

from __future__ import unicode_literals, print_function

from passacre.config import load as load_config, SqliteConfig
from passacre.generator import hash_site
from passacre.util import reify, dotify, nested_get, jdumps
from passacre import __version__, yaml2sqlite

import atexit
import collections
import json
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

if sys.version_info < (3, 3):
    import passacre._argparse as argparse
else:
    import argparse


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

def is_likely_hashed_site(site):
    return len(site) == 48 and '.' not in site

def site_sort_key(site):
    return not is_likely_hashed_site(site), site

def maybe_load_json(val):
    try:
        return json.loads(val)
    except ValueError:
        return val

schema_file = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 'schema.sql')


class Passacre(object):
    atexit = atexit
    xerox = xerox
    prompt = staticmethod(prompt)
    prompt_password = staticmethod(prompt_password)
    sleep = staticmethod(time.sleep)
    _load_config = staticmethod(load_config)

    _config = _config_file = None

    _subcommands = {
        'init': "initialize an sqlite config",
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
            'set-value': "change a schema's value",
            'set-name': "change a schema's name",
        }),
        'config': "view/change global configuration",
        'yaml2sqlite': "convert YAML config to sqlite",
    }

    @reify
    def config(self):
        if self._config is None:
            self.load_config(self._config_file)
        return self._config

    def load_config(self, config_fobj=None, expanduser=None):
        "Load the passacre configuration to ``self.config``."
        if config_fobj is None:
            config_fobj = open_first([
                '~/.config/passacre/passacre.sqlite',
                '~/.config/passacre/passacre.yaml',
                '~/.passacre.sqlite',
                '~/.passacre.yaml',
            ], 'rb', expanduser)
        with config_fobj:
            self._config = self._load_config(config_fobj)


    def init_args(self, subparser):
        subparser.add_argument('path', nargs='?', default='~/.passacre.sqlite',
                               help='path of the config file to initialize (default: %(default)s)')

    def init_action(self, args):
        import sqlite3
        db = sqlite3.connect(os.path.expanduser(args.path))
        curs = db.cursor()
        with open(schema_file) as infile:
            schema = infile.read()
        curs.executescript(schema)

        config = SqliteConfig()
        config._db = db
        config.add_schema('32-printable', [[32, 'printable']])
        schema_id, _ = config.get_schema('32-printable')
        config.add_site('default', schema_id)


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


    def site_args(self, subparser):
        subparser.add_argument('--by-schema', action='store_true',
                               help='list sites organized by schema')

        hash_group = subparser.add_argument_group('for {add,remove,set-schema}')
        hash_group.add_argument('-a', '--hashed', action='store_true',
                                help='hash the site name')
        hash_group.add_argument('-c', '--confirm', action='store_true',
                                help='confirm prompted password')

    def site_action(self, args):
        "Perform an action on a site in a config file."

        sites = self.config.get_all_sites()
        if args.by_schema:
            sites_by_schema = collections.defaultdict(list)
            for site, site_config in sites.items():
                sites_by_schema[site_config['schema-name']].append(site)
            for schema in sorted(sites_by_schema):
                print('%s: %s' % (
                    schema, ', '.join(sorted(sites_by_schema[schema], key=site_sort_key))))
            return

        for site in sorted(sites, key=site_sort_key):
            site_config = sites[site]
            if 'schema-name' in site_config:
                print('%s: %s' % (site, site_config['schema-name']))
            else:
                print(site)


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


    def site_add_args(self, subparser):
        subparser.add_argument('name', help='the name of the site')
        subparser.add_argument('schema', help='the schema to use')

    def site_add_action(self, args):
        schema_id, _ = self.config.get_schema(args.schema)
        if args.hashed:
            password = self.prompt_password(args.confirm)
            args.name = hash_site(password, args.name, self.config.site_hashing)
        self.config.add_site(args.name, schema_id)


    def site_remove_args(self, subparser):
        subparser.add_argument('name', help='the name of the site to remove')

    def site_remove_action(self, args):
        if args.name == 'default':
            sys.exit("can't remove the default site")
        if args.hashed:
            password = self.prompt_password(args.confirm)
            args.name = hash_site(password, args.name, self.config.site_hashing)
        self.config.remove_site(args.name)


    def site_set_schema_args(self, subparser):
        subparser.add_argument('site', help='the name of the site to update')
        subparser.add_argument('schema', help='the schema to use')

    def site_set_schema_action(self, args):
        schema_id, _ = self.config.get_schema(args.schema)
        if args.hashed:
            password = self.prompt_password(args.confirm)
            args.site = hash_site(password, args.site, self.config.site_hashing)
        self.config.set_site_schema(args.site, schema_id)


    def schema_action(self, args):
        "Perform an action on a schema in a config file."

        schemata = self.config.get_all_schemata()
        for schema in sorted(schemata):
            print('%s: %s' % (schema, jdumps(schemata[schema])))


    def schema_add_args(self, subparser):
        subparser.add_argument('name', help='the name of the schema')
        subparser.add_argument('value', help='the value of the schema')

    def schema_add_action(self, args):
        self.config.add_schema(args.name, json.loads(args.value))


    def schema_remove_args(self, subparser):
        subparser.add_argument('name', help='the name of the schema to remove')

    def schema_remove_action(self, args):
        schema_id, _ = self.config.get_schema(args.name)
        self.config.remove_schema(schema_id)


    def schema_set_name_args(self, subparser):
        subparser.add_argument('oldname', help='the schema to set the name of')
        subparser.add_argument('newname', help='the new name of the schema')

    def schema_set_name_action(self, args):
        schema_id, _ = self.config.get_schema(args.oldname)
        self.config.set_schema_name(schema_id, args.newname)


    def schema_set_value_args(self, subparser):
        subparser.add_argument('name', help='the name of the schema')
        subparser.add_argument('value', help='the new value for the schema')

    def schema_set_value_action(self, args):
        schema_id, _ = self.config.get_schema(args.name)
        self.config.set_schema_value(schema_id, json.loads(args.value))


    def config_args(self, subparser):
        subparser.add_argument('-s', '--site',
                               help='the site to operate on or omitted for global config')
        subparser.add_argument('-a', '--hashed', action='store_true',
                               help='hash the site name')
        subparser.add_argument('-c', '--confirm', action='store_true',
                               help='confirm prompted password')
        subparser.add_argument('name', nargs='?',
                               help='the config option to get or set or omitted to get all')
        subparser.add_argument('value', nargs='?',
                               help='the new value to set or omitted to get')

    def config_action(self, args):
        if args.hashed and args.site:
            password = self.prompt_password(args.confirm)
            args.site = hash_site(password, args.site, self.config.site_hashing)
        if not args.name:
            for k, v in sorted(dotify(self.config.get_site_config(args.site))):
                print('%s: %s' % (k, jdumps(v)))
            return
        if not args.value:
            print(jdumps(nested_get(
                self.config.get_site_config(args.site), args.name.split('.'))))
            return
        self.config.set_config(args.site, args.name, maybe_load_json(args.value))

    def yaml2sqlite_args(self, subparser):
        subparser.add_argument('infile', type=argparse.FileType('rb'),
                               help='the input YAML config file')
        subparser.add_argument('outfile', type=argparse.FileType('wb'),
                               help='the output sqlite config file')

    def yaml2sqlite_action(self, args):
        import sqlite3
        db = sqlite3.connect(args.outfile.name)
        curs = db.cursor()
        with open(schema_file) as infile:
            schema = infile.read()
        curs.executescript(schema)

        yaml2sqlite.main(args.infile.name, args.outfile.name)

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
                command = subaction_prefix + 'command'
                subsubparsers = subparser.add_subparsers(dest=command)
                self.build_subcommands(subaction_prefix, subsubparsers, subsubcommands)

    def build_parser(self):
        "Build an ``ArgumentParser`` from the defined subcommands."
        parser = argparse.ArgumentParser(prog='passacre')
        parser.add_argument('-V', '--version', action='version',
                            version='%(prog)s ' + __version__)
        parser.add_argument('-f', '--config', type=argparse.FileType('rb'),
                            help='specify a config file to use')
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
        parser = self.build_parser()
        args = parser.parse_args(args)
        self._config_file = args.config
        action = self.find_action(args)
        if not action:
            parser.print_help()
            sys.exit(2)
        action_method = getattr(self, action + '_action')
        action_method(args)

def main(args=None):
    Passacre().main(args)
