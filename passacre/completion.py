# Copyright (c) Aaron Gallagher <_@habnab.it>
# See COPYING for details.

from __future__ import print_function

from passacre import _argparse as argparse


def escape(x):
    """
    Shell escape the given string

    Implementation borrowed from now-deprecated commands.mkarg() in the stdlib
    """
    if '\'' not in x:
        return '\'' + x + '\''
    s = '"'
    for c in x:
        if c in '\\$"`':
            s = s + '\\'
        s = s + c
    s = s + '"'
    return s


_OMIT_DASH_F = object()


class NullCompleter(object):
    def zsh_action(self):
        return ' '

    def fish_action(self):
        return '()'


class FilesCompleter(object):
    def zsh_action(self):
        return '_files'

    def fish_action(self):
        return _OMIT_DASH_F


class SchemataCompleter(object):
    def zsh_action(self):
        return '_passacre_schemata'

    def fish_action(self):
        return '(__fish_passacre_schemata)'


class SitesCompleter(object):
    def zsh_action(self):
        return '_passacre_sites'

    def fish_action(self):
        return '(__fish_passacre_sites)'


class HashMethodsCompleter(object):
    def zsh_action(self):
        return '_passacre_hash_methods'

    def fish_action(self):
        return 'keccak skein'


def zsh_arguments_for(arguments):
    for arg in arguments:
        completer = getattr(arg, 'completer', None) or NullCompleter()
        if not arg.option_strings:
            yield escape(':%s:%s' % (arg.dest, completer.zsh_action()))
            continue

        option_strings = []
        if len(arg.option_strings) > 1:
            options = set(arg.option_strings)
            for option in sorted(options):
                rest = options - set([option])
                option_string = '(%s)%s' % (' '.join(rest), option)
                option_strings.append(option_string)
        else:
            option_strings.append(arg.option_strings[0])

        takes_argument = arg.nargs != 0
        equals = action = ''
        if takes_argument:
            equals = '='
            action = ':%s:%s' % (arg.metavar or ' ', completer.zsh_action())
        for option_string in option_strings:
            yield escape('%s%s[%s]%s' % (option_string, equals, arg.help, action))


def _zsh_completion_for(parser, name=''):
    subcommands = []
    arguments = []

    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            for subaction_name, subaction in sorted(action.choices.items()):
                pseudo_action = next(pa for pa in action._choices_actions if pa.dest == subaction_name)
                full_subaction_name = name + '_' + subaction_name.replace('-', '_')
                subcommands.append((
                    subaction_name, full_subaction_name, pseudo_action.help,
                    _zsh_completion_for(subaction, full_subaction_name)))
        else:
            arguments.append(action)

    if not subcommands:
        return False, arguments

    print("""
_passacre_subcommand%s () {
    """ % (name,))

    print("""
    if [[ $CURRENT = 1 ]]; then
        local _passacre_commands
        _passacre_commands=(%s)
        _describe 'subcommand' _passacre_commands
    fi
    case $line[1] in
    """ % (' '.join(escape('%s:%s' % (n, desc)) for n, _, desc, _ in subcommands),))

    for subcommand_name, full_subaction_name, _, (has_subcommands, subcommand_arguments) in subcommands:
        next_parser = ''
        if has_subcommands:
            next_parser = escape('*::site cmd:_passacre_subcommand%s' % (full_subaction_name,))
        print("""
        (%s)
            _arguments -S \\
                %s %s \\
                && return 0
            ;;
        """ % (subcommand_name, next_parser, ' '.join(zsh_arguments_for(subcommand_arguments))))

    print("""
    esac
}
    """)

    return True, arguments


def zsh_completion_for(parser):
    print('#compdef passacre')
    _, arguments = _zsh_completion_for(parser)
    print("""
_passacre () {
    _arguments -S \\
        '*::cmd:_passacre_subcommand' \\
        %s \\
        && return 0
}


_passacre_sites () {
    local -a _passacre_site_list
    _passacre_site_list=($(passacre site --omit-hashed | cut -d: -f1))
    _wanted _passacre_site_list expl 'passacre sites' compadd -a _passacre_site_list
}


_passacre_schemata () {
    local -a _passacre_schema_list
    _passacre_schema_list=($(passacre schema | cut -d: -f1))
    _wanted _passacre_schema_list expl 'passacre schemata' compadd -a _passacre_schema_list
}


_passacre_hash_methods () {
    local -a _passacre_hash_method_list
    _passacre_hash_method_list=(keccak skein)
    _wanted _passacre_hash_method_list expl 'passacre hash methods' compadd -a _passacre_hash_method_list
}


_passacre "$@"
""" % (' '.join(zsh_arguments_for(arguments)),))


def _fish_completion_for(parser, name='passacre'):
    subcommands = []
    arguments = []

    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            for subaction_name, subaction in sorted(action.choices.items()):
                pseudo_action = next(pa for pa in action._choices_actions if pa.dest == subaction_name)
                full_subaction_name = name + ' ' + subaction_name
                subcommands.append((subaction_name, pseudo_action.help))
                _fish_completion_for(subaction, full_subaction_name)
        else:
            arguments.append(action)

    n_positional = 0

    for arg in arguments:
        completer = getattr(arg, 'completer', None) or NullCompleter()
        positional = not arg.option_strings

        short_opt = long_opt = ''
        for option in arg.option_strings:
            if option.startswith('--'):
                long_opt = '-l ' + option.lstrip('-')
            elif option.startswith('-'):
                short_opt = '-s ' + option.lstrip('-')

        positional_stars = ''
        if positional:
            positional_stars = ' '.join(['"*"'] * n_positional)
            n_positional += 1
        predicate = '-n %s' % escape('__fish_passacre_using_command %s %s' % (name, positional_stars))
        takes_argument = arg.nargs != 0
        possibilities = ''
        if takes_argument:
            action = completer.fish_action()
            possibilities = ''
            dash_f = '-f'
            if action is _OMIT_DASH_F:
                dash_f = ''
            else:
                possibilities = '-a ' + escape(action)
            print("complete %s -c passacre %s %s %s %s" % (
                dash_f, predicate, short_opt, long_opt, possibilities))
        print("complete -f -c passacre %s %s %s -d %s" % (
            predicate, short_opt, long_opt, escape(arg.help)))

    if subcommands:
        predicate = '-n %s' % escape('__fish_passacre_using_command %s' % (name,))
        for subcommand_name, help in subcommands:
            print("complete -f -c passacre %s -a %s -d %s" % (
                predicate, escape(subcommand_name), escape(help)))


def fish_completion_for(parser):
    print("""

function __fish_passacre_using_command
	set cmd (commandline -opc)
	set argvpos 1
	set argvcount (count $argv)
	for c in $cmd
		if [ $argvpos -le $argvcount ]
			set arg $argv[$argvpos]
		else
			set arg --
		end
		switch $c
		case '-*'
			continue
		case $arg
			set argvpos (math $argvpos + 1)
		case '*'
			return 1
		end
	end
	test $argvpos -gt $argvcount
	return $status
end

function __fish_passacre_sites
	passacre site --omit-hashed | cut -d: -f1
end

function __fish_passacre_schemata
	passacre schema | cut -d: -f1
end

    """)

    _fish_completion_for(parser)
