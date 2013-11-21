# Copyright (c) Aaron Gallagher <_@habnab.it>
# See COPYING for details.

from __future__ import unicode_literals, print_function

from passacre.compat import input, argparse, python_2_encode
from passacre.config import load as load_config, SqliteConfig
from passacre.generator import hash_site
from passacre.jsonmini import unparse as jdumps
from passacre.schema import multibase_of_schema
from passacre.util import reify, dotify, nested_get, jloads, errormark
from passacre import __version__, completion, features, yaml2sqlite

import atexit
import collections
from getpass import getpass
import math
import operator
import os
import sys
import time
import traceback

try:
    import xerox
except ImportError:  # pragma: nocover
    xerox = None


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
        return jloads(val)
    except ValueError:
        return val

def transform_args(transformations):
    def deco(f):
        def wrap(self, args):
            for attr, transformer in transformations:
                val = getattr(args, attr)
                if val is not None:
                    val = transformer(val)
                    setattr(args, attr, val)
            return f(self, args)
        return wrap
    return deco

def needs_mutable_config(f):
    def wrap(self, args):
        if not self.config.is_mutable_config:
            raise NotImplementedError(
                'this command requires a mutable config (i.e. sqlite format)')
        return f(self, args)
    return wrap

schema_file = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 'schema.sql')


class Passacre(object):
    atexit = atexit
    xerox = xerox
    prompt = staticmethod(prompt)
    _prompt_password = staticmethod(prompt_password)
    sleep = staticmethod(time.sleep)
    _load_config = staticmethod(load_config)
    environ = os.environ

    _config = _config_file = None

    _subcommands = {
        'init': "initialize an sqlite config",
        'generate': "generate a password",
        'entropy': "display each site's password entropy",
        'site': ("actions on sites", {
            'add': "add a site to a config file",
            'remove': "remove a site from a config file",
            'config': "change a site's configuration",
            'set-schema': "change a site's schema",
            'set-name': "change a site's domain",
            'hash': "hash a site's name",
            'hash-all': "hash all non-hashed sites",
        }),
        'schema': ("actions on schemata", {
            'add': "add a schema",
            'remove': "remove a schema",
            'set-value': "change a schema's value",
            'set-name': "change a schema's name",
        }),
        'config': "view/change global configuration",
        'info': "information about the passacre environment",
        'agent': ("commands for passacre-agent", {
            'run': "run the passacre agent",
            'lock': "lock the passacre agent",
            'unlock': "unlock the passacre agent",
        }),
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

    def prompt_password(self, confirm):
        if self.config.global_config.get('always-confirm-passwords'):
            confirm = True
        return self._prompt_password(confirm)


    try:
        from passacre.agent.main import run_amp_command as _run_amp_command
    except ImportError:
        pass
    else:
        _run_amp_command = staticmethod(_run_amp_command)


    @features.agent.check
    @errormark('communicating with the passacre agent')
    def _run_agent(self, command, **args):
        from twisted.internet import endpoints

        if 'PASSACRE_AGENT' not in self.environ:
            raise ValueError("'PASSACRE_AGENT' is not set")
        description = self.environ['PASSACRE_AGENT']
        if description.startswith('/'):
            description = 'unix:' + endpoints.quoteStringArgument(description)
        return self._run_amp_command(description, command, args)


    def init_args(self, subparser):
        subparser.add_argument('path', nargs='?', default='~/.passacre.sqlite',
                               help='path of the config file to initialize (default: %(default)s)')
        subparser.add_argument('-y', '--from-yaml', type=argparse.FileType('rb'), metavar='YAML',
                               help='optional input YAML config file to convert from'
        ).completer = completion.FilesCompleter()

    def init_action(self, args):
        import sqlite3
        path = os.path.expanduser(args.path)
        db = sqlite3.connect(path)
        curs = db.cursor()
        with open(schema_file) as infile:
            schema = infile.read()
        curs.executescript(schema)

        if args.from_yaml:
            yaml2sqlite.main(args.from_yaml.name, path)
        else:
            config = SqliteConfig()
            config._db = db
            config.add_schema('32-printable', [[32, 'printable']])
            schema_id, _ = config.get_schema('32-printable')
            config.add_site('default', schema_id)


    def generate_args(self, subparser):
        subparser.add_argument('site', nargs='?',
                               help='site for which to generate a password'
        ).completer = completion.SitesCompleter()
        subparser.add_argument('-o', '--override-config', metavar='CONFIG',
                               help='a JSON dictionary of config values to override')
        subparser.add_argument('-u', '--username',
                               help='username for the site')
        subparser.add_argument('-n', '--no-newline', action='store_true',
                               help="don't write a newline after the password")
        subparser.add_argument('-c', '--confirm', action='store_true',
                               help='confirm prompted password')
        subparser.add_argument('-S', '--save', action='store_true', default=None,
                               help='save the site name to the site list (only works '
                               'with passacre agent)')
        subparser.add_argument('-s', '--no-save', action='store_false', dest='save',
                               help='do not save the site name to the site list')
        if self.xerox is not None:
            subparser.add_argument('-C', '--copy', action='store_true',
                                   help='put the generated password on the clipboard')
            subparser.add_argument('-w', '--timeout', type=int, metavar='N',
                                   help='clear the clipboard after N seconds')


    def _generate_from_agent(self, args):
        from passacre.agent import commands
        if args.save is None:
            site_list = self.config.global_config.get('site-list', {})
            args.save = site_list.get('auto-save')
        try:
            results = self._run_agent(
                commands.Generate, site=args.site, username=args.username, save_site=args.save)
        except Exception:
            try:
                self.excepthook(*sys.exc_info())
            except SystemExit:
                pass
            print('falling back on no agent', file=sys.stderr)
            return False
        password = python_2_encode(results['password'])
        self._process_generated_password(password, args)
        return True

    @transform_args([
        ('override_config', jloads),
    ])
    def generate_action(self, args):
        "Generate a password."
        if args.site is None:
            args.site = self.prompt('Site: ')
        if 'PASSACRE_AGENT' in self.environ:
            if self._generate_from_agent(args):
                return
        password = self.prompt_password(args.confirm)
        password = self.config.generate_for_site(
            args.username, password, args.site, args.override_config)
        self._process_generated_password(password, args)

    def _process_generated_password(self, password, args):
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


    def entropy_args(self, subparser):
        subparser.add_argument('--schema', action='store_true',
                               help='show entropy by schema instead of by site')

    def entropy_action(self, args):
        """Display each site's potential password entropy in bits.

        This is the same thing as the base 2 logarithm of the number of
        possible passwords for a site.
        """

        entropy = [('schema' if args.schema else 'site', 'entropy', '(bits)'), ('', '', '')]
        if args.schema:
            pre_entropy = []
            for schema_name, schema in self.config.get_all_schemata().items():
                multibase = multibase_of_schema(schema, self.config.words)
                pre_entropy.append((schema_name, math.log(multibase.max_encodable_value + 1, 2)))
        else:
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
        subparser.add_argument('--omit-hashed', action='store_true',
                               help="don't list hashed sites")

        hash_group = subparser.add_argument_group('for {add,remove,set-schema}')
        hash_group.add_argument('-a', '--hashed', action='store_true',
                                help='hash the site name')

        confirm_group = subparser.add_argument_group('for {add,remove,set-schema,hash-all}')
        confirm_group.add_argument('-c', '--confirm', action='store_true',
                                   help='confirm prompted password')

    def _fill_in_sites_from_agent(self, sites):
        if 'PASSACRE_AGENT' not in self.environ:
            return

        from passacre.agent import commands
        results = self._run_agent(commands.FetchSiteList)
        for site in results['sites']:
            sites.setdefault(site, {})

    def site_action(self, args):
        "Perform an action on a site in a config file."

        sites = self.config.get_all_sites()
        if args.omit_hashed:
            sites = dict((name, config) for name, config in sites.items()
                         if not is_likely_hashed_site(name))
        if args.by_schema:
            sites_by_schema = collections.defaultdict(list)
            for site, site_config in sites.items():
                sites_by_schema[site_config['schema-name']].append(site)
            for schema in sorted(sites_by_schema):
                print('%s: %s' % (
                    schema, ', '.join(sorted(sites_by_schema[schema], key=site_sort_key))))
            return

        self._fill_in_sites_from_agent(sites)
        for site in sorted(sites, key=site_sort_key):
            site_config = sites[site]
            if 'schema-name' in site_config:
                print('%s: %s' % (site, site_config['schema-name']))
            else:
                print(site)


    def perhaps_hash_site(self, args):
        if args.hashed or (self.config.site_hashing['enabled'] == 'always' and args.site != 'default'):
            password = self.prompt_password(args.confirm)
            args.site = hash_site(password, args.site, self.config.site_hashing)


    def site_hash_args(self, subparser):
        subparser.add_argument('site', nargs='?',
                               help='the site to hash'
        ).completer = completion.SitesCompleter()
        subparser.add_argument('-m', '--method',
                               help='which hash method to use'
        ).completer = completion.HashMethodsCompleter()
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

    def site_hash_all_args(self, subparser):
        subparser.add_argument('-m', '--method',
                               help='which hash method to use'
        ).completer = completion.HashMethodsCompleter()
        subparser.add_argument('-c', '--confirm', action='store_true',
                               help='confirm prompted password')

    @needs_mutable_config
    def site_hash_all_action(self, args):
        """Hash all non-hashed sites."""

        password = self.prompt_password(args.confirm)
        config = self.config.site_hashing
        if args.method is not None:
            config['method'] = args.method
        for site in self.config.get_all_sites():
            if site == 'default' or is_likely_hashed_site(site):
                continue
            self.config.rename_site(site, hash_site(password, site, config))


    def site_add_args(self, subparser):
        subparser.add_argument('site', help='the name of the site')
        subparser.add_argument('schema', help='the schema to use'
        ).completer = completion.SchemataCompleter()
        subparser.add_argument('-N', '--new-schema', metavar='VALUE',
                               help='a schema value for the new schema')

    @transform_args([
        ('new_schema', jloads),
    ])
    @needs_mutable_config
    def site_add_action(self, args):
        if args.new_schema:
            self.config.add_schema(args.schema, args.new_schema)
        schema_id, _ = self.config.get_schema(args.schema)
        self.perhaps_hash_site(args)
        self.config.add_site(args.site, schema_id)


    def site_remove_args(self, subparser):
        subparser.add_argument('site', help='the name of the site to remove'
        ).completer = completion.SitesCompleter()

    @needs_mutable_config
    def site_remove_action(self, args):
        if args.site == 'default':
            sys.exit("can't remove the default site")
        self.perhaps_hash_site(args)
        self.config.remove_site(args.site)


    def site_set_schema_args(self, subparser):
        subparser.add_argument('site', help='the name of the site to update'
        ).completer = completion.SitesCompleter()
        subparser.add_argument('schema', help='the schema to use'
        ).completer = completion.SchemataCompleter()

    @needs_mutable_config
    def site_set_schema_action(self, args):
        schema_id, _ = self.config.get_schema(args.schema)
        self.perhaps_hash_site(args)
        self.config.set_site_schema(args.site, schema_id)


    def site_set_name_args(self, subparser):
        subparser.add_argument('oldname', help='the name of the site to update'
        ).completer = completion.SitesCompleter()
        subparser.add_argument('newname', help='the new name for the site')

    @needs_mutable_config
    def site_set_name_action(self, args):
        if args.oldname == 'default':
            sys.exit("can't rename the default site")
        password = None
        if args.hashed or self.config.site_hashing['enabled'] == 'always':
            password = self.prompt_password(args.confirm)
            args.oldname = hash_site(password, args.oldname, self.config.site_hashing)
            args.newname = hash_site(password, args.newname, self.config.site_hashing)
        self.config.rename_site(args.oldname, args.newname)


    def schema_action(self, args):
        "Perform an action on a schema in a config file."

        schemata = self.config.get_all_schemata()
        for schema in sorted(schemata):
            print('%s: %s' % (schema, jdumps(schemata[schema])))


    def schema_add_args(self, subparser):
        subparser.add_argument('name', help='the name of the schema')
        subparser.add_argument('value', help='the value of the schema')

    @transform_args([
        ('value', jloads),
    ])
    @needs_mutable_config
    def schema_add_action(self, args):
        self.config.add_schema(args.name, args.value)


    def schema_remove_args(self, subparser):
        subparser.add_argument('name', help='the name of the schema to remove'
        ).completer = completion.SchemataCompleter()

    @needs_mutable_config
    def schema_remove_action(self, args):
        schema_id, _ = self.config.get_schema(args.name)
        self.config.remove_schema(schema_id)


    def schema_set_name_args(self, subparser):
        subparser.add_argument('oldname', help='the schema to set the name of'
        ).completer = completion.SchemataCompleter()
        subparser.add_argument('newname', help='the new name of the schema')

    @needs_mutable_config
    def schema_set_name_action(self, args):
        schema_id, _ = self.config.get_schema(args.oldname)
        self.config.set_schema_name(schema_id, args.newname)


    def schema_set_value_args(self, subparser):
        subparser.add_argument('name', help='the name of the schema'
        ).completer = completion.SchemataCompleter()
        subparser.add_argument('value', help='the new value for the schema')

    @transform_args([
        ('value', jloads),
    ])
    @needs_mutable_config
    def schema_set_value_action(self, args):
        schema_id, _ = self.config.get_schema(args.name)
        self.config.set_schema_value(schema_id, args.value)


    def _base_config_args(self, subparser):
        subparser.add_argument('-a', '--hashed', action='store_true',
                               help='hash the site name')
        subparser.add_argument('-c', '--confirm', action='store_true',
                               help='confirm prompted password')
        subparser.add_argument('name', nargs='?',
                               help='the config option to get or set or omitted to get all')
        subparser.add_argument('value', nargs='?',
                               help='the new value to set or omitted to get')

    def config_args(self, subparser):
        subparser.add_argument('-s', '--site',
                               help='the site to operate on or omitted for global config'
        ).completer = completion.SitesCompleter()
        self._base_config_args(subparser)

    def config_action(self, args):
        if args.site:
            self.perhaps_hash_site(args)
        if not args.name:
            for k, v in sorted(dotify(self.config.get_site_config(args.site))):
                print('%s: %s' % (k, jdumps(v)))
            return
        if not args.value:
            value = nested_get(
                self.config.get_site_config(args.site), args.name.split('.'))
            if value is not None:
                print(jdumps(value))
            return
        self.config.set_config(args.site, args.name, maybe_load_json(args.value))

    def site_config_args(self, subparser):
        subparser.add_argument('site', help='the site to operate on'
        ).completer = completion.SitesCompleter()
        self._base_config_args(subparser)

    site_config_action = config_action


    @features.agent.check
    def agent_action(self, args):
        from passacre.agent import commands
        if 'PASSACRE_AGENT' not in self.environ:
            print('no PASSACRE_AGENT set')
            return
        print('PASSACRE_AGENT: %(PASSACRE_AGENT)s' % self.environ)
        results = self._run_agent(commands.Version)
        print('passacre version %(version)s (%(sha)s)' % results)

    def agent_run_args(self, subparser):
        subparser.add_argument('port', help='the port to listen on')

    @features.agent.check
    def agent_run_action(self, args):
        from passacre.agent.main import server_main
        server_main(type(self), args.port)

    def agent_unlock_args(self, subparser):
        subparser.add_argument('-c', '--confirm', action='store_true',
                               help='confirm prompted password')

    @features.agent.check
    def agent_unlock_action(self, args):
        from passacre.agent import commands
        password = self.prompt_password(args.confirm)
        self._run_agent(commands.Unlock, password=password)

    @features.agent.check
    def agent_lock_action(self, args):
        from passacre.agent import commands
        self._run_agent(commands.Lock)


    def info_action(self, args):
        print('passacre version ' + __version__)
        print()
        for feature in features.features:
            outcome = 'usable' if feature.usable else 'NOT USABLE'
            print('feature "%s": %s' % (feature.name, outcome))
            for s in feature.usability_strings():
                print(' ', s)
            print()


    def build_subcommands(self, action_prefix, subparsers, subcommands):
        for subcommand, subcommand_help in sorted(subcommands.items()):
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
        parser.add_argument('-v', '--verbose', action='store_true',
                            help='increase output on errors')
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

    def excepthook(self, type_, value, tb):
        errormark = getattr(value, '_errormark', None)
        exitcode = 1
        if errormark is not None:
            description, exitcode, a, kw = errormark
            description = description.format(*a, **kw)
            print('an error occurred {0}'.format(description), file=sys.stderr)
        if self.verbose:
            traceback.print_exception(type_, value, tb, file=sys.stderr)
        else:
            print('(pass -v for the full traceback)', file=sys.stderr)
            print('{0.__name__}: {1}'.format(type_, value), file=sys.stderr)
        sys.exit(exitcode)

    def main(self, args=None):
        parser = self.build_parser()
        args = parser.parse_args(args)
        self.verbose = args.verbose
        self._config_file = args.config
        action = self.find_action(args)
        if not action:
            parser.print_help()
            sys.exit(2)
        action_method = getattr(self, action + '_action')
        sys.excepthook = self.excepthook
        try:
            action_method(args)
        except KeyboardInterrupt:
            sys.exit(4)

def main(args=None):  # pragma: nocover
    Passacre().main(args)
