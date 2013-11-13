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


class NullCompleter(object):
    def zsh_action(self):
        return ' '


class FilesCompleter(object):
    def zsh_action(self):
        return '_files'


class SchemataCompleter(object):
    def zsh_action(self):
        return '_passacre_schemata'


class SitesCompleter(object):
    def zsh_action(self):
        return '_passacre_sites'


class HashMethodsCompleter(object):
    def zsh_action(self):
        return '_passacre_hash_methods'


def zsh_arguments_for(arguments):
    for arg in arguments:
        completer = getattr(arg, 'completer', None) or NullCompleter()
        if not arg.option_strings:
            yield escape(':%s:%s' % (arg.dest, completer.zsh_action()))
            continue

        option_strings = []
        if len(arg.option_strings) > 1:
            options = set(arg.option_strings)
            for option in options:
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
            for subaction_name, subaction in action.choices.iteritems():
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
    _passacre_site_list=($(passacre site | cut -d: -f1))
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


if __name__ == '__main__':
    from passacre.application import Passacre
    zsh_completion_for(Passacre().build_parser())
